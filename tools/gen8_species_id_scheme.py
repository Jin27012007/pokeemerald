#!/usr/bin/env python3
"""Generate a non-runtime Gen 8 species-ID and form-policy proposal."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "reports/gen8-conversion/species_id_mapping.json"
SPECIES_HEADER = ROOT / "include/constants/species.h"
POKEMON_HEADER = ROOT / "include/pokemon.h"
POKEDEX_HEADER = ROOT / "include/constants/pokedex.h"
FORM_POLICY = ROOT / "data/pokemon/gen8_form_policy.json"
DEFAULT_OUTPUT = ROOT / "reports/gen8-conversion/species_id_scheme_proposal.json"

CANONICAL_COUNT = 898
EXISTING_CANONICAL_COUNT = 386
NEW_CANONICAL_COUNT = 512
LEGACY_OLD_UNOWN_COUNT = 25
DYNAMIC_UNOWN_COUNT = 27
OLD_UNOWN_LETTERS = list("BCDEFGHIJKLMNOPQRSTUVWXYZ")
DYNAMIC_UNOWN_FORMS = OLD_UNOWN_LETTERS + ["EMARK", "QMARK"]


def read_text(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"Required input is missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def numeric_macro(source: str, name: str) -> int:
    match = re.search(rf"^#define\s+{re.escape(name)}\s+(\d+)\s*$", source, re.M)
    if not match:
        raise RuntimeError(f"Could not resolve numeric macro {name}")
    return int(match.group(1))


def species_macros(source: str) -> dict[str, int]:
    return {
        name: int(value)
        for name, value in re.findall(
            r"^#define\s+SPECIES_([A-Z0-9_]+)\s+(\d+)\s*$", source, re.M
        )
    }


def old_unown_ids(source: str) -> list[dict]:
    macros = species_macros(source)
    result = []
    for offset, letter in enumerate(OLD_UNOWN_LETTERS):
        symbol = f"OLD_UNOWN_{letter}"
        if symbol not in macros:
            raise RuntimeError(f"Legacy Unown macro missing: SPECIES_{symbol}")
        result.append({"symbol": f"SPECIES_{symbol}", "current_internal_id": macros[symbol]})

    values = [row["current_internal_id"] for row in result]
    if values != list(range(252, 277)):
        raise RuntimeError(f"Legacy OLD_UNOWN IDs changed or are not contiguous: {values}")
    return result


def dynamic_unown_offsets(species_header: str) -> list[dict]:
    expression_re = re.compile(
        r"^#define\s+SPECIES_UNOWN_([A-Z0-9_]+)\s+"
        r"\((NUM_SPECIES|SPECIES_UNOWN_B)\s*\+\s*(\d+)\)\s*$",
        re.M,
    )
    expressions = {
        name: (base, int(offset))
        for name, base, offset in expression_re.findall(species_header)
    }
    if set(expressions) != set(DYNAMIC_UNOWN_FORMS):
        missing = sorted(set(DYNAMIC_UNOWN_FORMS) - set(expressions))
        extra = sorted(set(expressions) - set(DYNAMIC_UNOWN_FORMS))
        raise RuntimeError(f"Unexpected dynamic Unown macro set: missing={missing}, extra={extra}")

    result = []
    for offset, name in enumerate(DYNAMIC_UNOWN_FORMS, start=1):
        base, expression_offset = expressions[name]
        expected_base = "NUM_SPECIES" if name == "B" else "SPECIES_UNOWN_B"
        expected_offset = 1 if name == "B" else offset - 1
        if base != expected_base or expression_offset != expected_offset:
            raise RuntimeError(
                f"Unexpected Unown expression for {name}: ({base} + {expression_offset}); "
                f"expected ({expected_base} + {expected_offset})"
            )
        result.append({
            "symbol": f"SPECIES_UNOWN_{name}",
            "offset_after_num_species": offset,
        })
    return result


def build_proposal(
    rows: list[dict],
    species_header: str,
    pokemon_header: str,
    pokedex_header: str,
    form_policy: dict,
) -> dict:
    if len(rows) != CANONICAL_COUNT:
        raise RuntimeError(f"Expected {CANONICAL_COUNT} canonical records, got {len(rows)}")
    if [int(row["national_dex"]) for row in rows] != list(range(1, CANONICAL_COUNT + 1)):
        raise RuntimeError("Canonical National Dex records must be ordered and continuous 1-898")

    existing = [row for row in rows if row.get("emerald_internal_id") is not None]
    new = [row for row in rows if row.get("emerald_internal_id") is None]
    if len(existing) != EXISTING_CANONICAL_COUNT or len(new) != NEW_CANONICAL_COUNT:
        raise RuntimeError(
            f"Expected {EXISTING_CANONICAL_COUNT} existing and {NEW_CANONICAL_COUNT} new species; "
            f"got {len(existing)} existing and {len(new)} new"
        )

    macros = species_macros(species_header)
    current_none = numeric_macro(species_header, "SPECIES_NONE")
    current_chimecho = numeric_macro(species_header, "SPECIES_CHIMECHO")
    current_egg = numeric_macro(species_header, "SPECIES_EGG")
    if current_none != 0 or current_chimecho != 411 or current_egg != 412:
        raise RuntimeError(
            f"Unexpected production layout: NONE={current_none}, "
            f"CHIMECHO={current_chimecho}, EGG={current_egg}"
        )
    if not re.search(r"^#define\s+NUM_SPECIES\s+SPECIES_EGG\s*$", species_header, re.M):
        raise RuntimeError("NUM_SPECIES must remain tied to SPECIES_EGG in the current production source")
    if not re.search(
        r"^#define\s+NATIONAL_DEX_COUNT\s+NATIONAL_DEX_CALYREX\s*$",
        pokedex_header,
        re.M,
    ):
        raise RuntimeError("Expected the canonical National Dex to end at Calyrex (898)")
    if numeric_macro(pokemon_header, "NUM_UNOWN_FORMS") != 28:
        raise RuntimeError("The current Unown personality model must retain 28 forms")

    old_unown = old_unown_ids(species_header)
    dynamic_unown = dynamic_unown_offsets(species_header)
    current_dynamic_first = current_egg + 1
    current_dynamic_last = current_egg + DYNAMIC_UNOWN_COUNT

    existing_ids = [int(row["emerald_internal_id"]) for row in existing]
    if len(set(existing_ids)) != EXISTING_CANONICAL_COUNT:
        raise RuntimeError("Existing canonical internal IDs contain duplicates")
    if max(existing_ids) != current_chimecho:
        raise RuntimeError(
            f"Existing canonical ID maximum must remain Chimecho ({current_chimecho}); "
            f"found {max(existing_ids)}"
        )
    for row in existing:
        symbol = row.get("normalized_symbol")
        if symbol not in macros:
            raise RuntimeError(f"Existing canonical species macro missing: SPECIES_{symbol}")
        if macros[symbol] != int(row["emerald_internal_id"]):
            raise RuntimeError(
                f"Existing ID mismatch for {symbol}: "
                f"mapping={row['emerald_internal_id']}, header={macros[symbol]}"
            )
        if int(row["emerald_internal_id"]) >= current_egg:
            raise RuntimeError(f"Existing species overlaps Egg: {symbol}")

    # Allocate only in this proposal. Runtime constants and save data remain untouched.
    next_candidate_id = current_egg
    proposed_species = []
    for row in rows:
        if row.get("emerald_internal_id") is not None:
            candidate_id = int(row["emerald_internal_id"])
            allocation = "existing_id_preserved"
        else:
            candidate_id = next_candidate_id
            next_candidate_id += 1
            allocation = "candidate_id_not_runtime"
        proposed_species.append({
            "national_dex": int(row["national_dex"]),
            "source_symbol": row.get("source_symbol"),
            "normalized_symbol": row.get("normalized_symbol"),
            "current_internal_id": row.get("emerald_internal_id"),
            "candidate_internal_id": candidate_id,
            "allocation_status": allocation,
        })

    candidate_new_ids = [
        row["candidate_internal_id"]
        for row in proposed_species
        if row["allocation_status"] == "candidate_id_not_runtime"
    ]
    proposed_egg = next_candidate_id
    proposed_num_species = proposed_egg
    proposed_dynamic_first = proposed_num_species + 1
    proposed_dynamic_last = proposed_num_species + DYNAMIC_UNOWN_COUNT

    if candidate_new_ids != list(range(current_egg, current_egg + NEW_CANONICAL_COUNT)):
        raise RuntimeError("Candidate ID allocation is not a continuous ascending-Dex sequence")
    if proposed_egg != 924 or proposed_num_species != 924:
        raise RuntimeError(f"Unexpected proposed Egg/NUM_SPECIES values: {proposed_egg}")
    if proposed_dynamic_last != 951:
        raise RuntimeError(f"Unexpected proposed dynamic Unown range end: {proposed_dynamic_last}")
    if set(candidate_new_ids) & set(existing_ids):
        raise RuntimeError("Candidate IDs overlap preserved species IDs")
    if set(candidate_new_ids) & {item["current_internal_id"] for item in old_unown}:
        raise RuntimeError("Candidate IDs overlap legacy OLD_UNOWN aliases")

    unown_migrations = []
    for entry in dynamic_unown:
        offset = entry["offset_after_num_species"]
        unown_migrations.append({
            "symbol": entry["symbol"],
            "current_internal_id": current_egg + offset,
            "candidate_internal_id": proposed_num_species + offset,
            "candidate_status": "migration_target_only_not_runtime",
        })

    if form_policy.get("schema_version") != 1:
        raise RuntimeError("Unsupported Gen 8 form policy schema version")
    policies = form_policy.get("policies", [])
    required_policies = {"canonical", "cosmetic", "persistent_separate", "temporary_battle"}
    policy_values = {item.get("value") for item in policies}
    if policy_values != required_policies:
        raise RuntimeError(f"Form policy categories incomplete: {policy_values}")
    if form_policy.get("canonical_national_dex", {}).get("count") != CANONICAL_COUNT:
        raise RuntimeError("Form policy must describe exactly 898 canonical National Dex rows")
    if form_policy.get("canonical_national_dex", {}).get("alternate_forms_receive_species_internal_ids") is not False:
        raise RuntimeError("Alternate forms must not receive species IDs")
    if form_policy.get("form_identity", {}).get("missing_or_ambiguous_classification_blocks_runtime_import") is not True:
        raise RuntimeError("Unclassified forms must remain blocked from runtime import")

    # The 25 OLD_UNOWN IDs belong to the historic namespace and remain unchanged.
    legacy_unown_mapping = []
    for item in old_unown:
        legacy_unown_mapping.append({
            **item,
            "candidate_internal_id": item["current_internal_id"],
            "candidate_status": "legacy_alias_preserved",
        })

    return {
        "schema_version": 1,
        "status": "candidate_scheme_only_not_runtime",
        "runtime_activation_allowed": False,
        "production_ids_modified": False,
        "species_header_modified": False,
        "save_migration_implemented": False,
        "scope": {
            "canonical_national_dex_first": 1,
            "canonical_national_dex_last": CANONICAL_COUNT,
            "canonical_species_count": CANONICAL_COUNT,
        },
        "counts": {
            "existing_canonical_species": EXISTING_CANONICAL_COUNT,
            "new_canonical_species": NEW_CANONICAL_COUNT,
            "legacy_old_unown_aliases": LEGACY_OLD_UNOWN_COUNT,
            "dynamic_unown_auxiliary_values": DYNAMIC_UNOWN_COUNT,
        },
        "allocation_policy": {
            "existing_species": "preserve the exact current Emerald internal ID",
            "new_species": "assign consecutive candidate IDs in ascending National Dex order",
            "new_species_candidate_first": current_egg,
            "new_species_candidate_last": current_egg + NEW_CANONICAL_COUNT - 1,
            "new_species_candidate_count": NEW_CANONICAL_COUNT,
            "candidate_ids_are_not_runtime_ids": True,
        },
        "current_namespace": {
            "species_none": current_none,
            "last_existing_canonical_species": current_chimecho,
            "egg_sentinel": current_egg,
            "num_species_definition": "SPECIES_EGG",
            "dynamic_unown_first": current_dynamic_first,
            "dynamic_unown_last": current_dynamic_last,
            "legacy_old_unown_first": 252,
            "legacy_old_unown_last": 276,
        },
        "candidate_namespace": {
            "new_species_first": current_egg,
            "new_species_last": current_egg + NEW_CANONICAL_COUNT - 1,
            "egg_sentinel": proposed_egg,
            "num_species": proposed_num_species,
            "dynamic_unown_first": proposed_dynamic_first,
            "dynamic_unown_last": proposed_dynamic_last,
            "legacy_old_unown_first": 252,
            "legacy_old_unown_last": 276,
        },
        "sentinel_migration": {
            "required_before_activation": True,
            "egg": {
                "symbol": "SPECIES_EGG",
                "current_value": current_egg,
                "candidate_value": proposed_egg,
            },
            "dynamic_unown": unown_migrations,
            "legacy_old_unown": legacy_unown_mapping,
            "preserve_species_none": True,
            "preserve_all_386_existing_canonical_ids": True,
            "raw_boxpokemon_byte_rewrite_allowed": False,
            "required_storage_audit": [
                "SaveBlock1 player party",
                "PokemonStorage PC boxes and current-box metadata",
                "Daycare BoxPokemon records",
                "Mail species fields",
                "ContestWinner species fields",
                "outbreak species fields",
                "link, battle, TV, event and other persisted species fields",
                "rotating save slots, checksums and interrupted-write recovery",
            ],
        },
        "form_policy": {
            "policy_file": "data/pokemon/gen8_form_policy.json",
            "form_key_domain": "separate_from_species_internal_ids",
            "alternate_forms_create_national_dex_entries": False,
            "alternate_forms_create_species_internal_ids": False,
            "allowed_policies": sorted(required_policies),
            "unclassified_forms_runtime_allowed": False,
        },
        "species": proposed_species,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    rows = json.loads(read_text(MAPPING))
    form_policy = json.loads(read_text(FORM_POLICY))
    proposal = build_proposal(
        rows,
        read_text(SPECIES_HEADER),
        read_text(POKEMON_HEADER),
        read_text(POKEDEX_HEADER),
        form_policy,
    )
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(proposal, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("PASS: 898 canonical records mapped; 386 existing internal IDs preserved.")
    print("PASS: 512 candidate IDs are 412-923; Egg and dynamic Unown sentinels are shifted only in the proposal.")
    print("PASS: 25 OLD_UNOWN aliases remain 252-276; alternate forms use a separate form_key domain.")
    print("BLOCKED: proposal is not runtime-ready; no production IDs or saves were changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
