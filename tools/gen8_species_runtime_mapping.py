#!/usr/bin/env python3
"""Build explicit, staging-only Expansion-to-Emerald SpeciesInfo mappings."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/pokemon"
REPORTS = ROOT / "reports/gen8-conversion"
GENERATIONS = (4, 5, 6, 7, 8)
NUM_ABILITY_SLOTS = 3  # Must match include/pokemon.h.
BATCH_RANGES = {
    4: (387, 493, 107),
    5: (494, 649, 156),
    6: (650, 721, 72),
    7: (722, 809, 88),
    8: (810, 898, 89),
}
BASE_STATS = (
    "baseHP", "baseAttack", "baseDefense", "baseSpeed",
    "baseSpAttack", "baseSpDefense", "catchRate", "expYield",
)
EV_STATS = (
    "evYield_HP", "evYield_Attack", "evYield_Defense", "evYield_Speed",
    "evYield_SpAttack", "evYield_SpDefense",
)
BATCH_PATHS = [
    DATA / f"gen8_species_info_batches/gen{generation}_species_info.json"
    for generation in GENERATIONS
]
DEPENDENCY_PATHS = {
    "abilities": DATA / "gen8_ability_source_dependencies.json",
    "items": DATA / "gen8_item_source_dependencies.json",
    "types": DATA / "gen8_type_source_dependencies.json",
    "egg_groups": DATA / "gen8_egg_group_source_dependencies.json",
    "growth_rates": DATA / "gen8_growth_rate_source_dependencies.json",
}
OUTPUT_DATA = DATA / "gen8_species_info_runtime_mapping.json"
OUTPUT_AUDIT = REPORTS / "species_info_runtime_mapping_audit.json"


def load_json(path: Path):
    if not path.is_file():
        raise RuntimeError(f"Missing required input: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def unique_index(rows: list[dict], key: str, label: str) -> dict:
    result = {}
    for row in rows:
        value = row.get(key)
        if value in result:
            raise RuntimeError(f"Duplicate {label}: {value!r}")
        result[value] = row
    return result


def map_symbol(symbol, source_id, source_domain, dependencies,
               source_id_key, target_id_key, label):
    if symbol not in source_domain:
        raise RuntimeError(f"{label} symbol missing from Expansion enum catalog: {symbol}")
    if source_domain[symbol] != source_id:
        raise RuntimeError(
            f"{label} source-ID mismatch for {symbol}: "
            f"batch={source_id!r}, enum_catalog={source_domain[symbol]!r}"
        )
    dependency = dependencies.get(symbol)
    if dependency is None:
        return {
            "symbol": symbol, "source_id": source_id, "emerald_id": None,
            "target_symbol_present": False, "mapping_status": "missing_dependency",
        }
    if dependency.get(source_id_key) != source_id:
        raise RuntimeError(f"{label} dependency source-ID mismatch for {symbol}")
    target_id = dependency.get(target_id_key)
    return {
        "symbol": symbol,
        "source_id": source_id,
        "emerald_id": target_id,
        "target_symbol_present": target_id is not None,
        "mapping_status": "mapped" if target_id is not None else "missing_target_enum",
    }


def map_held_item(source_id, source_domain, dependencies_by_id):
    if source_id is None:
        return {
            "source_id": None, "symbol": None, "emerald_id": None,
            "target_constant_present": False, "target_data_record_present": False,
            "mapping_status": "unresolved_source_item_id",
        }
    source_id = int(source_id)
    if source_id == 0:
        if source_domain.get("NONE") != 0:
            raise RuntimeError("Expansion item enum does not define ITEM_NONE as ID 0")
        return {
            "source_id": 0, "symbol": "NONE", "emerald_id": 0,
            "target_constant_present": True, "target_data_record_present": True,
            "target_behavior_audited": True, "mapping_status": "mapped_none_sentinel",
        }
    dependency = dependencies_by_id.get(source_id)
    if dependency is None:
        return {
            "source_id": source_id, "symbol": None, "emerald_id": None,
            "target_constant_present": False, "target_data_record_present": False,
            "mapping_status": "missing_item_dependency",
        }
    symbol = dependency["item_symbol"]
    if source_domain.get(symbol) != source_id:
        raise RuntimeError(f"Held-item source-ID mismatch for {symbol}")
    target_id = dependency.get("emerald_item_id")
    target_data = bool(dependency.get("target_item_data_record_present"))
    if target_id is None:
        status = "missing_target_item_constant"
    elif not target_data:
        status = "missing_target_item_data_record"
    else:
        status = "mapped_target_item"
    return {
        "source_id": source_id,
        "symbol": symbol,
        "emerald_id": target_id,
        "target_constant_present": target_id is not None,
        "target_data_record_present": target_data,
        "target_behavior_audited": bool(dependency.get("target_item_behavior_audited")),
        "mapping_status": status,
    }


def build_runtime_mapping(batches: list[dict], dependencies: dict[str, list[dict]],
                          expected_species_count: int = 512,
                          strict_batch_contract: bool = True) -> tuple[dict, dict]:
    if strict_batch_contract and len(batches) != 5:
        raise RuntimeError(f"Expected five generation batches, got {len(batches)}")
    if not batches:
        raise RuntimeError("At least one SpeciesInfo batch is required")

    domains = batches[0].get("source_enum_domains")
    if not isinstance(domains, dict):
        raise RuntimeError("SpeciesInfo batches do not contain source enum catalogs")

    rows = []
    for batch in batches:
        generation = int(batch.get("species_introduction_generation", 0))
        if generation not in BATCH_RANGES:
            raise RuntimeError(f"Unexpected SpeciesInfo generation: {generation}")
        if batch.get("status") != "staging_only_not_runtime":
            raise RuntimeError(f"Gen {generation} batch is not staging-only")
        if batch.get("runtime_activation_allowed") is not False:
            raise RuntimeError(f"Gen {generation} batch allows runtime activation")
        if strict_batch_contract:
            start, end, count = BATCH_RANGES[generation]
        else:
            batch_rows = batch.get("species", [])
            if not batch_rows:
                raise RuntimeError(f"Gen {generation} test batch is empty")
            dex_values = [int(item["national_dex"]) for item in batch_rows]
            start, end, count = min(dex_values), max(dex_values), len(dex_values)
        if batch.get("national_dex_range") != [start, end] or batch.get("species_count") != count:
            raise RuntimeError(f"Gen {generation} batch range/count mismatch")
        if batch.get("source_enum_domains") != domains:
            raise RuntimeError("Expansion enum catalogs differ between generation batches")
        for source_row in batch.get("species", []):
            row = dict(source_row)
            row["_introduction_generation"] = generation
            rows.append(row)

    rows.sort(key=lambda row: int(row["national_dex"]))
    dexes = [int(row["national_dex"]) for row in rows]
    if len(rows) != expected_species_count or len(set(dexes)) != len(dexes):
        raise RuntimeError("SpeciesInfo batch coverage is incomplete or duplicated")
    if expected_species_count == 512 and dexes != list(range(387, 899)):
        raise RuntimeError("Gen 4–8 batches must cover National Dex 387–898 continuously")

    ability_deps = unique_index(dependencies["abilities"], "ability_symbol", "ability dependency")
    item_deps = dependencies["items"]
    type_deps = unique_index(dependencies["types"], "type_symbol", "type dependency")
    egg_deps = unique_index(dependencies["egg_groups"], "egg_group_symbol", "egg dependency")
    growth_deps = unique_index(dependencies["growth_rates"], "growth_rate_symbol", "growth dependency")
    item_by_source_id = {}
    for item in item_deps:
        source_id = item.get("source_item_id")
        if source_id is None:
            continue
        source_id = int(source_id)
        if source_id in item_by_source_id:
            raise RuntimeError(f"Duplicate held-item source ID: {source_id}")
        item_by_source_id[source_id] = item

    type_domain = domains["types"]
    egg_domain = domains["egg_groups"]
    growth_domain = domains["growth_rates"]
    ability_domain = domains["abilities"]
    item_domain = domains["items"]
    growth_by_id = {int(value): symbol for symbol, value in growth_domain.items() if value is not None}
    if len(growth_by_id) != sum(value is not None for value in growth_domain.values()):
        raise RuntimeError("Growth-rate source IDs are ambiguous")

    mapped_rows = []
    blocker_counts = Counter()
    semantic_counts = Counter()
    field_counts = Counter()
    hidden_ability_species = 0
    exp_yield_overflow_species = 0

    for row in rows:
        dex = int(row["national_dex"])
        stats = row.get("statistics")
        if not isinstance(stats, dict) or any(not isinstance(stats.get(name), int) for name in BASE_STATS):
            raise RuntimeError(f"Dex {dex}: required numeric base statistics are missing")
        for field in BASE_STATS:
            upper = 65535 if field == "expYield" else 255
            if not 0 <= int(stats[field]) <= upper:
                raise RuntimeError(f"Dex {dex}: invalid source value for {field}")

        exp_yield = int(stats["expYield"])
        if exp_yield > 255:
            exp_yield_overflow_species += 1
        initializer_stats = {field: int(stats[field]) for field in BASE_STATS}
        for field in EV_STATS:
            value = int(stats.get(field, 0))
            if not 0 <= value <= 3:
                raise RuntimeError(f"Dex {dex}: {field}={value} exceeds Emerald's 2-bit EV field")
            initializer_stats[field] = value

        type_symbols, type_ids = row.get("types_source_symbols"), row.get("types_source_ids")
        egg_symbols, egg_ids = row.get("egg_groups_source_symbols"), row.get("egg_groups_source_ids")
        if not isinstance(type_symbols, list) or len(type_symbols) != 2 or not isinstance(type_ids, list) or len(type_ids) != 2:
            raise RuntimeError(f"Dex {dex}: expected two source type slots and IDs")
        if not isinstance(egg_symbols, list) or len(egg_symbols) != 2 or not isinstance(egg_ids, list) or len(egg_ids) != 2:
            raise RuntimeError(f"Dex {dex}: expected two source egg-group slots and IDs")

        types = [
            map_symbol(symbol, source_id, type_domain, type_deps,
                       "source_type_id", "emerald_type_id", "type")
            for symbol, source_id in zip(type_symbols, type_ids)
        ]
        egg_groups = [
            map_symbol(symbol, source_id, egg_domain, egg_deps,
                       "source_egg_group_id", "emerald_egg_group_id", "egg group")
            for symbol, source_id in zip(egg_symbols, egg_ids)
        ]

        growth_id = row.get("growth_rate_source_id")
        growth_symbol = growth_by_id.get(int(growth_id)) if growth_id is not None else None
        if growth_symbol is None:
            raise RuntimeError(f"Dex {dex}: unresolved growth-rate source enum")
        growth = map_symbol(
            growth_symbol, int(growth_id), growth_domain, growth_deps,
            "source_growth_rate_id", "emerald_growth_rate_id", "growth rate",
        )

        ability_symbols = row.get("abilities_source_symbols")
        ability_ids = row.get("abilities_source_ids")
        hidden_symbol, hidden_id = row.get("hidden_ability_source_symbol"), row.get("hidden_ability_source_id")
        if not isinstance(ability_symbols, list) or len(ability_symbols) != 3:
            raise RuntimeError(f"Dex {dex}: expected three source ability slots")
        if not isinstance(ability_ids, list) or len(ability_ids) != 2 or hidden_symbol != ability_symbols[2]:
            raise RuntimeError(f"Dex {dex}: source hidden-ability slot is malformed")
        abilities = []
        for slot, (symbol, source_id) in enumerate(
            zip(ability_symbols, [ability_ids[0], ability_ids[1], hidden_id]), start=1
        ):
            mapped = map_symbol(
                symbol, source_id, ability_domain, ability_deps,
                "source_ability_id", "emerald_ability_id", "ability",
            )
            dependency = ability_deps.get(symbol, {})
            mapped.update({
                "slot": slot,
                "slot_role": ("primary" if slot == 1 else "secondary" if slot == 2 else "hidden"),
                "emerald_struct_slot_supported": slot < NUM_ABILITY_SLOTS,
                "target_behavior_audited": bool(dependency.get("target_behavior_audited")),
            })
            abilities.append(mapped)

        held_items = {
            "common": map_held_item(row.get("item_common_source_id"), item_domain, item_by_source_id),
            "rare": map_held_item(row.get("item_rare_source_id"), item_domain, item_by_source_id),
        }

        blockers, pending = [], []
        for mapped in types:
            if mapped["emerald_id"] is None:
                blockers.append(f"type_enum_unmapped:{mapped['symbol']}")
            target = type_deps.get(mapped["symbol"], {})
            if not target.get("type_chart_runtime_audited", False):
                pending.append(f"type_chart_not_audited:{mapped['symbol']}")
        for mapped in egg_groups:
            if mapped["emerald_id"] is None:
                blockers.append(f"egg_group_enum_unmapped:{mapped['symbol']}")
        if growth["emerald_id"] is None:
            blockers.append(f"growth_rate_enum_unmapped:{growth['symbol']}")
        for mapped in abilities:
            if mapped["emerald_id"] is None:
                blockers.append(f"ability_enum_unmapped:{mapped['symbol']}")
            if mapped["slot"] == 3 and mapped["symbol"] != "NONE":
                pending.append("hidden_ability_acquisition_flow_not_implemented")
            if mapped["symbol"] != "NONE" and not mapped["target_behavior_audited"]:
                pending.append(f"ability_behavior_not_audited:{mapped['symbol']}")
        for label, item in held_items.items():
            if item["source_id"] not in (None, 0) and item["emerald_id"] is None:
                blockers.append(f"held_item_enum_unmapped:{label}:{item['symbol'] or 'UNKNOWN'}")
            if item["source_id"] not in (None, 0) and not item["target_data_record_present"]:
                blockers.append(f"held_item_data_missing:{label}:{item['symbol'] or 'UNKNOWN'}")
            if item["source_id"] not in (None, 0) and item.get("target_constant_present") and not item.get("target_behavior_audited"):
                pending.append(f"held_item_behavior_not_audited:{item['symbol']}")
        if exp_yield > 255:
            blockers.append("exp_yield_exceeds_emerald_u8")
        if row.get("item_rare_source_id") is None:
            blockers.append("rare_held_item_source_id_unresolved")

        blocker_counts.update(set(blockers))
        semantic_counts.update(set(pending))
        field_counts["type_slots"] += len(types)
        field_counts["type_slots_mapped"] += sum(item["emerald_id"] is not None for item in types)
        field_counts["egg_group_slots"] += len(egg_groups)
        field_counts["egg_group_slots_mapped"] += sum(item["emerald_id"] is not None for item in egg_groups)
        field_counts["ability_slots"] += len(abilities)
        field_counts["ability_slots_mapped"] += sum(item["emerald_id"] is not None for item in abilities)
        field_counts["growth_rate_rows"] += 1
        field_counts["growth_rate_rows_mapped"] += growth["emerald_id"] is not None
        for item in held_items.values():
            if item["source_id"] not in (None, 0):
                field_counts["held_item_references"] += 1
                field_counts["held_item_references_mapped"] += item["emerald_id"] is not None
        hidden_ability_species += ability_symbols[2] != "NONE"

        mapped_rows.append({
            "national_dex": dex,
            "national_symbol": row["national_symbol"],
            "source_species_symbol": row["source_species_symbol"],
            "species_introduction_generation": row["_introduction_generation"],
            "source_generation": row["source_generation"],
            "source_file": row["source_file"],
            "production_emerald_species_id": None,
            "statistics_source_values": dict(stats),
            "statistics_emerald_initializer_values": initializer_stats,
            "types": types,
            "egg_groups": egg_groups,
            "growth_rate": growth,
            "abilities": abilities,
            "held_items": held_items,
            "gender_ratio_source_value": row.get("gender_ratio_source_value"),
            "friendship_source_value": row.get("friendship_source_value"),
            "body_color_source_value": row.get("body_color_source_value"),
            "runtime_blockers": sorted(set(blockers)),
            "runtime_semantics_pending": sorted(set(pending)),
            "runtime_activation_allowed": False,
        })

    audit = {
        "schema_version": 1,
        "status": "explicit_symbol_mapping_staging_only",
        "runtime_activation_allowed": False,
        "national_dex_range": [dexes[0], dexes[-1]],
        "species_count": len(mapped_rows),
        "counts": {
            "species": len(mapped_rows),
            "species_with_hidden_ability": hidden_ability_species,
            "species_with_exp_yield_above_255": exp_yield_overflow_species,
            "species_with_runtime_blockers": sum(bool(row["runtime_blockers"]) for row in mapped_rows),
            "runtime_ready_species": 0,
            **dict(field_counts),
        },
        "runtime_blocker_counts": dict(sorted(blocker_counts.items())),
        "runtime_semantics_pending_counts": dict(sorted(semantic_counts.items())),
        "blocking_gates": [
            "No production Emerald internal IDs have been allocated for the 512 species.",
            "The three ability slots are represented in runtime storage; hidden-ability encounter, breeding and distribution flows still need implementation.",
            "Emerald SpeciesInfo stores expYield as u8; source values above 255 cannot be copied without a runtime layout change.",
            "Missing abilities, Fairy type, held-item data, move/evolution tables and graphics remain incomplete or unaudited.",
            "In-game migration of persistent species IDs and old saves has not been validated.",
        ],
        "invariants": [
            "Expansion source IDs and Emerald target IDs are stored separately.",
            "Missing target mappings remain null; no numeric enum is guessed or copied.",
            "The mapping ledger does not emit gSpeciesInfo or production species IDs.",
            "All five generation batches remain read-only staging inputs.",
        ],
    }
    mapping = {
        "schema_version": 1,
        "status": audit["status"],
        "runtime_activation_allowed": False,
        "source_snapshot": batches[0].get("source_snapshot"),
        "national_dex_range": audit["national_dex_range"],
        "species_count": len(mapped_rows),
        "species": mapped_rows,
        "invariants": audit["invariants"],
    }
    return mapping, audit


def main() -> int:
    try:
        batches = [load_json(path) for path in BATCH_PATHS]
        dependencies = {name: load_json(path) for name, path in DEPENDENCY_PATHS.items()}
        mapping, audit = build_runtime_mapping(batches, dependencies)
        REPORTS.mkdir(parents=True, exist_ok=True)
        OUTPUT_DATA.write_text(json.dumps(mapping, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        OUTPUT_AUDIT.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(audit["counts"], indent=2))
        print(f"Runtime activation allowed: {audit['runtime_activation_allowed']}")
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
        print(f"GEN8 RUNTIME MAPPING FAILED: {error}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
