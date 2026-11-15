#!/usr/bin/env python3
"""Static regression tests for the Gen 6 Fairy type integration."""
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]

def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

def test_type_id_and_chart():
    header = read("include/constants/pokemon.h")
    assert re.search(r"#define TYPE_FAIRY\s+18\b", header)
    assert re.search(r"#define NUMBER_OF_MON_TYPES\s+19\b", header)
    chart_source = read("src/battle_main.c")
    match = re.search(
        r"const u8 gTypeEffectiveness\[(\d+)\]\s*=\s*\{(.*?)\n\};",
        chart_source, re.S
    )
    assert match, "type effectiveness table not found"
    assert int(match.group(1)) == 366
    tokens = re.findall(r"\bTYPE_[A-Z0-9_]+\b", match.group(2))
    assert len(tokens) == 366, f"expected 122 triplets, found {len(tokens) // 3}"
    triplets = [tuple(tokens[i:i + 3]) for i in range(0, len(tokens), 3)]
    expected = {
        ("TYPE_FIGHTING", "TYPE_FAIRY", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_POISON", "TYPE_FAIRY", "TYPE_MUL_SUPER_EFFECTIVE"),
        ("TYPE_BUG", "TYPE_FAIRY", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_DRAGON", "TYPE_FAIRY", "TYPE_MUL_NO_EFFECT"),
        ("TYPE_DARK", "TYPE_FAIRY", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_STEEL", "TYPE_FAIRY", "TYPE_MUL_SUPER_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_FIGHTING", "TYPE_MUL_SUPER_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_POISON", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_STEEL", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_FIRE", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_DRAGON", "TYPE_MUL_SUPER_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_DARK", "TYPE_MUL_SUPER_EFFECTIVE"),
    }
    assert expected.issubset(set(triplets)), f"missing Fairy matchups: {expected - set(triplets)}"
    assert ("TYPE_GHOST", "TYPE_STEEL", "TYPE_MUL_NOT_EFFECTIVE") not in triplets
    assert ("TYPE_DARK", "TYPE_STEEL", "TYPE_MUL_NOT_EFFECTIVE") not in triplets
    assert '[TYPE_FAIRY] = _("FAIRY")' in chart_source

def test_fairy_ui_and_dex_search():
    summary = read("src/pokemon_summary_screen.c")
    assert "sSpriteAnim_TypeFairy" in summary
    assert "    sSpriteAnim_TypeFairy," in summary
    assert "[TYPE_FAIRY] = 14" in summary
    messages = read("src/battle_message.c")
    assert '[TYPE_FAIRY]    = _("a FAIRY move")' in messages
    pokedex = read("src/pokedex.c")
    assert "gTypeNames[TYPE_FAIRY]" in pokedex
    assert "    TYPE_FAIRY," in pokedex
    rules = read("graphics_file_rules.mk")
    assert re.search(r"^types := .*\bfairy\s*$", rules, re.M)
    icon = ROOT / "graphics/types/fairy.png"
    assert icon.is_file(), "missing 32x16 Fairy icon source"
    data = icon.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", data[16:24])
    assert (width, height) == (32, 16), f"unexpected Fairy icon size: {(width, height)}"

def test_existing_species_modern_typings():
    source = read("src/data/pokemon/species_info.h")
    expected = {
        "CLEFAIRY": ("TYPE_FAIRY", "TYPE_FAIRY"),
        "CLEFABLE": ("TYPE_FAIRY", "TYPE_FAIRY"),
        "JIGGLYPUFF": ("TYPE_NORMAL", "TYPE_FAIRY"),
        "WIGGLYTUFF": ("TYPE_NORMAL", "TYPE_FAIRY"),
        "MR_MIME": ("TYPE_PSYCHIC", "TYPE_FAIRY"),
        "CLEFFA": ("TYPE_FAIRY", "TYPE_FAIRY"),
        "IGGLYBUFF": ("TYPE_NORMAL", "TYPE_FAIRY"),
        "TOGEPI": ("TYPE_FAIRY", "TYPE_FAIRY"),
        "TOGETIC": ("TYPE_FAIRY", "TYPE_FAIRY"),
        "SNUBBULL": ("TYPE_FAIRY", "TYPE_FAIRY"),
        "GRANBULL": ("TYPE_FAIRY", "TYPE_FAIRY"),
        "MARILL": ("TYPE_WATER", "TYPE_FAIRY"),
        "AZUMARILL": ("TYPE_WATER", "TYPE_FAIRY"),
        "AZURILL": ("TYPE_NORMAL", "TYPE_FAIRY"),
        "MAWILE": ("TYPE_STEEL", "TYPE_FAIRY"),
        "RALTS": ("TYPE_PSYCHIC", "TYPE_FAIRY"),
        "KIRLIA": ("TYPE_PSYCHIC", "TYPE_FAIRY"),
        "GARDEVOIR": ("TYPE_PSYCHIC", "TYPE_FAIRY"),
    }
    for species, pair in expected.items():
        start = source.index(f"[SPECIES_{species}] =")
        end = source.index("\n    },", start)
        block = source[start:end]
        match = re.search(r"\.types\s*=\s*\{\s*(TYPE_[A-Z0-9_]+)\s*,\s*(TYPE_[A-Z0-9_]+)\s*\}", block)
        assert match, f"missing type pair for {species}"
        assert match.groups() == pair, f"{species}: expected {pair}, got {match.groups()}"

def test_gen8_mapping_no_longer_rejects_fairy_enum():
    converter = read("tools/gen8_convert_emerald.py")
    assert "fairy_type_not_in_emerald_enum" not in converter
    assert '"fairy_type_supported_in_emerald": "FAIRY" in' in converter
    assert '"fairy_type"' not in converter.split('"source_only_fields_require_runtime_work":', 1)[1].split("\n", 1)[0]
    builder = read("tools/gen8_build_pending_tables.py")
    assert '"type_chart_runtime_audited": name == "FAIRY"' in builder

def main():
    test_type_id_and_chart()
    test_fairy_ui_and_dex_search()
    test_existing_species_modern_typings()
    test_gen8_mapping_no_longer_rejects_fairy_enum()
    print("PASS: Fairy battle chart, type ID, UI, Pokédex, legacy species and Gen 8 mapping.")

if __name__ == "__main__":
    main()
