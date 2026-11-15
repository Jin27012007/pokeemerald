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
    assert "third_ability_slot_not_supported_by_emerald_struct" in blockers
    assert "exp_yield_exceeds_emerald_u8" in blockers
    assert row["abilities"][2]["emerald_struct_slot_supported"] is False
    assert row["statistics_emerald_initializer_values"]["evYield_HP"] == 0
    assert row["statistics_emerald_initializer_values"]["evYield_Attack"] == 1
    assert audit["counts"]["species_with_hidden_ability"] == 1
    assert audit["counts"]["species_with_exp_yield_above_255"] == 1


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
    test_symbol_mappings_keep_source_and_emerald_ids_separate()
    test_emerald_layout_blockers_are_explicit()
    test_unmapped_held_item_is_not_guessed()
    test_source_enum_id_mismatch_is_rejected()
    print("PASS: explicit source-to-Emerald enum mappings, field limits and runtime blockers.")


if __name__ == "__main__":
    main()
