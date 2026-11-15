#!/usr/bin/env python3
"""Regression tests for deterministic and isolated Gen 4–Gen 6 SpeciesInfo batches."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "gen8_species_info_batches", ROOT / "tools/gen8_species_info_batches.py"
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def make_fixture(batch=None):
    batch = batch or batch_spec()
    canonical = []
    compact = []
    for dex in range(1, 899):
        is_batch = batch["national_dex_start"] <= dex <= batch["national_dex_start"] + 1
        symbol = f"TESTMON_{dex}"
        if is_batch:
            canonical.append({
                "national_dex": dex,
                "national_symbol": symbol,
                "source_record_symbol": symbol,
                "source_national_dex_symbol": f"NATIONAL_DEX_{symbol}",
                "source_national_dex_matches_selected": True,
                "source_generation": batch["species_introduction_generation"],
                "record_provenance": "expansion_source_initializer",
                "source_fields_present": sorted(module.REQUIRED_SOURCE_FIELDS),
                "source_complete": True,
                "source_missing_fields": [],
                "source_unresolved_fields": [],
                "source_fields_resolved": True,
                "target_mapping_compatible": False,
                "runtime_gaps": ["test_gap"],
            })
            compact.append({
                "species_symbol": symbol,
                "generation": batch["species_introduction_generation"],
                "national_dex_symbol": f"NATIONAL_DEX_{symbol}",
                "source_raw": {
                    "baseHP": "50",
                    "types": (
                        "#if P_UPDATED_TYPES >= GEN_6\n"
                        "MON_TYPES(TYPE_FAIRY, TYPE_FLYING)\n"
                        "#else\n"
                        "MON_TYPES(TYPE_NORMAL, TYPE_FLYING)\n"
                        "#endif"
                    ),
                    "eggGroups": "MON_EGG_GROUPS(EGG_GROUP_MONSTER, EGG_GROUP_GRASS)",
                    "abilities": "{ ABILITY_OVERGROW, ABILITY_TEST_ALIAS, ABILITY_TEST_HIDDEN }",
                },
                "source_expanded_fields": {
                    "baseHP": "50",
                    "baseAttack": "60",
                    "baseDefense": "40",
                    "baseSpeed": "70",
                    "baseSpAttack": "80",
                    "baseSpDefense": "50",
                    "evYield_Attack": "1",
                    "types": "MON_TYPES((P_UPDATED_TYPES >= GEN_6 ? TYPE_FAIRY : TYPE_NORMAL), TYPE_FLYING)",
                    "eggGroups": "MON_EGG_GROUPS(EGG_GROUP_MONSTER, EGG_GROUP_GRASS)",
                    "abilities": "{ ABILITY_OVERGROW, ABILITY_TEST_ALIAS, ABILITY_TEST_HIDDEN }",
                },
                "source_initializer_raw": "{ .baseHP = 50 }",
                "source_initializer_expanded": "{ .baseHP = 50 }",
                "statistics": {
                    "baseHP": 50, "baseAttack": 60, "baseDefense": 40,
                    "baseSpeed": 70, "baseSpAttack": 80, "baseSpDefense": 50,
                    "catchRate": 45, "expYield": 120,
                    "evYield_Attack": 1, "evYield_Defense": 0,
                },
                "gender_ratio": 127,
                "friendship": 50,
                "growth_rate": 3,
                "types": [19, 3],
                "egg_groups": [1, 7],
                "abilities": [65, None],
                "hidden_ability": 34,
                "item_common": 0,
                "item_rare": 25,
                "body_color": 3,
                "source_complete": True,
                "source_fields_resolved": True,
                "source_missing_fields": [],
                "source_unresolved_fields": [],
                "status": "compact_fields_resolved",
            })
        else:
            canonical.append({
                "national_dex": dex,
                "national_symbol": symbol,
                "source_record_symbol": f"SPECIES_{symbol}",
                "source_national_dex_symbol": None,
                "source_national_dex_matches_selected": True,
                "source_generation": 3,
                "record_provenance": "existing_emerald_runtime_record",
                "source_fields_present": [],
                "source_complete": True,
                "source_missing_fields": [],
                "source_unresolved_fields": [],
                "source_fields_resolved": True,
                "target_mapping_compatible": True,
                "runtime_gaps": [],
            })
    domains = {
        "types": {"GRASS": 12, "POISON": 4, "FAIRY": 19, "NORMAL": 1, "FLYING": 3},
        "egg_groups": {"MONSTER": 1, "GRASS": 7},
        "growth_rates": {"MEDIUM_FAST": 3},
        "abilities": {"OVERGROW": 65, "NONE": 0, "TEST_ALIAS": None, "TEST_HIDDEN": 34},
        "items": {"NONE": 0, "TEST_ITEM": 25},
    }
    return canonical, compact, domains


def batch_spec(generation=4):
    start, introduction_generation = {4: (387, 4), 5: (494, 5), 6: (650, 6)}[generation]
    return {
        "batch_id": "test_batch",
        "species_introduction_generation": introduction_generation,
        "national_dex_start": start,
        "national_dex_end": start + 1,
        "expected_species_count": 2,
        "source_generation_range": [1, 8],
    }


def test_gen5_batch_configuration_and_generation():
    configured = module.BATCHES[5]
    assert configured["batch_id"] == "gen5_species_info"
    assert configured["species_introduction_generation"] == 5
    assert configured["national_dex_start"] == 494
    assert configured["national_dex_end"] == 649
    assert configured["expected_species_count"] == 156

    fixture_spec = batch_spec(5)
    canonical, compact, domains = make_fixture(fixture_spec)
    result = module.build_batch(
        canonical, compact, domains,
        {"repository": "https://github.com/example/source", "commit": "b" * 40},
        fixture_spec,
    )
    assert result["national_dex_range"] == [494, 495]
    assert result["species_introduction_generation"] == 5
    assert result["species_count"] == 2
    assert [row["national_dex"] for row in result["species"]] == [494, 495]
    assert result["runtime_activation_allowed"] is False
    assert result["species"][0]["source_generation"] == 5
    assert result["species"][0]["source_file"].endswith("gen_5_families.h")


def test_gen6_batch_configuration_and_generation():
    configured = module.BATCHES[6]
    assert configured["batch_id"] == "gen6_species_info"
    assert configured["species_introduction_generation"] == 6
    assert configured["national_dex_start"] == 650
    assert configured["national_dex_end"] == 721
    assert configured["expected_species_count"] == 72

    fixture_spec = batch_spec(6)
    canonical, compact, domains = make_fixture(fixture_spec)
    result = module.build_batch(
        canonical, compact, domains,
        {"repository": "https://github.com/example/source", "commit": "c" * 40},
        fixture_spec,
    )
    assert result["national_dex_range"] == [650, 651]
    assert result["species_introduction_generation"] == 6
    assert result["species_count"] == 2
    assert [row["national_dex"] for row in result["species"]] == [650, 651]
    assert result["runtime_activation_allowed"] is False
    assert result["species"][0]["source_generation"] == 6
    assert result["species"][0]["source_file"].endswith("gen_6_families.h")


def test_batch_is_complete_and_staging_only():
    canonical, compact, domains = make_fixture()
    result = module.build_batch(
        canonical, compact, domains,
        {"repository": "https://github.com/example/source", "commit": "a" * 40},
        batch_spec(),
    )
    assert result["species_count"] == 2
    assert result["national_dex_range"] == [387, 388]
    assert result["species_introduction_generation"] == 4
    assert result["status"] == "staging_only_not_runtime"
    assert result["runtime_activation_allowed"] is False
    assert [row["national_dex"] for row in result["species"]] == [387, 388]
    first = result["species"][0]
    assert first["statistics"]["baseHP"] == 50
    assert first["statistics"]["evYield_Attack"] == 1
    assert "evYield_Defense" not in first["statistics"]
    assert first["types_source_ids"] == [19, 3]
    assert first["types_source_symbols"] == ["FAIRY", "FLYING"]
    assert first["egg_groups_source_symbols"] == ["MONSTER", "GRASS"]
    assert first["abilities_source_symbols"] == ["OVERGROW", "TEST_ALIAS", "TEST_HIDDEN"]
    assert first["abilities_source_ids"] == [65, None]
    assert first["abilities_numeric_ids_complete"] is False
    assert first["hidden_ability_source_symbol"] == "TEST_HIDDEN"
    assert first["source_generation"] == 4
    assert first["source_file"].endswith("gen_4_families.h")
    assert first["runtime_gap_codes"] == ["test_gap"]
    assert "emerald_internal_id" not in first
    assert "species_internal_id" not in first


def test_family_macro_brace_initializer_is_preserved():
    canonical, compact, domains = make_fixture()
    compact[0]["source_raw"]["types"] = "ROTOM_FAMILY_TYPES"
    compact[0]["source_expanded_fields"]["types"] = "{ TYPE_ELECTRIC, TYPE_GHOST }"
    compact[0]["types"] = [14, 8]
    domains["types"].update({"ELECTRIC": 14, "GHOST": 8})

    result = module.build_batch(
        canonical, compact, domains,
        {"repository": "https://github.com/example/source", "commit": "a" * 40},
        batch_spec(),
    )
    first = result["species"][0]
    assert first["types_source_symbols"] == ["ELECTRIC", "GHOST"]
    assert first["types_source_ids"] == [14, 8]
    assert first["source_fields_raw"]["types"] == "ROTOM_FAMILY_TYPES"


def test_batch_is_deterministic():
    canonical, compact, domains = make_fixture()
    args = (
        canonical, compact, domains,
        {"repository": "https://github.com/example/source", "commit": "a" * 40},
        batch_spec(),
    )
    first = json.dumps(module.build_batch(*args), sort_keys=True)
    second = json.dumps(module.build_batch(*args), sort_keys=True)
    assert first == second


def test_missing_canonical_row_is_rejected():
    canonical, compact, domains = make_fixture()
    canonical = [row for row in canonical if row["national_dex"] != 388]
    try:
        module.build_batch(canonical, compact, domains,
            {"repository": "https://github.com/example/source", "commit": "a" * 40},
            batch_spec())
    except RuntimeError as error:
        assert "898 canonical metadata rows" in str(error)
    else:
        raise AssertionError("incomplete canonical catalog was accepted")


def test_source_file_generation_is_preserved_and_must_match():
    canonical, compact, domains = make_fixture()
    canonical[batch_spec()["national_dex_start"] - 1]["source_generation"] = 3
    compact[0]["generation"] = 3
    result = module.build_batch(
        canonical, compact, domains,
        {"repository": "https://github.com/example/source", "commit": "a" * 40},
        batch_spec(),
    )
    first = result["species"][0]
    assert result["species_introduction_generation"] == 4
    assert first["source_generation"] == 3
    assert first["source_file"].endswith("gen_3_families.h")

    canonical, compact, domains = make_fixture()
    canonical[386]["source_generation"] = 5
    try:
        module.build_batch(canonical, compact, domains,
            {"repository": "https://github.com/example/source", "commit": "a" * 40},
            batch_spec())
    except RuntimeError as error:
        assert "parsed source generation disagrees" in str(error)
    else:
        raise AssertionError("mismatched source file generation was accepted")

    canonical, compact, domains = make_fixture()
    canonical[386]["source_national_dex_matches_selected"] = False
    try:
        module.build_batch(canonical, compact, domains,
            {"repository": "https://github.com/example/source", "commit": "a" * 40},
            batch_spec())
    except RuntimeError as error:
        assert "identity is not verified" in str(error)
    else:
        raise AssertionError("unverified source Dex identity was accepted")


def test_unresolved_source_record_is_rejected():
    canonical, compact, domains = make_fixture()
    compact[0]["source_fields_resolved"] = False
    try:
        module.build_batch(canonical, compact, domains,
            {"repository": "https://github.com/example/source", "commit": "a" * 40},
            batch_spec())
    except RuntimeError as error:
        assert "not fully resolved" in str(error)
    else:
        raise AssertionError("unresolved SpeciesInfo record was accepted")


def test_raw_and_expanded_source_are_both_preserved():
    canonical, compact, domains = make_fixture()
    result = module.build_batch(
        canonical, compact, domains,
        {"repository": "https://github.com/example/source", "commit": "a" * 40},
        batch_spec(),
    )
    row = result["species"][0]
    assert row["source_fields_raw"]["baseHP"] == "50"
    assert "#if P_UPDATED_TYPES >= GEN_6" in row["source_fields_raw"]["types"]
    assert row["source_fields_expanded"]["baseHP"] == "50"
    assert row["source_fields_expanded"]["types"] == (
        "MON_TYPES((P_UPDATED_TYPES >= GEN_6 ? TYPE_FAIRY : TYPE_NORMAL), TYPE_FLYING)"
    )
    assert row["source_initializer_raw"] == "{ .baseHP = 50 }"
    assert row["source_initializer_expanded"] == "{ .baseHP = 50 }"


def main():
    test_gen5_batch_configuration_and_generation()
    test_gen6_batch_configuration_and_generation()
    test_batch_is_complete_and_staging_only()
    test_family_macro_brace_initializer_is_preserved()
    test_batch_is_deterministic()
    test_missing_canonical_row_is_rejected()
    test_source_file_generation_is_preserved_and_must_match()
    test_unresolved_source_record_is_rejected()
    test_raw_and_expanded_source_are_both_preserved()
    print("PASS: Gen 4/Gen 5/Gen 6 batch identity, field coverage, provenance, determinism and runtime isolation.")


if __name__ == "__main__":
    main()
