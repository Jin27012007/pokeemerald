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
    start = BATTLE_MAIN.index("const u8 gTypeEffectiveness[372]")
    end = BATTLE_MAIN.index("\n};", start)
    chart = BATTLE_MAIN[start:end]
    triples = re.findall(
        r"(TYPE_[A-Z0-9_]+)\s*,\s*(TYPE_[A-Z0-9_]+)\s*,\s*(TYPE_MUL_[A-Z_]+)",
        chart,
    )
    assert len(triples) == 124
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


def test_fairy_summary_icon_and_palette_are_registered():
    assert "ANIMCMD_FRAME(TYPE_FAIRY * 8, 0, FALSE, FALSE)" in SUMMARY
    assert "sSpriteAnim_TypeFairy,\n    sSpriteAnim_CategoryCool" in SUMMARY
    assert "[TYPE_FAIRY] = 14" in SUMMARY
    assert "fairy" in GRAPHICS_RULES.split("types ?=", 1)[1].split("\n", 1)[0]
    assert (ROOT / "graphics/types/fairy.png").is_file()


def test_type_chart_random_probe_cannot_read_past_the_table():
    assert ">= sizeof(gTypeEffectiveness) / 3" in BATTLE_SCRIPTS
    assert "> sizeof(gTypeEffectiveness) / 3" not in BATTLE_SCRIPTS


def main():
    test_fairy_has_a_unique_emerald_type_id()
    test_fairy_chart_contains_all_gen6_matchups()
    test_fairy_summary_icon_and_palette_are_registered()
    test_type_chart_random_probe_cannot_read_past_the_table()
    print("PASS: Fairy type ID, 12 matchup changes, summary icon and bounded chart access.")


if __name__ == "__main__":
    main()
