#!/usr/bin/env python3
"""Regression tests for the first playable batch of Gen 4 move definitions."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED = [
    [
        "AQUA_JET",
        362,
        "EFFECT_HIT",
        40,
        "WATER",
        "PHYSICAL",
        100,
        20,
        1
    ],
    [
        "AURA_SPHERE",
        363,
        "EFFECT_ALWAYS_HIT",
        80,
        "FIGHTING",
        "SPECIAL",
        0,
        20,
        0
    ],
    [
        "BRAVE_BIRD",
        364,
        "EFFECT_RECOIL",
        120,
        "FLYING",
        "PHYSICAL",
        100,
        15,
        0
    ],
    [
        "BUG_BUZZ",
        365,
        "EFFECT_SPECIAL_DEFENSE_DOWN_HIT",
        90,
        "BUG",
        "SPECIAL",
        100,
        10,
        0
    ],
    [
        "DARK_PULSE",
        366,
        "EFFECT_FLINCH_HIT",
        80,
        "DARK",
        "SPECIAL",
        100,
        15,
        0
    ],
    [
        "DRAIN_PUNCH",
        367,
        "EFFECT_ABSORB",
        75,
        "FIGHTING",
        "PHYSICAL",
        100,
        10,
        0
    ],
    [
        "DRAGON_PULSE",
        368,
        "EFFECT_HIT",
        85,
        "DRAGON",
        "SPECIAL",
        100,
        10,
        0
    ],
    [
        "EARTH_POWER",
        369,
        "EFFECT_SPECIAL_DEFENSE_DOWN_HIT",
        90,
        "GROUND",
        "SPECIAL",
        100,
        10,
        0
    ],
    [
        "ENERGY_BALL",
        370,
        "EFFECT_SPECIAL_DEFENSE_DOWN_HIT",
        90,
        "GRASS",
        "SPECIAL",
        100,
        10,
        0
    ],
    [
        "GIGA_IMPACT",
        371,
        "EFFECT_RECHARGE",
        150,
        "NORMAL",
        "PHYSICAL",
        90,
        5,
        0
    ],
    [
        "GRASS_KNOT",
        372,
        "EFFECT_LOW_KICK",
        1,
        "GRASS",
        "SPECIAL",
        100,
        20,
        0
    ],
    [
        "ICE_SHARD",
        373,
        "EFFECT_HIT",
        40,
        "ICE",
        "PHYSICAL",
        100,
        30,
        1
    ],
    [
        "IRON_HEAD",
        374,
        "EFFECT_FLINCH_HIT",
        80,
        "STEEL",
        "PHYSICAL",
        100,
        15,
        0
    ],
    [
        "LEAF_STORM",
        375,
        "EFFECT_OVERHEAT",
        130,
        "GRASS",
        "SPECIAL",
        90,
        5,
        0
    ],
    [
        "MAGMA_STORM",
        376,
        "EFFECT_TRAP",
        100,
        "FIRE",
        "SPECIAL",
        75,
        5,
        0
    ],
    [
        "NASTY_PLOT",
        377,
        "EFFECT_SPECIAL_ATTACK_UP_2",
        0,
        "DARK",
        "STATUS",
        0,
        20,
        0
    ],
    [
        "NIGHT_SLASH",
        378,
        "EFFECT_HIGH_CRITICAL",
        70,
        "DARK",
        "PHYSICAL",
        100,
        15,
        0
    ],
    [
        "POISON_JAB",
        379,
        "EFFECT_POISON_HIT",
        80,
        "POISON",
        "PHYSICAL",
        100,
        20,
        0
    ],
    [
        "POWER_GEM",
        380,
        "EFFECT_HIT",
        80,
        "ROCK",
        "SPECIAL",
        100,
        20,
        0
    ],
    [
        "POWER_WHIP",
        381,
        "EFFECT_HIT",
        120,
        "GRASS",
        "PHYSICAL",
        85,
        10,
        0
    ],
    [
        "PSYCHO_CUT",
        382,
        "EFFECT_HIGH_CRITICAL",
        70,
        "PSYCHIC",
        "PHYSICAL",
        100,
        20,
        0
    ],
    [
        "ROAR_OF_TIME",
        383,
        "EFFECT_RECHARGE",
        150,
        "DRAGON",
        "SPECIAL",
        90,
        5,
        0
    ],
    [
        "ROCK_POLISH",
        384,
        "EFFECT_SPEED_UP_2",
        0,
        "ROCK",
        "STATUS",
        0,
        20,
        0
    ],
    [
        "ROCK_WRECKER",
        385,
        "EFFECT_RECHARGE",
        150,
        "ROCK",
        "PHYSICAL",
        90,
        5,
        0
    ],
    [
        "SEED_BOMB",
        386,
        "EFFECT_HIT",
        80,
        "GRASS",
        "PHYSICAL",
        100,
        15,
        0
    ],
    [
        "SHADOW_CLAW",
        387,
        "EFFECT_HIGH_CRITICAL",
        70,
        "GHOST",
        "PHYSICAL",
        100,
        15,
        0
    ],
    [
        "SHADOW_SNEAK",
        388,
        "EFFECT_HIT",
        40,
        "GHOST",
        "PHYSICAL",
        100,
        30,
        1
    ],
    [
        "SPACIAL_REND",
        389,
        "EFFECT_HIGH_CRITICAL",
        100,
        "DRAGON",
        "SPECIAL",
        95,
        5,
        0
    ],
    [
        "STONE_EDGE",
        390,
        "EFFECT_HIGH_CRITICAL",
        100,
        "ROCK",
        "PHYSICAL",
        80,
        5,
        0
    ],
    [
        "WOOD_HAMMER",
        391,
        "EFFECT_RECOIL",
        120,
        "GRASS",
        "PHYSICAL",
        100,
        15,
        0
    ],
    [
        "X_SCISSOR",
        392,
        "EFFECT_HIT",
        80,
        "BUG",
        "PHYSICAL",
        100,
        15,
        0
    ],
    [
        "ZEN_HEADBUTT",
        393,
        "EFFECT_FLINCH_HIT",
        80,
        "PSYCHIC",
        "PHYSICAL",
        90,
        15,
        0
    ]
]


def test_gen4_move_ids_and_runtime_records():
    constants = (ROOT / "include/constants/moves.h").read_text(encoding="utf-8")
    records = (ROOT / "src/data/battle_moves.h").read_text(encoding="utf-8")
    names = (ROOT / "src/data/text/move_names.h").read_text(encoding="utf-8")
    descriptions = (ROOT / "src/data/text/move_descriptions.h").read_text(encoding="utf-8")
    animations = (ROOT / "data/battle_anim_scripts.s").read_text(encoding="utf-8")
    assert "#define MOVES_COUNT 394" in constants
    assert len(EXPECTED) == 32
    for symbol, move_id, effect, power, move_type, category, accuracy, pp, priority in EXPECTED:
        assert f"#define MOVE_{symbol} {move_id}" in constants
        start = records.index(f"[MOVE_{symbol}] =")
        end = records.index("\n    },", start) + 7
        entry = records[start:end]
        assert f".effect = {effect}" in entry, symbol
        assert f".power = {power}" in entry, symbol
        assert f".type = TYPE_{move_type}" in entry, symbol
        assert f".category = DAMAGE_CATEGORY_{category}" in entry, symbol
        assert f".accuracy = {accuracy}" in entry, symbol
        assert f".pp = {pp}" in entry, symbol
        assert f".priority = {priority}" in entry, symbol
        assert f"[MOVE_{symbol}] = " in names
        assert f"[MOVE_{symbol} - 1] =" in descriptions
        assert f"@ {symbol.replace('_', ' ').title()}" in animations


def test_new_moves_use_existing_effect_handlers():
    effects = (ROOT / "include/constants/battle_move_effects.h").read_text(encoding="utf-8")
    records = (ROOT / "src/data/battle_moves.h").read_text(encoding="utf-8")
    for _, _, effect, *_ in EXPECTED:
        assert f"#define {effect} " in effects
    # Variable-power Grass Knot must use the target-weight calculation.
    grass_knot = records.split("[MOVE_GRASS_KNOT] =", 1)[1].split("\n    },", 1)[0]
    assert ".effect = EFFECT_LOW_KICK" in grass_knot
    # These recharge moves use the existing recharge state machine, not a generic hit.
    for symbol in ["GIGA_IMPACT", "ROAR_OF_TIME", "ROCK_WRECKER"]:
        entry = records.split(f"[MOVE_{symbol}] =", 1)[1].split("\n    },", 1)[0]
        assert ".effect = EFFECT_RECHARGE" in entry


if __name__ == "__main__":
    test_gen4_move_ids_and_runtime_records()
    test_new_moves_use_existing_effect_handlers()
    print("PASS: 32 Gen 4 moves with IDs, damage categories, data, names, descriptions and animation pointers.")
