#!/usr/bin/env python3
"""Validate the staged Gen 8 species-ID allocation proposal."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/gen8_species_id_allocation_proposal.py"
SPEC = importlib.util.spec_from_file_location("gen8_id_proposal", SCRIPT)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

MAPPING = ROOT / "reports/gen8-conversion/species_id_mapping.json"
OUTPUT = ROOT / "reports/gen8-conversion/species_id_allocation_proposal.json"
SPECIES_HEADER = ROOT / "include/constants/species.h"


def main() -> int:
    rows = json.loads(MAPPING.read_text(encoding="utf-8"))
    header = SPECIES_HEADER.read_text(encoding="utf-8")
    proposal = json.loads(OUTPUT.read_text(encoding="utf-8"))
    expected = module.build_proposal(rows, header)
    assert proposal == expected, "Proposal output is not deterministic"

    assert proposal["status"] == "proposal_only_not_runtime"
    assert proposal["runtime_activation_allowed"] is False
    assert proposal["production_files_modified"] is False
    assert proposal["species_header_modified"] is False
    assert proposal["summary"] == {
        "canonical_species": 898,
        "existing_emerald_species": 386,
        "new_species_needing_ids": 512,
    }

    namespace = proposal["candidate_internal_namespace"]
    assert namespace["first_new_species_id"] == 412
    assert namespace["last_new_species_id"] == 923
    assert namespace["new_species_id_count"] == 512
    assert namespace["current_egg_sentinel_id"] == 412
    assert namespace["proposed_egg_sentinel_id"] == 924
    assert namespace["proposed_num_species"] == 924
    assert namespace["proposed_unown_auxiliary_first"] == 925
    assert namespace["proposed_unown_auxiliary_last"] == 951
    assert namespace["proposed_unown_auxiliary_count"] == 27

    species = proposal["species"]
    assert len(species) == 898
    assert [row["national_dex"] for row in species] == list(range(1, 899))
    existing = [row for row in species if row["allocation"] == "preserve_existing_internal_id"]
    new = [row for row in species if row["allocation"] == "candidate_new_internal_id_not_runtime"]
    assert len(existing) == 386
    assert len(new) == 512
    assert [row["proposed_emerald_internal_id"] for row in new] == list(range(412, 924))
    assert all(
        row["proposed_emerald_internal_id"] == row["current_emerald_internal_id"]
        for row in existing
    )

    # The proposal must never silently promote its candidate IDs in production.
    assert "#define SPECIES_EGG 412" in header
    assert "#define NUM_SPECIES SPECIES_EGG" in header
    assert "SPECIES_UNOWN_B (NUM_SPECIES + 1)" in header

    print("PASS: 898 rows; 386 original IDs preserved; 512 candidate IDs are unique and ordered.")
    print("PASS: Egg/NUM_SPECIES/Unown remain unchanged in production; proposal is non-runtime.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
