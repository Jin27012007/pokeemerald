#!/usr/bin/env python3
"""Test the proposed Gen 8 species namespace and alternate-form policy."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/gen8_species_id_scheme.py"
SPEC = importlib.util.spec_from_file_location("gen8_species_id_scheme", SCRIPT)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)

MAPPING = ROOT / "reports/gen8-conversion/species_id_mapping.json"
OUTPUT = ROOT / "reports/gen8-conversion/species_id_scheme_proposal.json"
SPECIES_HEADER = ROOT / "include/constants/species.h"
POKEMON_HEADER = ROOT / "include/pokemon.h"
POKEDEX_HEADER = ROOT / "include/constants/pokedex.h"
FORM_POLICY = ROOT / "data/pokemon/gen8_form_policy.json"


def main() -> int:
    rows = json.loads(MAPPING.read_text(encoding="utf-8"))
    species_header = SPECIES_HEADER.read_text(encoding="utf-8")
    pokemon_header = POKEMON_HEADER.read_text(encoding="utf-8")
    pokedex_header = POKEDEX_HEADER.read_text(encoding="utf-8")
    form_policy = json.loads(FORM_POLICY.read_text(encoding="utf-8"))
    proposal = json.loads(OUTPUT.read_text(encoding="utf-8"))

    expected = module.build_proposal(
        rows, species_header, pokemon_header, pokedex_header, form_policy
    )
    assert proposal == expected, "Species-ID proposal output is not deterministic"

    assert proposal["status"] == "candidate_scheme_only_not_runtime"
    assert proposal["runtime_activation_allowed"] is False
    assert proposal["production_ids_modified"] is False
    assert proposal["species_header_modified"] is False
    assert proposal["save_migration_implemented"] is False

    assert proposal["counts"] == {
        "existing_canonical_species": 386,
        "new_canonical_species": 512,
        "legacy_old_unown_aliases": 25,
        "dynamic_unown_auxiliary_values": 27,
    }

    current = proposal["current_namespace"]
    candidate = proposal["candidate_namespace"]
    assert current == {
        "species_none": 0,
        "last_existing_canonical_species": 411,
        "egg_sentinel": 412,
        "num_species_definition": "SPECIES_EGG",
        "dynamic_unown_first": 413,
        "dynamic_unown_last": 439,
        "legacy_old_unown_first": 252,
        "legacy_old_unown_last": 276,
    }
    assert candidate == {
        "new_species_first": 412,
        "new_species_last": 923,
        "egg_sentinel": 924,
        "num_species": 924,
        "dynamic_unown_first": 925,
        "dynamic_unown_last": 951,
        "legacy_old_unown_first": 252,
        "legacy_old_unown_last": 276,
    }

    species = proposal["species"]
    assert len(species) == 898
    assert [row["national_dex"] for row in species] == list(range(1, 899))
    existing = [row for row in species if row["allocation_status"] == "existing_id_preserved"]
    new = [row for row in species if row["allocation_status"] == "candidate_id_not_runtime"]
    assert len(existing) == 386
    assert len(new) == 512
    assert all(
        row["candidate_internal_id"] == row["current_internal_id"]
        for row in existing
    )
    assert [row["candidate_internal_id"] for row in new] == list(range(412, 924))
    assert [row["national_dex"] for row in new] == sorted(row["national_dex"] for row in new)

    sentinel = proposal["sentinel_migration"]
    assert sentinel["required_before_activation"] is True
    assert sentinel["egg"] == {
        "symbol": "SPECIES_EGG",
        "current_value": 412,
        "candidate_value": 924,
    }
    unown = sentinel["dynamic_unown"]
    assert len(unown) == 27
    assert [row["current_internal_id"] for row in unown] == list(range(413, 440))
    assert [row["candidate_internal_id"] for row in unown] == list(range(925, 952))
    assert sentinel["raw_boxpokemon_byte_rewrite_allowed"] is False

    legacy = sentinel["legacy_old_unown"]
    assert len(legacy) == 25
    assert [row["current_internal_id"] for row in legacy] == list(range(252, 277))
    assert all(
        row["candidate_internal_id"] == row["current_internal_id"]
        for row in legacy
    )

    form = proposal["form_policy"]
    assert form["alternate_forms_create_national_dex_entries"] is False
    assert form["alternate_forms_create_species_internal_ids"] is False
    assert form["unclassified_forms_runtime_allowed"] is False
    assert set(form["allowed_policies"]) == {
        "canonical", "cosmetic", "persistent_separate", "temporary_battle"
    }
    assert form_policy["record_schema"]["no_implicit_default_policy"] is True

    # Confirm the proposal did not promote the candidate values in production.
    assert "#define SPECIES_EGG 412" in species_header
    assert "#define NUM_SPECIES SPECIES_EGG" in species_header
    assert "#define SPECIES_CHIMECHO 411" in species_header
    assert "#define NUM_UNOWN_FORMS 28" in pokemon_header
    assert "#define NATIONAL_DEX_COUNT  NATIONAL_DEX_CALYREX" in pokedex_header

    print("PASS: 898 canonical species; 386 old IDs preserved; 512 proposed IDs are 412-923.")
    print("PASS: Egg migration 412->924; dynamic Unown 413-439->925-951.")
    print("PASS: 25 OLD_UNOWN IDs stay 252-276; alternate forms have no separate species ID.")
    print("PASS: proposal remains non-runtime and production constants are unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
