#!/usr/bin/env python3
"""Regression tests for the explicit Gen 8 SpeciesInfo compatibility ledger."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "gen8_species_runtime_mapping", ROOT / "tools/gen8_species_runtime_mapping.py"
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def fixture():
    domains = {
        "types": {"NORMAL": 1, "FAIRY": 19},
        "egg_groups": {"FIELD": 5},
        "growth_rates": {"MEDIUM_FAST": 0},
        "abilities": {"NONE": 0, "OVERGROW": 65, "HIDDEN_TEST": 101},
        "items": {"NONE": 0, "POTION": 1},
    }
    row = {
        "national_dex": 387,
        "national_symbol": "TESTMON",
        "source_species_symbol": "TESTMON",
        "source_generation": 3,
        "source_file": "src/data/pokemon/species_info/gen_3_families.h",
        "statistics": {
            "baseHP": 50, "baseAttack": 60, "baseDefense": 55,
            "baseSpeed": 45, "baseSpAttack": 50, "baseSpDefense": 50,
            "catchRate": 45, "expYield": 300, "evYield_Attack": 1,
        },
        "types_source_symbols": ["NORMAL", "FAIRY"],
        "types_source_ids": [1, 19],
        "egg_groups_source_symbols": ["FIELD", "FIELD"],
        "egg_groups_source_ids": [5, 5],
        "growth_rate_source_id": 0,
        "abilities_source_symbols": ["OVERGROW", "NONE", "HIDDEN_TEST"],
        "abilities_source_ids": [65, 0],
        "hidden_ability_source_symbol": "HIDDEN_TEST",
        "hidden_ability_source_id": 101,
        "item_common_source_id": 1,
        "item_rare_source_id": 0,
        "gender_ratio_source_value": 127,
        "friendship_source_value": 50,
        "body_color_source_value": 3,
    }
    batch = {
        "species_introduction_generation": 4,
        "status": "staging_only_not_runtime",
        "runtime_activation_allowed": False,
        "national_dex_range": [387, 387],
        "species_count": 1,
        "source_snapshot": {"repository": "https://github.com/example/source", "commit": "a" * 40},
        "source_enum_domains": domains,
        "species": [row],
    }
    dependencies = {
        "types": [
            {"type_symbol": "NORMAL", "source_type_id": 1, "emerald_type_id": 0,
             "type_chart_runtime_audited": True},
            {"type_symbol": "FAIRY", "source_type_id": 19, "emerald_type_id": None,
             "type_chart_runtime_audited": False},
        ],
        "egg_groups": [
            {"egg_group_symbol": "FIELD", "source_egg_group_id": 5,
             "emerald_egg_group_id": 5},
        ],
        "growth_rates": [
            {"growth_rate_symbol": "MEDIUM_FAST", "source_growth_rate_id": 0,
             "emerald_growth_rate_id": 0},
        ],
        "abilities": [
            {"ability_symbol": "NONE", "source_ability_id": 0,
             "emerald_ability_id": 0, "target_behavior_audited": True},
            {"ability_symbol": "OVERGROW", "source_ability_id": 65,
             "emerald_ability_id": 65, "target_behavior_audited": True},
            {"ability_symbol": "HIDDEN_TEST", "source_ability_id": 101,
             "emerald_ability_id": None, "target_behavior_audited": False},
        ],
        "items": [
            {"item_symbol": "POTION", "source_item_id": 1,
             "emerald_item_id": 14, "target_item_data_record_present": True,
             "target_item_behavior_audited": False},
        ],
    }
    return [batch], dependencies



def test_fairy_type_runtime_contract():
    constants = (ROOT / "include/constants/pokemon.h").read_text(encoding="utf-8")
    battle = (ROOT / "src/battle_main.c").read_text(encoding="utf-8")
    messages = (ROOT / "src/battle_message.c").read_text(encoding="utf-8")
    summary = (ROOT / "src/pokemon_summary_screen.c").read_text(encoding="utf-8")
    graphics_rules = (ROOT / "graphics_file_rules.mk").read_text(encoding="utf-8")

    assert "#define TYPE_MYSTERY          9" in constants
    assert "#define TYPE_DARK             17" in constants
    assert "#define TYPE_FAIRY            18" in constants
    assert "#define NUMBER_OF_MON_TYPES   19" in constants

    chart = battle.split("const u8 gTypeEffectiveness[372] =", 1)[1].split("};", 1)[0]
    triples = module.re.findall(
        r"(TYPE_[A-Z0-9_]+)\\s*,\\s*(TYPE_[A-Z0-9_]+)\\s*,\\s*(TYPE_MUL_[A-Z0-9_]+)",
        chart,
    )
    assert len(triples) == 124, len(triples)
    expected = {
        ("TYPE_FAIRY", "TYPE_FIGHTING", "TYPE_MUL_SUPER_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_DRAGON", "TYPE_MUL_SUPER_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_DARK", "TYPE_MUL_SUPER_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_FIRE", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_POISON", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_STEEL", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_FIGHTING", "TYPE_FAIRY", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_BUG", "TYPE_FAIRY", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_DARK", "TYPE_FAIRY", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_DRAGON", "TYPE_FAIRY", "TYPE_MUL_NO_EFFECT"),
        ("TYPE_POISON", "TYPE_FAIRY", "TYPE_MUL_SUPER_EFFECTIVE"),
        ("TYPE_STEEL", "TYPE_FAIRY", "TYPE_MUL_SUPER_EFFECTIVE"),
    }
    assert expected.issubset(set(triples))
    assert "TYPE_ENDTABLE, TYPE_ENDTABLE, TYPE_MUL_NO_EFFECT" in chart

    assert '[TYPE_FAIRY] = _("FAIRY")' in battle
    assert '[TYPE_FAIRY]    = _("a FAIRY move")' in messages
    assert "sSpriteAnim_TypeFairy" in summary
    assert "sSpriteAnim_TypeFairy," in summary
    assert "[TYPE_FAIRY] = 14" in summary
    assert "dark fairy" in graphics_rules.split("types :=", 1)[1].splitlines()[0]


def test_runtime_three_slot_ability_storage_contract():
    header = (ROOT / "include/pokemon.h").read_text(encoding="utf-8")
    pokemon = (ROOT / "src/pokemon.c").read_text(encoding="utf-8")
    battle_scripts = (ROOT / "src/battle_script_commands.c").read_text(encoding="utf-8")
    battle_main = (ROOT / "src/battle_main.c").read_text(encoding="utf-8")
    battle_ai = (ROOT / "src/battle_ai_script_commands.c").read_text(encoding="utf-8")
    controller_paths = (
        "src/battle_controller_opponent.c",
        "src/battle_controller_link_opponent.c",
        "src/battle_controller_link_partner.c",
        "src/battle_controller_player.c",
    )
    controllers = [
        (ROOT / path).read_text(encoding="utf-8")
        for path in controller_paths
    ]

    assert "#define NUM_ABILITY_SLOTS 3" in header
    assert "NUM_ABILITY_SLOTS = 3" in (ROOT / "tools/gen8_species_runtime_mapping.py").read_text(encoding="utf-8")
    assert "u8 abilities[NUM_ABILITY_SLOTS];" in header
    assert "u16 expYield;" in header
    assert "SpeciesInfo) == 0x1E" in pokemon

    assert "u8 abilityNumHigh:1;" in header
    assert "u8 unused:3;" in header
    assert "u8 unknown; // Bit 0 stores the high bit of the ability slot index." in header

    # The stored ability slot combines the original encrypted low bit with
    # one spare public BoxPokemon bit. Both values are read/written by the
    # normal MON_DATA_ABILITY_NUM path used by party and PC records.
    assert "substruct3->abilityNum | (boxMon->abilityNumHigh << 1)" in pokemon
    assert "substruct3->abilityNum = abilityNum & 1;" in pokemon
    assert "boxMon->abilityNumHigh = (abilityNum >> 1) & 1;" in pokemon

    assert "if (abilityNum >= NUM_ABILITY_SLOTS)" in pokemon
    assert "gLastUsedAbility = info->abilities[abilityNum];" in pokemon
    assert "bool8 SetMonAbilitySlot(struct Pokemon *mon, u8 abilitySlot)" in pokemon
    assert "abilitySlot >= NUM_ABILITY_SLOTS" in pokemon
    assert "GetSpeciesInfoSafe(species)->abilities[abilitySlot] == ABILITY_NONE" in pokemon

    # The battle struct size does not grow: the high slot bit uses its
    # previously unused byte. All reads go through the accessor.
    assert "GetBattleMonAbilityNum(const struct BattlePokemon *mon)" in pokemon
    assert "mon->unknown & 1" in pokemon
    assert "SetBattleMonAbilityNum(" in pokemon
    assert "SetBattleMonAbilityNum(\n        &gBattleMons[battler]" in pokemon
    assert "GetBattleMonAbilityNum(&gBattleMons[gActiveBattler])" in battle_scripts
    assert "GetBattleMonAbilityNum(&gBattleMons[gActiveBattler])" in battle_main
    assert all("SetBattleMonAbilityNum(&battleMon, GetMonData(" in source for source in controllers)
    assert all("battleMon.abilityNum = GetMonData(" not in source for source in controllers)

    # The AI now treats all three non-empty slots as possible for an unknown
    # opponent, both when guessing and when answering an ability query.
    assert "for (i = 0; i < NUM_ABILITY_SLOTS; i++)" in battle_ai
    assert "GetRandomSpeciesAbility(gBattleMons[battler].species)" in battle_ai
    assert "SpeciesCanHaveAbility(gBattleMons[battler].species, ability)" in battle_ai

    # Pickup used to collapse every nonzero ability index to slot 2 in C's
    # zero-based terms (Emerald's second slot). It now asks the common getter.
    assert battle_scripts.count("ability = GetMonAbility(&gPlayerParty[i]);") == 2
    assert "GetSpeciesInfoSafe(species)->abilities[1]" not in battle_scripts


def test_symbol_mappings_keep_source_and_emerald_ids_separate():
    batches, dependencies = fixture()
    mapping, audit = module.build_runtime_mapping(
        batches, dependencies, expected_species_count=1, strict_batch_contract=False
    )
    row = mapping["species"][0]
    assert row["national_dex"] == 387
    assert row["production_emerald_species_id"] is None
    assert row["types"][0]["source_id"] == 1
    assert row["types"][0]["emerald_id"] == 0
    assert row["types"][1]["source_id"] == 19
    assert row["types"][1]["emerald_id"] is None
    assert row["growth_rate"]["source_id"] == 0
    assert row["growth_rate"]["emerald_id"] == 0
    assert row["held_items"]["common"]["source_id"] == 1
    assert row["held_items"]["common"]["emerald_id"] == 14
    assert row["held_items"]["rare"]["symbol"] == "NONE"
    assert row["held_items"]["rare"]["emerald_id"] == 0
    assert mapping["runtime_activation_allowed"] is False
    assert audit["counts"]["runtime_ready_species"] == 0


def test_emerald_layout_blockers_are_explicit():
    batches, dependencies = fixture()
    mapping, audit = module.build_runtime_mapping(
        batches, dependencies, expected_species_count=1, strict_batch_contract=False
    )
    row = mapping["species"][0]
    blockers = set(row["runtime_blockers"])
    assert "type_enum_unmapped:FAIRY" in blockers
    assert "third_ability_slot_not_supported_by_emerald_struct" not in blockers
    assert "exp_yield_exceeds_emerald_u8" not in blockers
    assert row["abilities"][2]["emerald_struct_slot_supported"] is True
    assert row["statistics_emerald_initializer_values"]["expYield"] == 300
    assert row["max_level_raw_exp_reward"] == 300 * 100 // 7
    assert "max_level_exp_reward_exceeds_battle_u16" not in blockers
    assert audit["counts"]["maximum_exp_yield"] == 300
    assert audit["counts"]["maximum_level_exp_reward_fits_u16"] is True
    assert "hidden_ability_acquisition_flow_not_implemented" in row["runtime_semantics_pending"]
    assert row["statistics_emerald_initializer_values"]["evYield_HP"] == 0
    assert row["statistics_emerald_initializer_values"]["evYield_Attack"] == 1
    assert audit["counts"]["species_with_hidden_ability"] == 1
    assert audit["counts"]["species_with_exp_yield_above_255"] == 1


def test_real_gen8_dataset_base_exp_fits_species_and_battle_fields():
    batches = [module.load_json(path) for path in module.BATCH_PATHS]
    rows = [row for batch in batches for row in batch["species"]]
    values = [int(row["statistics"]["expYield"]) for row in rows]
    assert len(values) == 512
    assert sum(value > 255 for value in values) == 105
    assert max(values) == 390
    max_level_reward = max(values) * module.MAX_LEVEL // 7
    assert max_level_reward == 5571
    assert max_level_reward <= 65535


def test_exp_yield_unsigned_16_bit_and_battle_reward_bounds():
    batches, dependencies = fixture()
    batches[0]["species"][0]["statistics"]["expYield"] = 65535
    mapping, audit = module.build_runtime_mapping(
        batches, dependencies, expected_species_count=1, strict_batch_contract=False
    )
    row = mapping["species"][0]
    assert row["statistics_emerald_initializer_values"]["expYield"] == 65535
    assert row["max_level_raw_exp_reward"] == 65535 * 100 // 7
    assert "max_level_exp_reward_exceeds_battle_u16" in row["runtime_blockers"]
    assert audit["counts"]["maximum_level_exp_reward_fits_u16"] is False

    batches[0]["species"][0]["statistics"]["expYield"] = 65536
    try:
        module.build_runtime_mapping(
            batches, dependencies, expected_species_count=1, strict_batch_contract=False
        )
    except RuntimeError as error:
        assert "invalid source value for expYield" in str(error)
    else:
        raise AssertionError("expYield above the unsigned 16-bit limit was accepted")


def test_unmapped_held_item_is_not_guessed():
    mapped = module.map_held_item(
        999, {"NONE": 0, "UNKNOWN_ITEM": 999}, {}
    )
    assert mapped["symbol"] is None
    assert mapped["emerald_id"] is None
    assert mapped["mapping_status"] == "missing_item_dependency"


def test_source_enum_id_mismatch_is_rejected():
    try:
        module.map_symbol(
            "FAIRY", 18, {"FAIRY": 19}, {"FAIRY": {
                "source_type_id": 19, "emerald_type_id": None
            }},
            "source_type_id", "emerald_type_id", "type",
        )
    except RuntimeError as error:
        assert "source-ID mismatch" in str(error)
    else:
        raise AssertionError("mismatched source enum IDs were accepted")


def main():
    test_fairy_type_runtime_contract()
    test_runtime_three_slot_ability_storage_contract()
    test_symbol_mappings_keep_source_and_emerald_ids_separate()
    test_emerald_layout_blockers_are_explicit()
    test_real_gen8_dataset_base_exp_fits_species_and_battle_fields()
    test_exp_yield_unsigned_16_bit_and_battle_reward_bounds()
    test_unmapped_held_item_is_not_guessed()
    test_source_enum_id_mismatch_is_rejected()
    print("PASS: explicit source-to-Emerald enum mappings, field limits and runtime blockers.")


if __name__ == "__main__":
    main()
