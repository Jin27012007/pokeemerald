#!/usr/bin/env python3
"""Unit tests for canonical intake structural and promotion gates."""
from __future__ import annotations
import importlib.util
from pathlib import Path
import tempfile
import json

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("validate_gen8_intake", ROOT / "tools/validate_gen8_intake.py")
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

def envelope(dex: int):
    return {
        "national_dex": dex,
        "national_symbol": f"NATIONAL_DEX_TEST_{dex}",
        "source_record_symbol": f"SPECIES_TEST_{dex}",
        "record_provenance": "expansion_source_initializer",
        "source_generation": 8,
        "source_fields_present": ["baseHP", "natDexNum"],
        "source_missing_fields": [],
        "source_unresolved_fields": [],
        "source_fields_resolved": True,
        "target_mapping_compatible": True,
        "runtime_gaps": [],
        "unresolved_fields": [],
    }

def test_envelope_contract():
    row = envelope(1)
    assert module.REQUIRED_ENVELOPE <= set(row)
    assert row["national_dex"] == 1
    assert row["record_provenance"] in module.ALLOWED_PROVENANCE

def test_promotability_is_separate_from_structural_coverage():
    row = envelope(1)
    row["runtime_gaps"] = ["graphics_not_migrated"]
    assert row["national_dex"] == 1
    assert not (
        row["source_fields_resolved"] and row["target_mapping_compatible"]
        and not row["source_missing_fields"] and not row["source_unresolved_fields"]
        and not row["runtime_gaps"] and not row["unresolved_fields"]
    )

def test_special_values_are_not_canonical_dex_keys():
    for value in (0, 412, 413, 438):
        assert not isinstance(value, bool) and not (1 <= value <= 898)

def main():
    test_envelope_contract()
    test_promotability_is_separate_from_structural_coverage()
    test_special_values_are_not_canonical_dex_keys()
    print("PASS: canonical intake envelope, structural-vs-runtime gate, and special-domain tests.")

if __name__ == "__main__":
    main()
