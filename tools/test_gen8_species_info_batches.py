#!/usr/bin/env python3
"""Regression tests for deterministic and isolated Gen 4 SpeciesInfo batching."""
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


def make_fixture():
    canonical = []
    compact = []
    for dex in range(1, 899):
        is_batch = 387 <= dex <= 388
        symbol = f"TESTMON_{dex}"
        if is_batch:
            canonical.append({
                "national_dex": dex,
                "national_symbol": symbol,
                "source_record_symbol": symbol,
                "source_national_dex_symbol": f"NATIONAL_DEX_{symbol}",
                "source_national_dex_matches_selected": True,
                "source_generation": 4,
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
                "generation": 4,
                "national_dex_symbol": f"NATIONAL_DEX_{symbol}",
                "source_raw": {"baseHP": "50"},
                "source_expanded_fields": {
                    "baseHP": "50",
                    "baseAttack": "60",
                    "baseDefense": "40",
                    "baseSpeed": "70",
                    "baseSpAttack": "80",
                    "baseSpDefense": "50",
                    "evYield_Attack": "1",
                    "types": "MON_TYPES(TYPE_GRASS, TYPE_POISON)",
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
                "types": [12, 4],
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
        "types": {"GRASS": 12, "POISON": 4},
        "egg_groups": {"MONSTER": 1, "GRASS": 7},
        "growth_rates": {"MEDIUM_FAST": 3},
        "abilities": {"OVERGROW": 65, "NONE": 0, "TEST_ALIAS": None, "TEST_HIDDEN": 34},
        "items": {"NONE": 0, "TEST_ITEM": 25},
    }
    return canonical, compact, domains


def batch_spec():
    return {
        "batch_id": "test_batch",
        "species_introduction_generation": 4,
        "national_dex_start": 387,
        "national_dex_end": 388,
        "expected_species_count": 2,
        "source_generation_range": [1, 8],
    }


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
    assert first["types_source_ids"] == [12, 4]
    assert first["types_source_symbols"] == ["GRASS", "POISON"]
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
    canonical[386]["source_generation"] = 3
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
    assert row["source_fields_raw"] == {"baseHP": "50"}
    assert row["source_fields_expanded"]["baseHP"] == "50"
    assert row["source_initializer_raw"] == "{ .baseHP = 50 }"
    assert row["source_initializer_expanded"] == "{ .baseHP = 50 }"


def main():
    test_batch_is_complete_and_staging_only()
    test_batch_is_deterministic()
    test_missing_canonical_row_is_rejected()
    test_source_file_generation_is_preserved_and_must_match()
    test_unresolved_source_record_is_rejected()
    test_raw_and_expanded_source_are_both_preserved()
    print("PASS: Gen 4 batch identity, field coverage, provenance, determinism and runtime isolation.")


if __name__ == "__main__":
    main()
