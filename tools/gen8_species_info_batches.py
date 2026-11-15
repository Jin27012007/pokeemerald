#!/usr/bin/env python3
"""Build the first reviewable, non-runtime Gen 4 SpeciesInfo import batch."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports/gen8-conversion"
DATA = ROOT / "data/pokemon"
CANONICAL_PATH = REPORTS / "species_info_by_national_dex.json"
COMPACT_PATH = DATA / "gen8_species_info_compact.json"
ENUM_AUDIT_PATH = REPORTS / "species_info_compact.json"
VENDOR_README = ROOT / "tools/vendor/pokeemerald-expansion/README.md"
OUTPUT = DATA / "gen8_species_info_batches/gen4_species_info.json"

BATCH = {
    "batch_id": "gen4_species_info",
    "species_introduction_generation": 4,
    "national_dex_start": 387,
    "national_dex_end": 493,
    "expected_species_count": 107,
    "source_generation_range": [1, 8],
}

REQUIRED_SOURCE_FIELDS = {
    "baseHP", "baseAttack", "baseDefense", "baseSpeed", "baseSpAttack",
    "baseSpDefense", "catchRate", "expYield", "genderRatio", "eggCycles",
    "friendship", "growthRate", "types", "eggGroups", "abilities",
    "bodyColor", "natDexNum",
}
REQUIRED_STATS = (
    "baseHP", "baseAttack", "baseDefense", "baseSpeed",
    "baseSpAttack", "baseSpDefense", "catchRate", "expYield",
)


def load_json(path: Path):
    if not path.is_file():
        raise RuntimeError(f"Missing generated input: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_source_snapshot() -> dict:
    if not VENDOR_README.is_file():
        raise RuntimeError("Pinned Expansion vendor README is missing")
    text = VENDOR_README.read_text(encoding="utf-8")
    repo = re.search(r"^Source repository:\s*(https://github.com/\S+)\s*$", text, re.M)
    commit = re.search(r"^Pinned upstream commit:\s*([0-9a-f]{40})\s*$", text, re.M)
    if not repo or not commit:
        raise RuntimeError("Could not resolve pinned Expansion repository and commit")
    return {"repository": repo.group(1), "commit": commit.group(1)}


def _index_unique(rows: list[dict], key: str, label: str) -> dict:
    result = {}
    for row in rows:
        value = row.get(key)
        if value in result:
            raise RuntimeError(f"Duplicate {label} key: {value!r}")
        result[value] = row
    return result


def build_batch(
    canonical_rows: list[dict],
    compact_rows: list[dict],
    source_enum_domains: dict,
    source_snapshot: dict,
    batch: dict = BATCH,
) -> dict:
    if len(canonical_rows) != 898:
        raise RuntimeError(f"Expected 898 canonical metadata rows, got {len(canonical_rows)}")
    canonical_by_dex = _index_unique(canonical_rows, "national_dex", "National Dex")
    if set(canonical_by_dex) != set(range(1, 899)):
        raise RuntimeError("Canonical metadata must cover National Dex 1-898 exactly")
    compact_by_symbol = _index_unique(compact_rows, "species_symbol", "source species")
    for domain in ("types", "egg_groups", "growth_rates", "abilities", "items"):
        if not isinstance(source_enum_domains.get(domain), dict) or not source_enum_domains[domain]:
            raise RuntimeError(f"Missing pinned source enum domain: {domain}")

    selected = []
    for dex in range(batch["national_dex_start"], batch["national_dex_end"] + 1):
        meta = canonical_by_dex[dex]
        if meta.get("record_provenance") != "expansion_source_initializer":
            raise RuntimeError(f"Dex {dex}: expected an Expansion source initializer")
        source_generation = meta.get("source_generation")
        if not isinstance(source_generation, int) or source_generation not in range(
            batch["source_generation_range"][0], batch["source_generation_range"][1] + 1
        ):
            raise RuntimeError(f"Dex {dex}: invalid source file generation {source_generation!r}")
        if meta.get("source_national_dex_matches_selected") is not True:
            raise RuntimeError(f"Dex {dex}: source National Dex identity is not verified")
        if meta.get("source_complete") is not True or meta.get("source_fields_resolved") is not True:
            raise RuntimeError(f"Dex {dex}: source SpeciesInfo fields are incomplete or unresolved")
        if meta.get("source_missing_fields") or meta.get("source_unresolved_fields"):
            raise RuntimeError(f"Dex {dex}: missing/unresolved source fields remain")
        if not REQUIRED_SOURCE_FIELDS.issubset(set(meta.get("source_fields_present", []))):
            missing = sorted(REQUIRED_SOURCE_FIELDS - set(meta.get("source_fields_present", [])))
            raise RuntimeError(f"Dex {dex}: required source fields absent: {missing}")

        symbol = meta.get("source_record_symbol")
        source = compact_by_symbol.get(symbol)
        if source is None:
            raise RuntimeError(f"Dex {dex}: selected source initializer {symbol!r} was not parsed")
        if source.get("generation") != source_generation:
            raise RuntimeError(f"Dex {dex}: parsed source generation disagrees with canonical metadata")
        if source.get("national_dex_symbol") != meta.get("source_national_dex_symbol"):
            raise RuntimeError(f"Dex {dex}: parsed initializer National Dex symbol mismatch")
        if source.get("source_complete") is not True or source.get("source_fields_resolved") is not True:
            raise RuntimeError(f"Dex {dex}: parsed source record is not fully resolved")
        if source.get("source_missing_fields") or source.get("source_unresolved_fields"):
            raise RuntimeError(f"Dex {dex}: parsed source still has missing/unresolved fields")

        statistics = source.get("statistics")
        if not isinstance(statistics, dict):
            raise RuntimeError(f"Dex {dex}: missing numeric statistics")
        for field in REQUIRED_STATS:
            value = statistics.get(field)
            upper = 65535 if field == "expYield" else 255
            if not isinstance(value, int) or not 0 <= value <= upper:
                raise RuntimeError(f"Dex {dex}: invalid or unresolved {field}={value!r}")
        # The upstream parser stores omitted EV yields as zero for comparison.
        # Do not export those synthetic zeros as source data: include an EV
        # field only when the initializer actually supplied that field.
        source_fields_expanded = source.get("source_expanded_fields", {})
        source_statistics = {field: statistics[field] for field in REQUIRED_STATS}
        ev_fields = (
            "evYield_HP", "evYield_Attack", "evYield_Defense", "evYield_Speed",
            "evYield_SpAttack", "evYield_SpDefense",
        )
        for field in ev_fields:
            if field in source_fields_expanded:
                value = statistics.get(field)
                if not isinstance(value, int) or value < 0:
                    raise RuntimeError(f"Dex {dex}: invalid or unresolved {field}={value!r}")
                source_statistics[field] = value
        for field in ("gender_ratio", "friendship", "growth_rate", "body_color"):
            value = source.get(field)
            if not isinstance(value, int) or value < 0:
                raise RuntimeError(f"Dex {dex}: invalid or unresolved {field}={value!r}")
        for field in ("types", "egg_groups", "abilities"):
            value = source.get(field)
            if not isinstance(value, list) or len(value) != 2 or any(
                not isinstance(item, int) or item < 0 for item in value
            ):
                raise RuntimeError(f"Dex {dex}: invalid source enum pair {field}={value!r}")
        if not isinstance(source.get("source_expanded_fields"), dict):
            raise RuntimeError(f"Dex {dex}: expanded source fields are missing")
        if not isinstance(source.get("source_initializer_raw"), str) or not isinstance(
            source.get("source_initializer_expanded"), str
        ):
            raise RuntimeError(f"Dex {dex}: source initializer provenance is missing")

        selected.append({
            "national_dex": dex,
            "national_symbol": meta["national_symbol"],
            "source_species_symbol": symbol,
            "source_generation": source["generation"],
            "source_file": f"src/data/pokemon/species_info/gen_{source['generation']}_families.h",
            "source_national_dex_symbol": source["national_dex_symbol"],
            "source_fields_present": meta["source_fields_present"],
            "statistics": source_statistics,
            "statistics_source_fields": sorted(source_statistics),
            "gender_ratio_source_value": source["gender_ratio"],
            "friendship_source_value": source["friendship"],
            "growth_rate_source_id": source["growth_rate"],
            "types_source_ids": source["types"],
            "egg_groups_source_ids": source["egg_groups"],
            "abilities_source_ids": source["abilities"],
            "hidden_ability_source_id": source.get("hidden_ability"),
            "item_common_source_id": source.get("item_common"),
            "item_rare_source_id": source.get("item_rare"),
            "body_color_source_value": source["body_color"],
            "source_fields_raw": source.get("source_raw", {}),
            "source_fields_expanded": source["source_expanded_fields"],
            "source_initializer_raw": source["source_initializer_raw"],
            "source_initializer_expanded": source["source_initializer_expanded"],
            "emerald_target_mapping_compatible": meta.get("target_mapping_compatible", False),
            "runtime_gap_codes": meta.get("runtime_gaps", []),
            "compact_parse_status": source.get("status"),
        })

    if len(selected) != batch["expected_species_count"]:
        raise RuntimeError(
            f"Batch {batch['batch_id']} expected {batch['expected_species_count']} rows, "
            f"got {len(selected)}"
        )
    return {
        "schema_version": 1,
        "batch_id": batch["batch_id"],
        "status": "staging_only_not_runtime",
        "runtime_activation_allowed": False,
        "identity_domain": "national_dex",
        "species_introduction_generation": batch["species_introduction_generation"],
        "national_dex_range": [batch["national_dex_start"], batch["national_dex_end"]],
        "expected_species_count": batch["expected_species_count"],
        "species_count": len(selected),
        "source_snapshot": source_snapshot,
        "source_files": sorted({
            f"src/data/pokemon/species_info/gen_{row['source_generation']}_families.h"
            for row in selected
        }),
        "extractor": {
            "script": "tools/gen8_convert_emerald.py",
            "batch_builder": "tools/gen8_species_info_batches.py",
            "target_generation_policy": 8,
        },
        "source_enum_domains": source_enum_domains,
        "species": selected,
        "invariants": [
            "No Emerald production species ID is allocated in this batch.",
            "National Dex numbers are identity keys, not internal table indices.",
            "All numeric enum IDs in this file belong to the pinned Expansion source.",
            "Raw and expanded initializers are preserved separately for audit.",
            "Emerald runtime compatibility and runtime gaps remain explicit and separate.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    try:
        canonical = load_json(CANONICAL_PATH)
        compact = load_json(COMPACT_PATH)
        audit = load_json(ENUM_AUDIT_PATH)
        result = build_batch(
            canonical,
            compact,
            audit.get("source_enum_domains", {}),
            load_source_snapshot(),
        )
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({
            "batch_id": result["batch_id"],
            "species_introduction_generation": result["species_introduction_generation"],
            "national_dex_range": result["national_dex_range"],
            "species_count": result["species_count"],
            "status": result["status"],
            "output": str(args.output.relative_to(ROOT)) if args.output.is_relative_to(ROOT) else str(args.output),
        }, indent=2))
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
        print(f"GEN 4 SPECIES INFO BATCH FAILED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
