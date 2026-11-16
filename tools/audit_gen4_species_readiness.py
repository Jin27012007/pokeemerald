#!/usr/bin/env python3
"""Generation 4-only readiness audit for a safe Emerald runtime integration.

This report deliberately does not allocate production species IDs or edit any
runtime species table. National Dex numbers are identity keys, never Emerald
array indices.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/pokemon"
REPORTS = ROOT / "reports/gen8-conversion"
OUTPUT = REPORTS / "gen4_runtime_readiness.json"

DEX_FIRST = 387
DEX_LAST = 493
EXPECTED_COUNT = 107
GENERATION_4_NEW_HELD_ITEMS = {
    "BLACK_SLUDGE", "ELECTIRIZER", "HONEY", "LAGGING_TAIL",
    "MAGMARIZER", "METRONOME", "OVAL_STONE", "WIDE_LENS",
}
REQUIRED_SOURCE_FIELDS = {
    "baseHP", "baseAttack", "baseDefense", "baseSpeed", "baseSpAttack",
    "baseSpDefense", "catchRate", "expYield", "genderRatio", "eggCycles",
    "friendship", "growthRate", "types", "eggGroups", "abilities",
    "bodyColor", "natDexNum",
}


def read_json(path: Path):
    if not path.is_file():
        raise RuntimeError(f"Required generated input is missing: {path.relative_to(ROOT)}")
    return json.loads(path.read_text(encoding="utf-8"))


def index_by_dex(rows: list[dict], label: str) -> dict[int, dict]:
    result = {}
    for row in rows:
        dex = int(row["national_dex"])
        if dex in result:
            raise RuntimeError(f"Duplicate National Dex identity in {label}: {dex}")
        result[dex] = row
    return result


def species_symbol(value: str | None) -> str | None:
    if not value:
        return None
    return value.removeprefix("SPECIES_")


def audit(
    batch: dict,
    runtime_mapping: dict,
    learnsets: list[dict],
    evolutions: list[dict],
    cries: list[dict],
    graphics: list[dict],
    pending: dict,
) -> dict:
    if batch.get("batch_id") != "gen4_species_info":
        raise RuntimeError("Expected the isolated Gen 4 SpeciesInfo batch")
    if batch.get("national_dex_range") != [DEX_FIRST, DEX_LAST]:
        raise RuntimeError("Gen 4 batch has an unexpected National Dex range")
    if batch.get("species_count") != EXPECTED_COUNT:
        raise RuntimeError("Gen 4 SpeciesInfo batch must contain exactly 107 species")

    batch_rows = index_by_dex(batch["species"], "Gen 4 SpeciesInfo batch")
    mapping_rows_all = runtime_mapping.get("species", [])
    mapping_rows = index_by_dex(
        [row for row in mapping_rows_all if DEX_FIRST <= int(row["national_dex"]) <= DEX_LAST],
        "runtime mapping",
    )
    learn_rows = index_by_dex(
        [row for row in learnsets if DEX_FIRST <= int(row["national_dex"]) <= DEX_LAST],
        "level-up learnsets",
    )
    evolution_rows = index_by_dex(evolutions, "evolution catalog")
    cry_rows = index_by_dex(
        [row for row in cries if DEX_FIRST <= int(row["national_dex"]) <= DEX_LAST],
        "cry catalog",
    )
    graphics_rows = index_by_dex(
        [row for row in graphics if DEX_FIRST <= int(row["national_dex"]) <= DEX_LAST],
        "graphics catalog",
    )

    expected_dex = set(range(DEX_FIRST, DEX_LAST + 1))
    for label, rows in (
        ("SpeciesInfo", batch_rows),
        ("runtime mapping", mapping_rows),
        ("level-up learnsets", learn_rows),
        ("cry catalog", cry_rows),
        ("graphics catalog", graphics_rows),
    ):
        if set(rows) != expected_dex:
            raise RuntimeError(f"{label} does not cover National Dex 387-493 exactly")

    missing_source_fields = {}
    for dex, row in batch_rows.items():
        missing = sorted(REQUIRED_SOURCE_FIELDS - set(row.get("source_fields_present", [])))
        if missing:
            missing_source_fields[row["national_symbol"]] = missing

    mapping_by_dex = mapping_rows
    unallocated = [
        row["national_symbol"]
        for row in mapping_by_dex.values()
        if row.get("production_emerald_species_id") is None
    ]
    if len(unallocated) != EXPECTED_COUNT:
        raise RuntimeError("The Gen 4 audit expected all 107 new species to remain unallocated")

    missing_battle_moves = set(pending.get("missing_target_battle_move_records", []))
    missing_contest_moves = set(pending.get("missing_target_contest_move_records", []))
    used_moves = Counter(
        move["move"]
        for row in learn_rows.values()
        for move in row.get("moves", [])
    )
    missing_battle_used = sorted(set(used_moves) & missing_battle_moves)
    missing_contest_used = sorted(set(used_moves) & missing_contest_moves)

    missing_items_by_species = {}
    missing_item_species = defaultdict(list)
    for row in mapping_by_dex.values():
        missing = []
        for slot, item in row.get("held_items", {}).items():
            if item.get("mapping_status") not in ("mapped_none_sentinel", "mapped_target_item"):
                symbol = item.get("symbol") or f"source_item_id_{item.get('source_id')}"
                missing.append({"slot": slot, "item": symbol})
                missing_item_species[symbol].append(row["national_symbol"])
        if missing:
            missing_items_by_species[row["national_symbol"]] = missing

    missing_graphics = [
        {
            "national_dex": dex,
            "species": row["species_symbol"],
            "missing_assets": [
                asset for asset, present in row.get("target_asset_presence", {}).items()
                if not present
            ],
        }
        for dex, row in graphics_rows.items()
        if not row.get("target_graphics_assets_complete", False)
    ]
    missing_cries = [
        {"national_dex": dex, "species": row["species_symbol"]}
        for dex, row in cry_rows.items()
        if not row.get("emerald_cry_table_match", False)
    ]

    gen4_symbols = {row["national_symbol"] for row in batch_rows.values()}
    evolution_edges = []
    evolution_conditions = Counter()
    evolution_methods = Counter()
    for source in evolutions:
        source_dex = int(source["national_dex"])
        for edge in source.get("evolutions", []):
            target = species_symbol(edge.get("target_species_symbol"))
            source_is_gen4 = DEX_FIRST <= source_dex <= DEX_LAST
            target_is_gen4 = target in gen4_symbols
            if not (source_is_gen4 or target_is_gen4):
                continue
            condition = edge.get("condition_expression") or ""
            conditions = sorted(set(re.findall(r"\bIF_[A-Z0-9_]+\b", condition)))
            evolution_methods[edge.get("method_symbol", "UNKNOWN")] += 1
            evolution_conditions.update(conditions)
            evolution_edges.append({
                "source_national_dex": source_dex,
                "source_species": source.get("species_symbol"),
                "method": edge.get("method_symbol"),
                "parameter": edge.get("parameter_expression"),
                "target_species": target,
                "conditions": conditions,
            })

    ability_mapping_incomplete = [
        row["national_symbol"]
        for row in batch_rows.values()
        if not row.get("abilities_numeric_ids_complete", False)
    ]
    ability_semantics_pending = Counter(
        pending_item
        for row in mapping_by_dex.values()
        for pending_item in row.get("runtime_semantics_pending", [])
        if pending_item.startswith("ability_behavior_not_audited:")
    )
    item_semantics_pending = Counter(
        pending_item
        for row in mapping_by_dex.values()
        for pending_item in row.get("runtime_semantics_pending", [])
        if pending_item.startswith("held_item_behavior_not_audited:")
        and pending_item.split(":", 1)[1] in GENERATION_4_NEW_HELD_ITEMS
    )
    missing_runtime_blockers = Counter(
        blocker
        for row in mapping_by_dex.values()
        for blocker in row.get("runtime_blockers", [])
    )

    counts = {
        "national_dex_species": EXPECTED_COUNT,
        "species_info_source_records": len(batch_rows),
        "species_info_records_missing_required_fields": len(missing_source_fields),
        "species_with_incomplete_ability_source_ids": len(ability_mapping_incomplete),
        "species_without_production_internal_id": len(unallocated),
        "level_up_learnset_records": len(learn_rows),
        "level_up_move_entries": sum(used_moves.values()),
        "distinct_level_up_moves": len(used_moves),
        "distinct_level_up_moves_missing_battle_records": len(missing_battle_used),
        "distinct_level_up_moves_missing_contest_records": len(missing_contest_used),
        "species_with_unmapped_held_items": len(missing_items_by_species),
        "distinct_unmapped_held_items": len(missing_item_species),
        "evolution_edges_touching_generation_4": len(evolution_edges),
        "distinct_evolution_conditions": len(evolution_conditions),
        "species_missing_target_graphics": len(missing_graphics),
        "species_missing_target_cry_entries": len(missing_cries),
        "distinct_ability_behaviors_pending_audit": len(ability_semantics_pending),
        "distinct_held_item_behaviors_pending_audit": len(item_semantics_pending),
        "runtime_blocker_entries": sum(missing_runtime_blockers.values()),
    }

    source_data_complete = (
        counts["species_info_source_records"] == EXPECTED_COUNT
        and counts["species_info_records_missing_required_fields"] == 0
    )
    readiness = {
        "107_species_source_records_present": counts["species_info_source_records"] == EXPECTED_COUNT,
        "required_species_statistics_and_fields_complete": source_data_complete,
        "all_species_ability_source_ids_resolved": not ability_mapping_incomplete,
        "production_species_ids_allocated": len(unallocated) == 0,
        "all_level_up_moves_have_battle_records": not missing_battle_used,
        "all_held_items_have_target_data": not missing_item_species,
        "all_held_item_behaviors_audited": not item_semantics_pending,
        "all_evolution_conditions_runtime_implemented": False,
        "all_target_graphics_assets_present": not missing_graphics,
        "all_target_cry_entries_present": not missing_cries,
        "runtime_activation_allowed": False,
    }

    blockers = [
        {
            "area": "Species IDs, array bounds and save compatibility",
            "count": len(unallocated),
            "detail": "All 107 Generation 4 species still lack production Emerald IDs. The global species-index consumer and save-migration gates must pass before changing NUM_SPECIES.",
        },
        {
            "area": "Battle moves",
            "count": len(missing_battle_used),
            "detail": "Distinct moves referenced by Generation 4 level-up learnsets still lack Emerald battle move records.",
            "symbols": missing_battle_used,
        },
        {
            "area": "Held items",
            "count": len(missing_item_species),
            "detail": "Held-item constants and target item-data records are missing for these items.",
            "symbols": sorted(missing_item_species),
            "affected_species": dict(sorted(missing_item_species.items())),
        },
        {
            "area": "Held-item runtime behavior",
            "count": len(item_semantics_pending),
            "detail": "Item constants and records exist, but effects without a verified Emerald runtime handler remain blocked.",
            "symbols": sorted(item_semantics_pending),
        },
        {
            "area": "Evolution conditions",
            "count": len(evolution_conditions),
            "detail": "Generation 4 evolution edges require explicit review and runtime handlers for their conditional requirements.",
            "symbols": sorted(evolution_conditions),
        },
        {
            "area": "Graphics",
            "count": len(missing_graphics),
            "detail": "Complete Emerald-format front/back sprites, animations, icons, footprints and palettes are still absent.",
        },
        {
            "area": "Cries",
            "count": len(missing_cries),
            "detail": "Generation 4 cry identifiers are in the source catalog, but their Emerald audio table/assets are not integrated.",
        },
        {
            "area": "Abilities",
            "count": len(ability_semantics_pending),
            "detail": "The source-to-target mapping exists, but battle behavior has not been audited for every ability assigned to these species.",
            "symbols": sorted(ability_semantics_pending),
        },
    ]

    return {
        "schema_version": 1,
        "status": "generation_4_pre_runtime_audit",
        "scope": {
            "generation": 4,
            "national_dex_range": [DEX_FIRST, DEX_LAST],
            "identity_key": "national_dex",
            "species_count": EXPECTED_COUNT,
            "learnset_policy": "Generation 8 Expansion level-up learnsets",
            "source_repository": batch.get("source_snapshot", {}).get("repository"),
            "source_commit": batch.get("source_snapshot", {}).get("commit"),
        },
        "counts": counts,
        "readiness": readiness,
        "blockers": blockers,
        "species_with_missing_required_source_fields": missing_source_fields,
        "species_with_incomplete_ability_source_ids": ability_mapping_incomplete,
        "species_without_production_internal_id": unallocated,
        "species_with_unmapped_held_items": missing_items_by_species,
        "generation_4_unmapped_held_items": {
            item: sorted(species) for item, species in sorted(missing_item_species.items())
        },
        "generation_4_missing_battle_moves": missing_battle_used,
        "generation_4_missing_contest_moves": missing_contest_used,
        "generation_4_evolution_edges": evolution_edges,
        "generation_4_evolution_conditions": dict(sorted(evolution_conditions.items())),
        "generation_4_evolution_methods": dict(sorted(evolution_methods.items())),
        "species_missing_target_graphics": missing_graphics,
        "species_missing_target_cries": missing_cries,
        "ability_behaviors_pending_audit": dict(sorted(ability_semantics_pending.items())),
        "held_item_behaviors_pending_audit": dict(sorted(item_semantics_pending.items())),
        "invariants": [
            "No production species ID is allocated by this audit.",
            "National Dex numbers are never used as Emerald runtime array indices.",
            "This report is a pre-runtime gate, not evidence that Generation 4 Pokémon are playable.",
            "NUM_SPECIES and legacy save layout remain unchanged.",
        ],
    }


def load_inputs() -> dict:
    return {
        "batch": read_json(DATA / "gen8_species_info_batches/gen4_species_info.json"),
        "runtime_mapping": read_json(DATA / "gen8_species_info_runtime_mapping.json"),
        "learnsets": read_json(DATA / "gen8_species_level_up_learnsets.json"),
        "evolutions": read_json(DATA / "gen8_species_evolutions.json"),
        "cries": read_json(DATA / "gen8_species_cry_map.json"),
        "graphics": read_json(DATA / "gen8_species_graphics_references.json"),
        "pending": read_json(REPORTS / "pending_species_tables_audit.json"),
    }


def main() -> int:
    report = audit(**load_inputs())
    REPORTS.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT.relative_to(ROOT)), "counts": report["counts"], "readiness": report["readiness"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
