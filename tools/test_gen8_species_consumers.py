#!/usr/bin/env python3
"""Regression tests for the automated species consumer inventory."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "audit_gen8_species_consumers", ROOT / "tools/audit_gen8_species_consumers.py"
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def test_namespace_inventory():
    namespace = module.parse_species_constants()
    assert namespace["egg_sentinel"] == 412
    assert namespace["num_species_expression"] == "SPECIES_EGG"
    expected_unown = {
        *(f"SPECIES_UNOWN_{letter}" for letter in "BCDEFGHIJKLMNOPQRSTUVWXYZ"),
        "SPECIES_UNOWN_EMARK",
        "SPECIES_UNOWN_QMARK",
    }
    actual_unown = {row["symbol"] for row in namespace["unown_calculated_constants"]}
    assert actual_unown == expected_unown, {
        "missing": sorted(expected_unown - actual_unown),
        "extra": sorted(actual_unown - expected_unown),
        "count": len(actual_unown),
    }
    # Emerald defines 25 letter forms (B-Z) plus ! and ? = 27 calculated forms.
    assert namespace["unown_calculated_count"] == 27
    assert namespace["numeric_collisions"] == {}
    assert namespace["max_explicit_ordinary_id"] == 411


def test_sentinel_and_bounds_contracts():
    module.test_index_safety_helpers()


def test_classifies_sentinel_table_access():
    level, reasons = module.risk_for(
        "value = gSpeciesInfo[species];", "species", "species_info", {"egg"}
    )
    assert level == "high"
    assert "sentinel_token_near_table_index" in reasons


def test_scans_core_consumers():
    findings, summary = module.scan_source()
    refs = {(f["path"], f["table"]) for f in findings}
    assert any(path == "src/pokemon.c" and table == "species_info" for path, table in refs)
    assert any(path == "src/pokemon_icon.c" and table == "icon" for path, table in refs)
    assert summary["scanned_source_files"] > 100
    assert summary["finding_count"] > 0


if __name__ == "__main__":
    test_namespace_inventory()
    test_sentinel_and_bounds_contracts()
    test_classifies_sentinel_table_access()
    test_scans_core_consumers()
    test_risk_for_rejects_in_range_sentinels_and_auxiliary_forms()
    test_scan_does_not_miss_multiline_species_table_index()
    print("PASS: consumer inventory parser, namespace and sentinel-bound regressions.")



def test_scan_does_not_miss_multiline_species_table_index():
    source = """
    value = gSpeciesInfo[
        species
    ];
    """
    # The line scanner is line-oriented and currently cannot safely associate
    # this index expression across physical lines. This fixture documents and
    # guards a conservative multiline expression collector.
    assert module.extract_multiline_table_refs(source, "species_info") == [
        "species"
    ]
