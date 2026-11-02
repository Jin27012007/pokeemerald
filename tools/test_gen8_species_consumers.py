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
    assert namespace["unown_calculated_count"] == 26
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
    print("PASS: consumer inventory parser, namespace and sentinel-bound regressions.")
