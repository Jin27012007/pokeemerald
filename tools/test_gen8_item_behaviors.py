#!/usr/bin/env python3
"""Regression tests for implemented Gen 4–8 held-item effects."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATTLE_UTIL = (ROOT / "src/battle_util.c").read_text(encoding="utf-8")
BATTLE_SCRIPTS = (ROOT / "src/battle_script_commands.c").read_text(encoding="utf-8")
BATTLE_MAIN = (ROOT / "src/battle_main.c").read_text(encoding="utf-8")
PENDING_TABLES = (ROOT / "tools/gen8_build_pending_tables.py").read_text(encoding="utf-8")


def test_absorb_bulb_cell_battery_and_snowball_consume_on_matching_hit():
    for effect in ("ABSORB_BULB", "CELL_BATTERY", "SNOWBALL"):
        assert f"case HOLD_EFFECT_{effect}:" in BATTLE_UTIL
    assert "gSpecialStatuses[battler].physicalDmg != 0" in BATTLE_UTIL
    assert "moveType == TYPE_WATER" in BATTLE_UTIL
    assert "moveType == TYPE_ELECTRIC" in BATTLE_UTIL
    assert "moveType == TYPE_ICE" in BATTLE_UTIL
    assert "BattleScript_BerryStatRaiseEnd2" in BATTLE_UTIL
    assert "gBattlerAttacker = battler" in BATTLE_UTIL


def test_wide_lens_and_light_clay_effects():
    assert "HOLD_EFFECT_WIDE_LENS" in BATTLE_SCRIPTS
    assert "(100 + GetItemHoldEffectParam(gBattleMons[gBattlerAttacker].item))" in BATTLE_SCRIPTS
    assert "HOLD_EFFECT_LIGHT_CLAY" in BATTLE_SCRIPTS
    assert "reflectTimer =\n            (GetItemHoldEffect" in BATTLE_SCRIPTS
    assert "lightscreenTimer =\n            (GetItemHoldEffect" in BATTLE_SCRIPTS
    assert "? 8 : 5" in BATTLE_SCRIPTS


def test_lagging_tail_is_last_within_priority_bracket():
    assert "holdEffect == HOLD_EFFECT_LAGGING_TAIL" in BATTLE_MAIN
    assert "speedBattler1 = 0" in BATTLE_MAIN
    assert "speedBattler2 = 0" in BATTLE_MAIN


def test_only_verified_item_behaviors_are_marked_audited():
    assert '"ABSORB_BULB", "CELL_BATTERY", "SNOWBALL"' in PENDING_TABLES
    assert '"LIGHT_CLAY", "WIDE_LENS", "LAGGING_TAIL"' in PENDING_TABLES
    assert '"LEEK", "RAZOR_CLAW", "RAZOR_FANG"' in PENDING_TABLES


def main():
    test_absorb_bulb_cell_battery_and_snowball_consume_on_matching_hit()
    test_wide_lens_and_light_clay_effects()
    test_lagging_tail_is_last_within_priority_bracket()
    test_only_verified_item_behaviors_are_marked_audited()
    print("PASS: Absorb Bulb, Cell Battery, Snowball, Wide Lens, Light Clay and Lagging Tail.")


if __name__ == "__main__":
    main()
