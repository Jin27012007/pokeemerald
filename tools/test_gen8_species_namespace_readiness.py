#!/usr/bin/env python3
"""Regression tests for the read-only Gen 8 namespace readiness audit."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/audit_gen8_species_namespace_readiness.py"
SPEC = importlib.util.spec_from_file_location("gen8_namespace_audit", SCRIPT)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

MAPPING = ROOT / "reports/gen8-conversion/species_id_mapping.json"
OUTPUT = ROOT / "reports/gen8-conversion/species_namespace_readiness.json"
SPECIES_HEADER = ROOT / "include/constants/species.h"
POKEDEX_HEADER = ROOT / "include/constants/pokedex.h"


def main() -> int:
    rows = json.loads(MAPPING.read_text(encoding="utf-8"))
    species_header = SPECIES_HEADER.read_text(encoding="utf-8")
    pokedex_header = POKEDEX_HEADER.read_text(encoding="utf-8")
    report = json.loads(OUTPUT.read_text(encoding="utf-8"))
    expected = module.audit(rows, species_header, pokedex_header)
    assert report == expected, "Readiness report is not deterministic"

    assert report["status"] == "blocked_before_internal_id_expansion"
    assert report["read_only_audit"] is True
    assert report["production_files_modified"] is False
    assert report["internal_ids_proposed_or_assigned"] is False
    assert report["num_species_change_allowed"] is False
    assert report["coverage"] == {
        "canonical_national_dex_rows": 898,
        "existing_emerald_internal_ids": 386,
        "species_without_production_internal_ids": 512,
        "existing_ids_preserved_and_verified": 386,
    }

    namespace = report["current_production_namespace"]
    assert namespace["last_existing_ordinary_species_id"] == 411
    assert namespace["egg_sentinel_id"] == 412
    assert namespace["num_species_definition"] == "SPECIES_EGG"
    assert namespace["unown_auxiliary_ids"] == 27

    assert len(report["preserved_species"]) == 386
    assert len(report["unallocated_species"]) == 512
    assert all(row["status"] == "no_production_internal_id" for row in report["unallocated_species"])
    assert all("internal_id" not in row for row in report["unallocated_species"])
    assert len(report["confirmed_promotion_blockers"]) >= 8

    # Production species constants and sentinels are expected to remain untouched.
    assert "#define SPECIES_CHIMECHO 411" in species_header
    assert "#define SPECIES_EGG 412" in species_header
    assert "#define NUM_SPECIES SPECIES_EGG" in species_header
    assert "#define NATIONAL_DEX_COUNT  NATIONAL_DEX_CALYREX" in pokedex_header

    print("PASS: all 898 Dex identities accounted for; 386 original IDs match the production header.")
    print("PASS: 512 entries remain unassigned; Egg, NUM_SPECIES and Unown sentinels are unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
