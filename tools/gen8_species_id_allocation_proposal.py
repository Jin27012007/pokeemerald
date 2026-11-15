#!/usr/bin/env python3
"""Generate a non-runtime proposal for allocating Gen 8 species IDs.

This deliberately does not edit species.h, NUM_SPECIES, save structures, or
any production table. It reserves candidate IDs for review only.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "reports/gen8-conversion/species_id_mapping.json"
SPECIES_HEADER = ROOT / "include/constants/species.h"
DEFAULT_OUTPUT = ROOT / "reports/gen8-conversion/species_id_allocation_proposal.json"
EXPECTED_CANONICAL = 898
EXPECTED_EXISTING = 386
EXPECTED_NEW = 512
UNOWN_AUXILIARY_COUNT = 27


def read_text(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"Required input is missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def read_macro_int(source: str, macro: str) -> int:
    match = re.search(rf"^#define\s+{re.escape(macro)}\s+(\d+)\s*$", source, re.M)
    if not match:
        raise RuntimeError(f"Could not resolve numeric macro {macro}")
    return int(match.group(1))


def build_proposal(rows: list[dict], species_header: str) -> dict:
    if len(rows) != EXPECTED_CANONICAL:
        raise RuntimeError(f"Expected {EXPECTED_CANONICAL} canonical rows, got {len(rows)}")

    dex_numbers = [int(row["national_dex"]) for row in rows]
    if dex_numbers != list(range(1, EXPECTED_CANONICAL + 1)):
        raise RuntimeError("Mapping must contain exactly National Dex 1-898 in order")

    existing = [row for row in rows if row.get("emerald_internal_id") is not None]
    new = [row for row in rows if row.get("emerald_internal_id") is None]
    if len(existing) != EXPECTED_EXISTING or len(new) != EXPECTED_NEW:
        raise RuntimeError(
            f"Unexpected mapping split: existing={len(existing)}, new={len(new)}"
        )

    existing_ids = [int(row["emerald_internal_id"]) for row in existing]
    if len(set(existing_ids)) != EXPECTED_EXISTING:
        raise RuntimeError("Existing Emerald internal IDs are not unique")

    current_egg_id = read_macro_int(species_header, "SPECIES_EGG")
    current_chimecho_id = read_macro_int(species_header, "SPECIES_CHIMECHO")
    if current_egg_id != current_chimecho_id + 1:
        raise RuntimeError(
            f"Expected Egg immediately after Chimecho; got Chimecho={current_chimecho_id}, Egg={current_egg_id}"
        )
    num_species = re.search(r"^#define\s+NUM_SPECIES\s+SPECIES_EGG\s*$", species_header, re.M)
    if not num_species:
        raise RuntimeError("NUM_SPECIES no longer points to SPECIES_EGG; review allocation logic")
    if "SPECIES_UNOWN_B (NUM_SPECIES + 1)" not in species_header:
        raise RuntimeError("Unown auxiliary IDs no longer derive from NUM_SPECIES + 1")

    if max(existing_ids) != current_chimecho_id:
        raise RuntimeError(
            f"Existing mapped IDs do not end at Chimecho: max={max(existing_ids)}, Chimecho={current_chimecho_id}"
        )
    if any(species_id >= current_egg_id for species_id in existing_ids):
        raise RuntimeError("An existing canonical species overlaps the current Egg sentinel")

    first_new_id = current_egg_id
    last_new_id = first_new_id + EXPECTED_NEW - 1
    proposed_egg_id = last_new_id + 1
    proposed_num_species = proposed_egg_id
    proposed_unown_first = proposed_num_species + 1
    proposed_unown_last = proposed_unown_first + UNOWN_AUXILIARY_COUNT - 1

    existing_by_dex = {
        int(row["national_dex"]): int(row["emerald_internal_id"])
        for row in existing
    }
    next_new_id = first_new_id
    proposal_rows = []
    for row in rows:
        dex = int(row["national_dex"])
        is_existing = row.get("emerald_internal_id") is not None
        if is_existing:
            proposed_id = int(row["emerald_internal_id"])
            kind = "preserve_existing_internal_id"
        else:
            proposed_id = next_new_id
            next_new_id += 1
            kind = "candidate_new_internal_id_not_runtime"
        proposal_rows.append({
            "national_dex": dex,
            "source_symbol": row.get("source_symbol"),
            "normalized_symbol": row.get("normalized_symbol"),
            "current_emerald_internal_id": row.get("emerald_internal_id"),
            "proposed_emerald_internal_id": proposed_id,
            "allocation": kind,
        })

    candidate_ids = [
        row["proposed_emerald_internal_id"]
        for row in proposal_rows
        if row["allocation"] == "candidate_new_internal_id_not_runtime"
    ]
    if candidate_ids != list(range(first_new_id, last_new_id + 1)):
        raise RuntimeError("New candidate IDs are not a continuous, deterministic range")
    if set(candidate_ids) & set(existing_ids):
        raise RuntimeError("Proposed IDs collide with existing canonical species IDs")
    if len(existing_by_dex) != EXPECTED_EXISTING:
        raise RuntimeError("Existing National Dex mapping contains duplicate identities")

    return {
        "schema_version": 1,
        "status": "proposal_only_not_runtime",
        "scope": "Canonical National Dex 1-898, Generations 1-8",
        "runtime_activation_allowed": False,
        "production_files_modified": False,
        "species_header_modified": False,
        "existing_internal_ids_preserved": True,
        "summary": {
            "canonical_species": EXPECTED_CANONICAL,
            "existing_emerald_species": EXPECTED_EXISTING,
            "new_species_needing_ids": EXPECTED_NEW,
        },
        "candidate_internal_namespace": {
            "first_new_species_id": first_new_id,
            "last_new_species_id": last_new_id,
            "new_species_id_count": EXPECTED_NEW,
            "allocation_order": "ascending National Dex number",
            "current_egg_sentinel_id": current_egg_id,
            "proposed_egg_sentinel_id": proposed_egg_id,
            "proposed_num_species": proposed_num_species,
            "proposed_unown_auxiliary_first": proposed_unown_first,
            "proposed_unown_auxiliary_last": proposed_unown_last,
            "proposed_unown_auxiliary_count": UNOWN_AUXILIARY_COUNT,
        },
        "promotion_blockers": [
            "Resolve all species-index consumers and the unclassified static-audit findings.",
            "Complete the real save-sector round-trip, interrupted-write and recovery tests.",
            "Implement and validate the missing Gen 8 move and Contest records.",
            "Resolve ability, held-item and Fairy/Stellar type compatibility.",
            "Implement evolution handlers, cry/audio and graphics payloads.",
            "Test party, PC, daycare, battle, trade/link, save/load, summary and Pokédex.",
        ],
        "species": proposal_rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    rows = json.loads(read_text(MAPPING))
    proposal = build_proposal(rows, read_text(SPECIES_HEADER))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(proposal, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        "PASS: proposed IDs for 512 new species; preserved all 386 existing IDs. "
        "No production species IDs or sentinels were changed."
    )
    print(
        "REVIEW ONLY: new IDs "
        f"{proposal['candidate_internal_namespace']['first_new_species_id']}-"
        f"{proposal['candidate_internal_namespace']['last_new_species_id']}; "
        f"future Egg={proposal['candidate_internal_namespace']['proposed_egg_sentinel_id']}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
