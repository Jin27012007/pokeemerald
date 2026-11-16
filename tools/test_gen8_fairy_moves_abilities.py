#!/usr/bin/env python3
"""Regression checks for the first executable Fairy move and ability batch."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
MOVES = (ROOT / "include/constants/moves.h").read_text(encoding="utf-8")
ABILITIES = (ROOT / "include/constants/abilities.h").read_text(encoding="utf-8")
BATTLE_MOVES = (ROOT / "src/data/battle_moves.h").read_text(encoding="utf-8")
MOVE_NAMES = (ROOT / "src/data/text/move_names.h").read_text(encoding="utf-8")
MOVE_DESCRIPTIONS = (ROOT / "src/data/text/move_descriptions.h").read_text(encoding="utf-8")
CONTEST = (ROOT / "src/data/contest_moves.h").read_text(encoding="utf-8")
ANIMS = (ROOT / "data/battle_anim_scripts.s").read_text(encoding="utf-8")
BATTLE_HEADER = (ROOT / "include/battle.h").read_text(encoding="utf-8")
POKEMON = (ROOT / "src/pokemon.c").read_text(encoding="utf-8")
BATTLE_COMMANDS = (ROOT / "src/battle_script_commands.c").read_text(encoding="utf-8")
ABILITY_TEXT = (ROOT / "src/data/text/abilities.h").read_text(encoding="utf-8")

EXPECTED_MOVES = {
    "FAIRY_WIND": 355,
    "PLAY_ROUGH": 356,
    "MOONBLAST": 357,
    "DAZZLING_GLEAM": 358,
    "FLEUR_CANNON": 359,
    "NATURES_MADNESS": 360,
    "SPIRIT_BREAK": 361,
    "STRANGE_STEAM": 362,
    "SPRINGTIDE_STORM": 363,
}


def block_after(source: str, marker: str) -> str:
    start = source.index(marker)
    end = source.find("\n    },", start)
    if end < 0:
        raise AssertionError(f"unterminated block: {marker}")
    return source[start:end]


def test_move_ids_and_count_are_contiguous():
    for name, move_id in EXPECTED_MOVES.items():
        assert f"#define MOVE_{name} {move_id}" in MOVES
    assert "#define MOVES_COUNT 364" in MOVES


def test_fairy_battle_data_uses_supported_effects():
    expected = {
        "FAIRY_WIND": ("EFFECT_HIT", "40", "100", "30", "MOVE_TARGET_SELECTED"),
        "PLAY_ROUGH": ("EFFECT_ATTACK_DOWN_HIT", "90", "90", "10", "MOVE_TARGET_SELECTED"),
        "MOONBLAST": ("EFFECT_SPECIAL_ATTACK_DOWN_HIT", "95", "100", "15", "MOVE_TARGET_SELECTED"),
        "DAZZLING_GLEAM": ("EFFECT_HIT", "80", "100", "10", "MOVE_TARGET_BOTH"),
        "FLEUR_CANNON": ("EFFECT_OVERHEAT", "130", "90", "5", "MOVE_TARGET_SELECTED"),
        "NATURES_MADNESS": ("EFFECT_SUPER_FANG", "1", "90", "10", "MOVE_TARGET_SELECTED"),
        "SPIRIT_BREAK": ("EFFECT_SPECIAL_ATTACK_DOWN_HIT", "75", "100", "15", "MOVE_TARGET_SELECTED"),
        "STRANGE_STEAM": ("EFFECT_CONFUSE_HIT", "90", "95", "10", "MOVE_TARGET_SELECTED"),
        "SPRINGTIDE_STORM": ("EFFECT_ATTACK_DOWN_HIT", "95", "80", "5", "MOVE_TARGET_BOTH"),
    }
    for name, fields in expected.items():
        block = block_after(BATTLE_MOVES, f"[MOVE_{name}] =")
        assert f".effect = {fields[0]}" in block, name
        assert f".power = {fields[1]}" in block, name
        assert f".accuracy = {fields[2]}" in block, name
        assert f".pp = {fields[3]}" in block, name
        assert f".target = {fields[4]}" in block, name
        assert ".type = TYPE_FAIRY" in block, name


def test_move_text_contest_and_animation_indexes_exist():
    for name in EXPECTED_MOVES:
        assert f"[MOVE_{name}] = " in MOVE_NAMES
        assert f"[MOVE_{name} - 1] = " in MOVE_DESCRIPTIONS
        assert f"[MOVE_{name}] = " in CONTEST

    proxies = {
        "FAIRY_WIND": "Move_SILVER_WIND",
        "PLAY_ROUGH": "Move_DOUBLE_EDGE",
        "MOONBLAST": "Move_PSYCHIC",
        "DAZZLING_GLEAM": "Move_SWIFT",
        "FLEUR_CANNON": "Move_HYPER_BEAM",
        "NATURES_MADNESS": "Move_SUPER_FANG",
        "SPIRIT_BREAK": "Move_BRICK_BREAK",
        "STRANGE_STEAM": "Move_SIGNAL_BEAM",
        "SPRINGTIDE_STORM": "Move_GUST",
    }
    for name, proxy in proxies.items():
        assert f"{proxy} @ MOVE_{name}" in ANIMS
    assert "Move_COUNT @ cannot be reached, because last move is Springtide Storm" in ANIMS


def test_fairy_physical_moves_keep_physical_damage_category():
    assert "IS_MOVE_PHYSICAL(move, moveType)" in BATTLE_HEADER
    assert "MOVE_PLAY_ROUGH" in BATTLE_HEADER
    assert "MOVE_SPIRIT_BREAK" in BATTLE_HEADER
    assert "IS_MOVE_PHYSICAL(move, type)" in POKEMON
    assert "IS_MOVE_SPECIAL(move, type)" in POKEMON
    assert "IS_MOVE_PHYSICAL(move, type)" in BATTLE_COMMANDS
    assert "IS_MOVE_PHYSICAL(gCurrentMove, moveType)" in BATTLE_COMMANDS


def test_fairy_aura_aura_break_and_pixilate_are_applied():
    for symbol in ("ABILITY_FAIRY_AURA", "ABILITY_AURA_BREAK", "ABILITY_PIXILATE"):
        assert symbol in ABILITIES
        assert f"[{symbol}]" in ABILITY_TEXT or f"case {symbol}" in POKEMON
    assert "gBattleMons[gBattlerAttacker].ability == ABILITY_PIXILATE" in BATTLE_HEADER
    assert "gBattleMovePower = (120 * gBattleMovePower) / 100" in POKEMON
    assert "gBattleMons[i].ability == ABILITY_FAIRY_AURA" in POKEMON
    assert "gBattleMons[i].ability == ABILITY_AURA_BREAK" in POKEMON
    assert "gBattleMovePower = (4 * gBattleMovePower) / 3" in POKEMON
    assert "gBattleMovePower = (3 * gBattleMovePower) / 4" in POKEMON


def main():
    test_move_ids_and_count_are_contiguous()
    test_fairy_battle_data_uses_supported_effects()
    test_move_text_contest_and_animation_indexes_exist()
    test_fairy_physical_moves_keep_physical_damage_category()
    test_fairy_aura_aura_break_and_pixilate_are_applied()
    print("PASS: 9 Fairy moves, battle data, categories, text, animation mappings and 3 abilities.")


if __name__ == "__main__":
    main()
