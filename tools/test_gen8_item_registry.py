#!/usr/bin/env python3
"""Regression tests for the imported Gen 4–8 item data registry."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ITEM_CONSTANTS = (ROOT / "include/constants/items.h").read_text(encoding="utf-8")
HOLD_EFFECTS = (ROOT / "include/constants/hold_effects.h").read_text(encoding="utf-8")
ITEM_DATA = (ROOT / "src/data/items.h").read_text(encoding="utf-8")
ITEM_TEXT = (ROOT / "src/data/text/item_descriptions.h").read_text(encoding="utf-8")
ICON_TABLE = (ROOT / "src/data/item_icon_table.h").read_text(encoding="utf-8")

SYMBOLS = (
    "ABSORB_BULB", "BLACK_SLUDGE", "CELL_BATTERY", "ELECTIRIZER",
    "ELECTRIC_SEED", "GRASSY_SEED", "HONEY", "LAGGING_TAIL",
    "LEADERS_CREST", "LEEK", "LIGHT_CLAY", "MAGMARIZER", "METRONOME",
    "MISTY_SEED", "OVAL_STONE", "PSYCHIC_SEED", "RAZOR_CLAW",
    "RAZOR_FANG", "RED_NECTAR", "SHED_SHELL", "SNOWBALL",
    "STICKY_BARB", "WIDE_LENS",
)


def camel(symbol):
    return "".join(part.title() for part in symbol.lower().split("_"))


def test_all_gen8_item_ids_have_records_text_and_safe_icons():
    for symbol in SYMBOLS:
        assert re.search(r"\bITEM_" + symbol + r"\s*,", ITEM_CONSTANTS)
        assert f"[ITEM_{symbol}] =" in ITEM_DATA
        assert f".itemId = ITEM_{symbol}" in ITEM_DATA
        assert f"sGen8{camel(symbol)}Desc" in ITEM_DATA
        assert f"sGen8{camel(symbol)}Desc[]" in ITEM_TEXT
        assert f"[ITEM_{symbol}] = {{gItemIcon_QuestionMark, gItemIconPalette_QuestionMark}}" in ICON_TABLE


def test_imported_hold_effect_ids_are_unique_and_fit_u8():
    rows = [
        (symbol, value)
        for symbol, value in re.findall(r"#define HOLD_EFFECT_([A-Z0-9_]+)\s+([0-9]+)", HOLD_EFFECTS)
        if not symbol.startswith("PARAM_") and symbol != "COUNT"
    ]
    values = [int(value) for _, value in rows]
    assert len(values) == len(set(values))
    assert max(values) < 256
    for symbol in (
        "ABSORB_BULB", "BLACK_SLUDGE", "CELL_BATTERY", "LAGGING_TAIL",
        "LIGHT_CLAY", "METRONOME", "SHED_SHELL", "SNOWBALL",
        "STICKY_BARB", "TERRAIN_SEED", "WIDE_LENS",
    ):
        assert f"#define HOLD_EFFECT_{symbol}" in HOLD_EFFECTS
    assert "#define HOLD_EFFECT_COUNT 78" in HOLD_EFFECTS


def test_legacy_equivalent_effects_are_reused_explicitly():
    assert ".holdEffect = HOLD_EFFECT_STICK," in ITEM_DATA
    assert ".holdEffect = HOLD_EFFECT_SCOPE_LENS," in ITEM_DATA
    assert ".holdEffect = HOLD_EFFECT_FLINCH," in ITEM_DATA


def main():
    test_all_gen8_item_ids_have_records_text_and_safe_icons()
    test_imported_hold_effect_ids_are_unique_and_fit_u8()
    test_legacy_equivalent_effects_are_reused_explicitly()
    print("PASS: 23 item IDs, records, descriptions, icon fallbacks and hold-effect IDs.")


if __name__ == "__main__":
    main()
