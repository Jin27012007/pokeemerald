#!/usr/bin/env python3
"""Static integration tests for Generation 4 held-item and move-category mechanics."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_physical_special_split_keeps_emerald_legacy_default():
    constants = read("include/constants/pokemon.h")
    pokemon_h = read("include/pokemon.h")
    pokemon_c = read("src/pokemon.c")
    battle_h = read("include/battle.h")
    commands = read("src/battle_script_commands.c")
    assert "#define DAMAGE_CATEGORY_AUTO     0" in constants
    assert "#define DAMAGE_CATEGORY_PHYSICAL 1" in constants
    assert "u8 category; // DAMAGE_CATEGORY_AUTO keeps original Emerald type-based damage." in pokemon_h
    assert "u8 GetMoveCategory(u16 move);" in pokemon_h
    assert "if (gBattleMoves[move].category != DAMAGE_CATEGORY_AUTO)" in pokemon_c
    assert "return IS_TYPE_PHYSICAL(gBattleMoves[move].type) ? DAMAGE_CATEGORY_PHYSICAL : DAMAGE_CATEGORY_SPECIAL;" in pokemon_c
    assert "isPhysical = GetMoveCategory(move) == DAMAGE_CATEGORY_PHYSICAL;" in pokemon_c
    assert "GetMoveCategory(gCurrentMove) == DAMAGE_CATEGORY_PHYSICAL" in commands
    # Old moves omit category and therefore retain Emerald's type-based behavior.
    old_tackle = read("src/data/battle_moves.h").split("[MOVE_TACKLE] =", 1)[1].split("\n    },", 1)[0]
    assert ".category =" not in old_tackle
    fairy_moves = read("src/data/battle_moves.h")
    assert ".category = DAMAGE_CATEGORY_PHYSICAL" in fairy_moves[fairy_moves.index("[MOVE_PLAY_ROUGH] ="):]
    assert ".category = DAMAGE_CATEGORY_SPECIAL" in fairy_moves[fairy_moves.index("[MOVE_MOONBLAST] ="):]
    assert ".category = DAMAGE_CATEGORY_STATUS" in fairy_moves[fairy_moves.index("[MOVE_BABY_DOLL_EYES] ="):]


def test_black_sludge_heals_poison_and_hurts_other_types():
    hold = read("include/constants/hold_effects.h")
    items = read("src/data/items.h")
    battle = read("src/battle_util.c")
    scripts = read("data/battle_scripts_1.s")
    headers = read("include/battle_scripts.h")
    assert "#define HOLD_EFFECT_BLACK_SLUDGE   69" in hold
    black = items.split("[ITEM_BLACK_SLUDGE] =", 1)[1].split("\n    },", 1)[0]
    assert ".holdEffect = HOLD_EFFECT_BLACK_SLUDGE" in black
    assert "gBattleMons[battler].type1 == TYPE_POISON || gBattleMons[battler].type2 == TYPE_POISON" in battle
    assert "gBattleMons[battler].maxHP / 16" in battle
    assert "gBattleMons[battler].maxHP / 8" in battle
    assert "PREPARE_ITEM_BUFFER(gBattleTextBuff1, ITEM_BLACK_SLUDGE)" in battle
    assert "BattleScript_ItemHurtByBlackSludge_End2::" in scripts
    assert "extern const u8 BattleScript_ItemHurtByBlackSludge_End2[];" in headers
    assert "printstring STRINGID_PKMNHURTBY" in scripts
    assert "tryfaintmon BS_ATTACKER" in scripts


def test_metronome_item_accumulates_repeated_move_power():
    hold = read("include/constants/hold_effects.h")
    item = read("src/data/items.h").split("[ITEM_METRONOME] =", 1)[1].split("\n    },", 1)[0]
    battle_h = read("include/battle.h")
    pokemon = read("src/pokemon.c")
    commands = read("src/battle_script_commands.c")
    assert "#define HOLD_EFFECT_METRONOME      70" in hold
    assert ".holdEffect = HOLD_EFFECT_METRONOME" in item
    assert "u16 metronomeMove;" in battle_h and "u8 metronomeCount;" in battle_h
    assert "100 + 20 * repeats" in pokemon
    assert "gBattleMons[gBattlerAttacker].item == ITEM_METRONOME" in commands
    assert "gDisableStructs[gBattlerAttacker].metronomeCount < 5" in commands


def test_honey_is_consumable_and_uses_encounter_lure():
    item = read("src/data/items.h").split("[ITEM_HONEY] =", 1)[1].split("\n    },", 1)[0]
    use = read("src/item_use.c")
    desc = read("src/data/text/item_descriptions.h")
    assert ".fieldUseFunc = ItemUseOutOfBattle_BlackWhiteFlute" in item
    assert "gSpecialVar_ItemId == ITEM_WHITE_FLUTE || gSpecialVar_ItemId == ITEM_HONEY" in use
    assert "if (gSpecialVar_ItemId == ITEM_HONEY)\n            RemoveUsedItem();" in use
    assert "attracts wild" in desc[desc.index("sHoneyDesc"):desc.index("sLaggingTailDesc")]


def test_oval_stone_and_trade_evolution_paths_are_implemented():
    constants = read("include/constants/pokemon.h")
    pokemon = read("src/pokemon.c")
    assert "#define EVO_LEVEL_HOLD_ITEM_DAY 16" in constants
    assert "case EVO_LEVEL_HOLD_ITEM_DAY:" in pokemon
    assert "heldItem == ITEM_OVAL_STONE" in pokemon
    assert "DAY_EVO_HOUR_BEGIN" in pokemon and "DAY_EVO_HOUR_END" in pokemon
    oval = pokemon.split("case EVO_LEVEL_HOLD_ITEM_DAY:", 1)[1].split("break;", 1)[0]
    assert "heldItem = ITEM_NONE" in oval
    assert "case EVO_TRADE_ITEM:" in pokemon
    assert "heldItem = ITEM_NONE;" in pokemon


def test_items_marked_as_audited_only_after_runtime_support():
    pipeline = read("tools/gen8_build_pending_tables.py")
    for name in ["BLACK_SLUDGE", "ELECTIRIZER", "HONEY", "LAGGING_TAIL",
                 "MAGMARIZER", "METRONOME", "OVAL_STONE", "WIDE_LENS"]:
        assert f'"{name}"' in pipeline


if __name__ == "__main__":
    test_physical_special_split_keeps_emerald_legacy_default()
    test_black_sludge_heals_poison_and_hurts_other_types()
    test_metronome_item_accumulates_repeated_move_power()
    test_honey_is_consumable_and_uses_encounter_lure()
    test_oval_stone_and_trade_evolution_paths_are_implemented()
    test_items_marked_as_audited_only_after_runtime_support()
    print("PASS: Gen 4 damage categories, Black Sludge, Metronome item, Honey, Oval Stone and trade-item evolution.")
