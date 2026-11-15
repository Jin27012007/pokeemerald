#!/usr/bin/env python3
"""Audit whether Emerald's internal species namespace can safely be expanded.

The report is read-only. It intentionally does not propose or assign IDs.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAPPING = ROOT / "reports/gen8-conversion/species_id_mapping.json"
SPECIES_HEADER = ROOT / "include/constants/species.h"
POKEDEX_HEADER = ROOT / "include/constants/pokedex.h"
DEFAULT_OUTPUT = ROOT / "reports/gen8-conversion/species_namespace_readiness.json"

EXPECTED_CANONICAL = 898
EXPECTED_EXISTING = 386
EXPECTED_UNALLOCATED = 512


def read_text(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"Required input is missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def numeric_species_macros(source: str) -> dict[str, int]:
    return {
        name: int(value)
        for name, value in re.findall(
            r"^#define\s+SPECIES_([A-Z0-9_]+)\s+(\d+)\s*$", source, re.M
        )
    }


def required_macro(source: str, name: str) -> int:
    match = re.search(rf"^#define\s+{re.escape(name)}\s+(\d+)\s*$", source, re.M)
    if not match:
        raise RuntimeError(f"Could not resolve #define {name}")
    return int(match.group(1))


def audit(rows: list[dict], species_header: str, pokedex_header: str) -> dict:
    if len(rows) != EXPECTED_CANONICAL:
        raise RuntimeError(f"Expected {EXPECTED_CANONICAL} National Dex rows, got {len(rows)}")
    if [int(row["national_dex"]) for row in rows] != list(range(1, EXPECTED_CANONICAL + 1)):
        raise RuntimeError("National Dex mapping is not a continuous 1-898 sequence")

    existing = [row for row in rows if row.get("emerald_internal_id") is not None]
    unallocated = [row for row in rows if row.get("emerald_internal_id") is None]
    if len(existing) != EXPECTED_EXISTING or len(unallocated) != EXPECTED_UNALLOCATED:
        raise RuntimeError(
            f"Unexpected mapping split: existing={len(existing)}, unallocated={len(unallocated)}"
        )

    species_ids = numeric_species_macros(species_header)
    current_egg = required_macro(species_header, "SPECIES_EGG")
    current_chimecho = required_macro(species_header, "SPECIES_CHIMECHO")
    if current_chimecho != 411 or current_egg != 412:
        raise RuntimeError(
            f"Unexpected production sentinel layout: Chimecho={current_chimecho}, Egg={current_egg}"
        )
    if not re.search(r"^#define\s+NUM_SPECIES\s+SPECIES_EGG\s*$", species_header, re.M):
        raise RuntimeError("Production NUM_SPECIES is no longer tied to SPECIES_EGG")
    if not re.search(r"^#define\s+SPECIES_UNOWN_B\s+\(NUM_SPECIES\s*\+\s*1\)\s*$", species_header, re.M):
        raise RuntimeError("Unown auxiliary IDs no longer derive from NUM_SPECIES + 1")
    if not re.search(r"^#define\s+SPECIES_UNOWN_QMARK\s+\(SPECIES_UNOWN_B\s*\+\s*26\)\s*$", species_header, re.M):
        raise RuntimeError("Unexpected Unown auxiliary range; expected 27 calculated values")
    if "#define NATIONAL_DEX_COUNT  NATIONAL_DEX_CALYREX" not in pokedex_header:
        raise RuntimeError("National Dex header does not declare Calyrex as the 898th canonical entry")

    preserved = []
    seen_ids = set()
    for row in existing:
        symbol = row.get("normalized_symbol")
        expected_id = int(row["emerald_internal_id"])
        if symbol not in species_ids:
            raise RuntimeError(f"Existing species symbol is missing from species.h: {symbol}")
        if species_ids[symbol] != expected_id:
            raise RuntimeError(
                f"Species ID mismatch for {symbol}: map={expected_id}, header={species_ids[symbol]}"
            )
        if expected_id in seen_ids:
            raise RuntimeError(f"Duplicate existing internal ID {expected_id}")
        if expected_id >= current_egg:
            raise RuntimeError(f"Existing species {symbol} overlaps Egg sentinel {current_egg}")
        seen_ids.add(expected_id)
        preserved.append({
            "national_dex": int(row["national_dex"]),
            "species_symbol": symbol,
            "internal_id": expected_id,
        })

    unallocated_rows = [
        {
            "national_dex": int(row["national_dex"]),
            "species_symbol": row.get("normalized_symbol"),
            "status": "no_production_internal_id",
        }
        for row in unallocated
    ]

    return {
        "schema_version": 1,
        "status": "blocked_before_internal_id_expansion",
        "read_only_audit": True,
        "production_files_modified": False,
        "internal_ids_proposed_or_assigned": False,
        "num_species_change_allowed": False,
        "scope": "Canonical National Dex 1-898 (Generations 1-8)",
        "coverage": {
            "canonical_national_dex_rows": EXPECTED_CANONICAL,
            "existing_emerald_internal_ids": EXPECTED_EXISTING,
            "species_without_production_internal_ids": EXPECTED_UNALLOCATED,
            "existing_ids_preserved_and_verified": len(preserved),
        },
        "current_production_namespace": {
            "last_existing_ordinary_species": "SPECIES_CHIMECHO",
            "last_existing_ordinary_species_id": current_chimecho,
            "egg_sentinel": "SPECIES_EGG",
            "egg_sentinel_id": current_egg,
            "num_species_definition": "SPECIES_EGG",
            "unown_auxiliary_ids": 27,
            "unown_auxiliary_first_expression": "NUM_SPECIES + 1",
            "unown_auxiliary_last_expression": "NUM_SPECIES + 26",
        },
        "confirmed_promotion_blockers": [
            {
                "area": "species index consumers",
                "detail": "Static inventory records 1,115 references, including 249 high-risk and 453 unclassified findings; all remaining consumers must be reviewed before ID allocation.",
            },
            {
                "area": "moves and contests",
                "detail": "322 distinct canonical Gen 8 learnset moves still lack Emerald battle/Contest records.",
            },
            {
                "area": "abilities",
                "detail": "172 ability identifiers used by canonical species have no Emerald constants/implementations.",
            },
            {
                "area": "held items",
                "detail": "85 held-item identifiers lack Emerald constants; 30 also lack target item-data records.",
            },
            {
                "area": "types",
                "detail": "Fairy and Stellar are absent from Emerald's type definitions and battle/contest compatibility layer.",
            },
            {
                "area": "evolutions",
                "detail": "Two canonical evolution methods still require target handlers and semantic tests.",
            },
            {
                "area": "graphics and audio",
                "detail": "512 new canonical species still lack target cry entries and 512 lack complete Emerald graphics payloads.",
            },
            {
                "area": "save migration",
                "detail": "The versioned Pokédex extension still needs real save-sector round-trip, interrupted-write, recovery, old-save compatibility and sector-boundary tests.",
            },
        ],
        "preserved_species": preserved,
        "unallocated_species": unallocated_rows,
        "next_gate": "Resolve promotion blockers and complete runtime/save tests; only then make a separate, reviewable species-ID and NUM_SPECIES migration.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    args = parser.parse_args()

    rows = json.loads(read_text(MAPPING))
    report = audit(rows, read_text(SPECIES_HEADER), read_text(POKEDEX_HEADER))
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        "PASS: National Dex 1-898 audited; 386 current internal IDs verified; "
        "512 species remain without production IDs."
    )
    print(
        "BLOCKED: species ID allocation and NUM_SPECIES expansion remain disabled "
        "until runtime and save promotion gates pass."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
