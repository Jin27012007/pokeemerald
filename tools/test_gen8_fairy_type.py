#!/usr/bin/env python3
"""Regression tests for the Gen 8 Fairy type integration."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
POKEMON_CONSTANTS = (ROOT / "include/constants/pokemon.h").read_text(encoding="utf-8")
BATTLE_MAIN = (ROOT / "src/battle_main.c").read_text(encoding="utf-8")
SUMMARY = (ROOT / "src/pokemon_summary_screen.c").read_text(encoding="utf-8")
BATTLE_SCRIPTS = (ROOT / "src/battle_script_commands.c").read_text(encoding="utf-8")
GRAPHICS_RULES = (ROOT / "graphics_file_rules.mk").read_text(encoding="utf-8")


def test_fairy_has_a_unique_emerald_type_id():
    assert "#define TYPE_FAIRY            18" in POKEMON_CONSTANTS
    assert "#define NUMBER_OF_MON_TYPES   19" in POKEMON_CONSTANTS
    assert '[TYPE_FAIRY] = _("FAIRY")' in BATTLE_MAIN


def test_fairy_chart_contains_all_gen6_matchups():
    start = BATTLE_MAIN.index("const u8 gTypeEffectiveness[366]")
    end = BATTLE_MAIN.index("\n};", start)
    chart = BATTLE_MAIN[start:end]
    triples = re.findall(
        r"(TYPE_[A-Z0-9_]+)\s*,\s*(TYPE_[A-Z0-9_]+)\s*,\s*(TYPE_MUL_[A-Z_]+)",
        chart,
    )
    assert len(triples) == 122
    expected = {
        ("TYPE_FAIRY", "TYPE_FIGHTING", "TYPE_MUL_SUPER_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_DRAGON", "TYPE_MUL_SUPER_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_DARK", "TYPE_MUL_SUPER_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_FIRE", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_POISON", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_STEEL", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_FIGHTING", "TYPE_FAIRY", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_POISON", "TYPE_FAIRY", "TYPE_MUL_SUPER_EFFECTIVE"),
        ("TYPE_BUG", "TYPE_FAIRY", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_DRAGON", "TYPE_FAIRY", "TYPE_MUL_NO_EFFECT"),
        ("TYPE_DARK", "TYPE_FAIRY", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_STEEL", "TYPE_FAIRY", "TYPE_MUL_SUPER_EFFECTIVE"),
    }
    assert expected.issubset(set(triples))
    assert ("TYPE_ENDTABLE", "TYPE_ENDTABLE", "TYPE_MUL_NO_EFFECT") in triples
    # Steel no longer resists Ghost and Dark from Generation VI onward.
    assert ("TYPE_GHOST", "TYPE_STEEL", "TYPE_MUL_NOT_EFFECTIVE") not in triples
    assert ("TYPE_DARK", "TYPE_STEEL", "TYPE_MUL_NOT_EFFECTIVE") not in triples


def test_fairy_summary_icon_and_palette_are_registered():
    assert "ANIMCMD_FRAME(TYPE_FAIRY * 8, 0, FALSE, FALSE)" in SUMMARY
    assert "sSpriteAnim_TypeFairy,\n    sSpriteAnim_CategoryCool" in SUMMARY
    assert "[TYPE_FAIRY] = 14" in SUMMARY
    assert "fairy" in GRAPHICS_RULES.split("types :=", 1)[1].split("\n", 1)[0]
    assert (ROOT / "graphics/types/fairy.png").is_file()


def test_type_chart_random_probe_cannot_read_past_the_table():
    assert ">= sizeof(gTypeEffectiveness) / 3" in BATTLE_SCRIPTS
    assert "> sizeof(gTypeEffectiveness) / 3" not in BATTLE_SCRIPTS


def test_hidden_power_keeps_the_original_gen3_type_pool():
    assert "NUMBER_OF_MON_TYPES - 4" in BATTLE_SCRIPTS
    assert "NUMBER_OF_MON_TYPES - 3) * typeBits" not in BATTLE_SCRIPTS
    assert "Fairy type are excluded" in BATTLE_SCRIPTS


def test_fairy_battle_text_and_pokedex_filter():
    battle_messages = (ROOT / "src/battle_message.c").read_text(encoding="utf-8")
    assert '[TYPE_FAIRY]    = _("a FAIRY move")' in battle_messages
    pokedex = (ROOT / "src/pokedex.c").read_text(encoding="utf-8")
    assert "gTypeNames[TYPE_FAIRY]" in pokedex
    start = pokedex.index("static const u8 sDexSearchTypeIds[NUMBER_OF_MON_TYPES]")
    end = pokedex.index("\n};", start)
    assert "TYPE_FAIRY," in pokedex[start:end]


def test_species_that_gained_fairy_keep_modern_types():
    source = (ROOT / "src/data/pokemon/species_info.h").read_text(encoding="utf-8")
    expected = {
        "CLEFAIRY": ("TYPE_FAIRY", "TYPE_FAIRY"),
        "CLEFABLE": ("TYPE_FAIRY", "TYPE_FAIRY"),
        "JIGGLYPUFF": ("TYPE_NORMAL", "TYPE_FAIRY"),
        "WIGGLYTUFF": ("TYPE_NORMAL", "TYPE_FAIRY"),
        "MR_MIME": ("TYPE_PSYCHIC", "TYPE_FAIRY"),
        "CLEFFA": ("TYPE_FAIRY", "TYPE_FAIRY"),
        "IGGLYBUFF": ("TYPE_NORMAL", "TYPE_FAIRY"),
        "TOGEPI": ("TYPE_FAIRY", "TYPE_FAIRY"),
        "TOGETIC": ("TYPE_FAIRY", "TYPE_FLYING"),
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
        expected_field = f".types = {{ {pair[0]}, {pair[1]} }}"
        assert expected_field in block, f"{species}: expected {expected_field}"


def test_gen8_converter_no_longer_treats_fairy_as_a_gap():
    converter = (ROOT / "tools/gen8_convert_emerald.py").read_text(encoding="utf-8")
    assert "fairy_type_not_in_emerald_enum" not in converter
    source_only_line = next(
        line for line in converter.splitlines()
        if '"source_only_fields_require_runtime_work"' in line
    )
    assert '"fairy_type"' not in source_only_line


def main():
    test_fairy_has_a_unique_emerald_type_id()
    test_fairy_chart_contains_all_gen6_matchups()
    test_fairy_summary_icon_and_palette_are_registered()
    test_type_chart_random_probe_cannot_read_past_the_table()
    test_hidden_power_keeps_the_original_gen3_type_pool()
    test_fairy_battle_text_and_pokedex_filter()
    test_species_that_gained_fairy_keep_modern_types()
    test_gen8_converter_no_longer_treats_fairy_as_a_gap()
    print("PASS: Fairy type, modern chart, UI, Pokédex, legacy species and Gen 8 conversion.")


if __name__ == "__main__":
    main()
