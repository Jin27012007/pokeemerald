#!/usr/bin/env python3
"""Bounds and sentinel regression tests for Pokémon graphics table accessors."""
from __future__ import annotations
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TABLES = {
    "gMonFrontPicTable": ("src/data/pokemon_graphics/front_pic_table.h", "SPECIES_SPRITE"),
    "gMonBackPicTable": ("src/data/pokemon_graphics/back_pic_table.h", "SPECIES_SPRITE"),
    "gMonPaletteTable": ("src/data/pokemon_graphics/palette_table.h", "SPECIES_PAL"),
    "gMonShinyPaletteTable": ("src/data/pokemon_graphics/shiny_palette_table.h", "SPECIES_SHINY_PAL"),
}
ACCESSORS = {
    "gMonFrontPicTable": "GetMonFrontPicTableEntry",
    "gMonBackPicTable": "GetMonBackPicTableEntry",
    "gMonPaletteTable": "GetMonPaletteTableEntry",
    "gMonShinyPaletteTable": "GetMonShinyPaletteTableEntry",
}

def function_body(source: str, name: str) -> str:
    match = re.search(rf"\b{name}\s*\([^)]*\)\s*\{{", source)
    assert match, f"Missing function {name}"
    start = source.index("{", match.start())
    depth = 0
    for pos in range(start, len(source)):
        if source[pos] == "{": depth += 1
        elif source[pos] == "}":
            depth -= 1
            if depth == 0: return source[start + 1:pos]
    raise AssertionError(f"Unclosed function {name}")

def compile_accessor_harness(decompress: str) -> None:
    compiler = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
    assert compiler, "A C compiler is required for graphics accessor tests"
    bodies = []
    for accessor in ACCESSORS.values():
        match = re.search(rf"\b{accessor}\s*\([^)]*\)\s*\{{", decompress)
        assert match, f"Missing function {accessor}"
        start = decompress.rfind("const struct", 0, match.start())
        brace = decompress.index("{", start)
        depth = 0
        for pos in range(brace, len(decompress)):
            if decompress[pos] == "{": depth += 1
            elif decompress[pos] == "}":
                depth -= 1
                if depth == 0:
                    bodies.append(decompress[start:pos + 1])
                    break
    harness = r'''
#include <stdint.h>
typedef int32_t s32;
#define SPECIES_NONE 0
#define SPECIES_UNOWN_QMARK 439
struct CompressedSpriteSheet { int value; };
struct CompressedSpritePalette { int value; };
static const s32 MON_GRAPHICS_LAST_SPECIES_ID = SPECIES_UNOWN_QMARK;
static struct CompressedSpriteSheet gMonFrontPicTable[440];
static struct CompressedSpriteSheet gMonBackPicTable[440];
static struct CompressedSpritePalette gMonPaletteTable[440];
static struct CompressedSpritePalette gMonShinyPaletteTable[440];
''' + "\n".join(bodies) + r'''
int main(void)
{
    int i;
    for (i = 0; i < 440; i++)
    {
        gMonFrontPicTable[i].value = i;
        gMonBackPicTable[i].value = i + 1000;
        gMonPaletteTable[i].value = i + 2000;
        gMonShinyPaletteTable[i].value = i + 3000;
    }
    if (GetMonFrontPicTableEntry(0)->value != 0) return 1;
    if (GetMonFrontPicTableEntry(412)->value != 412) return 2;
    if (GetMonFrontPicTableEntry(413)->value != 413) return 3;
    if (GetMonFrontPicTableEntry(439)->value != 439) return 4;
    if (GetMonFrontPicTableEntry(-1)->value != 0) return 5;
    if (GetMonFrontPicTableEntry(440)->value != 0) return 6;
    if (GetMonFrontPicTableEntry(65535)->value != 0) return 7;
    if (GetMonBackPicTableEntry(439)->value != 1439) return 8;
    if (GetMonBackPicTableEntry(440)->value != 1000) return 9;
    if (GetMonPaletteTableEntry(439)->value != 2439) return 10;
    if (GetMonPaletteTableEntry(-1)->value != 2000) return 11;
    if (GetMonShinyPaletteTableEntry(439)->value != 3439) return 12;
    if (GetMonShinyPaletteTableEntry(440)->value != 3000) return 13;
    return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix="gen8-graphics-access-") as tmp:
        source, binary = Path(tmp) / "test.c", Path(tmp) / "test"
        source.write_text(harness, encoding="utf-8")
        try:
            subprocess.run([compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
                            str(source), "-o", str(binary)], check=True,
                           capture_output=True, text=True)
        except subprocess.CalledProcessError as error:
            raise AssertionError(
                f"Graphics accessor harness compile failed:\\n{error.stderr}\\n{error.stdout}"
            ) from error
        subprocess.run([str(binary)], check=True, capture_output=True, text=True)

def main() -> int:
    species = (ROOT / "include/constants/species.h").read_text(encoding="utf-8")
    assert "#define SPECIES_UNOWN_QMARK (SPECIES_UNOWN_B + 26)" in species
    decompress = (ROOT / "src/decompress.c").read_text(encoding="utf-8")
    header = (ROOT / "include/decompress.h").read_text(encoding="utf-8")
    for table, (path, macro) in TABLES.items():
        source = (ROOT / path).read_text(encoding="utf-8")
        entries = re.findall(rf"\b{macro}\s*\(\s*([A-Z0-9_]+)", source)
        assert len(entries) == 440, (table, len(entries))
        assert entries[0] == "NONE" and entries[-1] == "UNOWN_QMARK"
        accessor = ACCESSORS[table]
        assert f"{accessor}(s32 species)" in header
        body = function_body(decompress, accessor)
        assert "species < 0 || species > MON_GRAPHICS_LAST_SPECIES_ID" in body
        assert "species = SPECIES_NONE;" in body
        assert f"return &{table}[species];" in body
    direct = []
    pattern = re.compile(r"\b(gMonFrontPicTable|gMonBackPicTable|gMonPaletteTable|gMonShinyPaletteTable)\s*\[")
    for path in sorted((ROOT / "src").rglob("*.c")):
        source = path.read_text(encoding="utf-8")
        for line_no, line in enumerate(source.splitlines(), 1):
            if pattern.search(line):
                direct.append((path.relative_to(ROOT).as_posix(), line_no, line.strip()))
    expected = [
        ("src/decompress.c", next(i for i, line in enumerate(decompress.splitlines(), 1) if "return &gMonFrontPicTable[species];" in line), "return &gMonFrontPicTable[species];"),
        ("src/decompress.c", next(i for i, line in enumerate(decompress.splitlines(), 1) if "return &gMonBackPicTable[species];" in line), "return &gMonBackPicTable[species];"),
        ("src/decompress.c", next(i for i, line in enumerate(decompress.splitlines(), 1) if "return &gMonPaletteTable[species];" in line), "return &gMonPaletteTable[species];"),
        ("src/decompress.c", next(i for i, line in enumerate(decompress.splitlines(), 1) if "return &gMonShinyPaletteTable[species];" in line), "return &gMonShinyPaletteTable[species];"),
    ]
    assert direct == expected, direct
    compile_accessor_harness(decompress)
    print("PASS: graphics access is bounded; Egg and all Unown auxiliary slots remain addressable.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
