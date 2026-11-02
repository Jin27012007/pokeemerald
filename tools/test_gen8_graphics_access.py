#!/usr/bin/env python3
"""Regression checks for bounds-checked Pokémon graphics table access."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/decompress.c"
HEADER = ROOT / "include/decompress.h"
REPORT = ROOT / "reports/gen8-conversion/graphics_access_audit.json"

TABLES = (
    "gMonFrontPicTable",
    "gMonBackPicTable",
    "gMonPaletteTable",
    "gMonShinyPaletteTable",
    "gMonFrontPicCoords",
    "gMonBackPicCoords",
)
EXPECTED_DIRECT_LINES = {
    "gMonFrontPicTable": "return &gMonFrontPicTable[species];",
    "gMonBackPicTable": "return &gMonBackPicTable[species];",
    "gMonPaletteTable": "return &gMonPaletteTable[species];",
    "gMonShinyPaletteTable": "return &gMonShinyPaletteTable[species];",
    "gMonFrontPicCoords": "return &gMonFrontPicCoords[species];",
    "gMonBackPicCoords": "return &gMonBackPicCoords[species];",
}


def main() -> int:
    source = SOURCE.read_text(encoding="utf-8")
    header = HEADER.read_text(encoding="utf-8")
    assert "MON_GRAPHICS_LAST_SPECIES_ID" in source
    assert "GetMonFrontPicCoordsEntry(s32 species)" in source
    assert "GetMonBackPicCoordsEntry(s32 species)" in source
    assert "GetMonFrontPicCoordsEntry(s32 species);" in header
    assert "GetMonBackPicCoordsEntry(s32 species);" in header

    for accessor in (
        "GetMonFrontPicTableEntry",
        "GetMonBackPicTableEntry",
        "GetMonPaletteTableEntry",
        "GetMonShinyPaletteTableEntry",
        "GetMonFrontPicCoordsEntry",
        "GetMonBackPicCoordsEntry",
    ):
        start = source.index(accessor + "(s32 species)")
        end = source.index("\n}", start) + 2
        body = source[start:end]
        assert "species < 0 || species > MON_GRAPHICS_LAST_SPECIES_ID" in body
        assert "species = SPECIES_NONE;" in body
        assert "return &gMon" in body

    direct_indexes = []
    for path in sorted((ROOT / "src").rglob("*.c")):
        relative = path.relative_to(ROOT).as_posix()
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for table in TABLES:
                if re.search(re.escape(table) + r"\s*\[[^\]\n]+\]", line):
                    direct_indexes.append({
                        "path": relative,
                        "line": line_number,
                        "table": table,
                        "source": line.strip(),
                    })

    expected = [
        {
            "path": "src/decompress.c",
            "line": next(
                n for n, line in enumerate(source.splitlines(), 1)
                if line.strip() == expected_line
            ),
            "table": table,
            "source": expected_line,
        }
        for table, expected_line in EXPECTED_DIRECT_LINES.items()
    ]
    assert sorted(direct_indexes, key=lambda x: (x["table"], x["line"])) == sorted(
        expected, key=lambda x: (x["table"], x["line"])
    ), direct_indexes

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "graphics_tables": list(TABLES),
        "bounded_accessor_count": 6,
        "unguarded_direct_indexes": 0,
        "guarded_table_index_sites": len(direct_indexes),
        "invalid_species_fallback": "SPECIES_NONE",
        "last_supported_graphics_id": "SPECIES_UNOWN_QMARK",
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("PASS: species front/back graphics, palettes and coordinates use bounded accessors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
