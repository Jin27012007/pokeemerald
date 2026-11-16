#!/usr/bin/env python3
"""Read-only readiness report for three Generation 4 evolutionary families."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "reports/gen8-conversion/gen4_species_pilot.json"

FAMILIES = {
    "Starly line": {396: "STARLY", 397: "STARAVIA", 398: "STARAPTOR"},
    "Bidoof line": {399: "BIDOOF", 400: "BIBAREL"},
    "Shinx line": {403: "SHINX", 404: "LUXIO", 405: "LUXRAY"},
}
EXPECTED_TARGETS = {
    "STARLY": "STARAVIA",
    "STARAVIA": "STARAPTOR",
    "BIDOOF": "BIBAREL",
    "SHINX": "LUXIO",
    "LUXIO": "LUXRAY",
}
REQUIRED_STATS = (
    "baseHP", "baseAttack", "baseDefense",
    "baseSpeed", "baseSpAttack", "baseSpDefense",
)


def normalize_symbol(value: str | None) -> str | None:
    if not value:
        return None
    value = value.upper()
    for prefix in ("NATIONAL_DEX_", "SPECIES_"):
        if value.startswith(prefix):
            value = value[len(prefix):]
    return value


def unique_by_dex(rows: list[dict], label: str) -> dict[int, dict]:
    result = {}
    for row in rows:
        dex = int(row["national_dex"])
        if dex in result:
            raise RuntimeError(f"Duplicate National Dex #{dex} in {label}")
        result[dex] = row
    return result


def audit(inputs: dict | None = None) -> dict:
    import audit_gen4_species_readiness as readiness

    if inputs is None:
        inputs = readiness.load_inputs()

    batch = inputs["batch"]
    if batch.get("batch_id") != "gen4_species_info":
        raise RuntimeError("Expected the Generation 4 SpeciesInfo staging batch")
    if batch.get("status") != "staging_only_not_runtime":
        raise RuntimeError("Gen 4 source batch is not marked staging-only")
    if batch.get("runtime_activation_allowed") is not False:
        raise RuntimeError("Gen 4 source batch unexpectedly permits runtime activation")

    wanted = {
        dex: symbol
        for family in FAMILIES.values()
        for dex, symbol in family.items()
    }
    if len(wanted) != 8:
        raise RuntimeError("Pilot definition must contain exactly eight species")

    source_rows = unique_by_dex(batch.get("species", []), "SpeciesInfo batch")
    mapping_rows = unique_by_dex(inputs["runtime_mapping"].get("species", []), "runtime mapping")
    learnset_rows = unique_by_dex(inputs["learnsets"], "level-up learnsets")
    evolution_rows = unique_by_dex(inputs["evolutions"], "evolution catalog")
    graphics_rows = unique_by_dex(inputs["graphics"], "graphics catalog")
    cry_rows = unique_by_dex(inputs["cries"], "cry catalog")

    missing_dex = sorted(set(wanted) - set(source_rows))
    if missing_dex:
        raise RuntimeError(f"Pilot species missing from source batch: {missing_dex}")

    pending_moves = set(inputs["pending"].get("missing_target_battle_move_records", []))
    pilot_move_symbols: set[str] = set()
    missing_pilot_moves: set[str] = set()
    species_report = []

    for dex, expected_symbol in sorted(wanted.items()):
        source = source_rows[dex]
        actual_symbol = normalize_symbol(
            source.get("national_symbol") or source.get("source_species_symbol")
        )
        if actual_symbol != expected_symbol:
            raise RuntimeError(
                f"National Dex #{dex} expected {expected_symbol}, found {actual_symbol}"
            )

        source_fields = set(source.get("source_fields_present", []))
        missing_fields = sorted(readiness.REQUIRED_SOURCE_FIELDS - source_fields)
        stats = source.get("statistics", {})
        missing_stats = [key for key in REQUIRED_STATS if key not in stats]
        if missing_fields or missing_stats:
            raise RuntimeError(
                f"{expected_symbol} source data incomplete: "
                f"fields={missing_fields}, stats={missing_stats}"
            )

        mapping = mapping_rows[dex]
        if mapping.get("production_emerald_species_id") is not None:
            raise RuntimeError(f"{expected_symbol} unexpectedly has a production species ID")
        if mapping.get("runtime_activation_allowed") is not False:
            raise RuntimeError(f"{expected_symbol} unexpectedly permits runtime activation")

        learnset = learnset_rows[dex]
        moves = learnset.get("moves", [])
        move_symbols = {
            move.get("move") for move in moves
            if isinstance(move.get("move"), str) and move.get("move")
        }
        if not moves or not move_symbols:
            raise RuntimeError(f"{expected_symbol} has no usable level-up learnset")
        pilot_move_symbols.update(move_symbols)
        missing_pilot_moves.update(move_symbols & pending_moves)

        graphics = graphics_rows[dex]
        cry = cry_rows[dex]
        evolution = evolution_rows[dex]
        graphics_missing = sorted(
            asset for asset, present in graphics.get("target_asset_presence", {}).items()
            if not present
        )

        species_report.append({
            "national_dex": dex,
            "species": expected_symbol,
            "source_generation": source.get("source_generation"),
            "source_file": source.get("source_file"),
            "base_stats": {key: stats[key] for key in REQUIRED_STATS},
            "types_source_symbols": source.get("types_source_symbols", []),
            "abilities_source_symbols": source.get("abilities_source_symbols", []),
            "learnset_move_count": len(moves),
            "learnset_moves": sorted(move_symbols),
            "moves_missing_target_battle_records": sorted(move_symbols & pending_moves),
            "evolution_targets": [
                normalize_symbol(edge.get("target_species_symbol"))
                for edge in evolution.get("evolutions", [])
            ],
            "evolution_methods": [
                edge.get("method_symbol") for edge in evolution.get("evolutions", [])
            ],
            "target_graphics_complete": graphics.get("target_graphics_assets_complete", False),
            "missing_target_graphics_assets": graphics_missing,
            "target_cry_present": cry.get("emerald_cry_table_match", False),
            "production_emerald_species_id": None,
            "runtime_blockers": mapping.get("runtime_blockers", []),
            "runtime_semantics_pending": mapping.get("runtime_semantics_pending", []),
            "runtime_activation_allowed": False,
        })

    actual_edges = {}
    for dex in wanted:
        row = evolution_rows[dex]
        source_symbol = normalize_symbol(row.get("species_symbol"))
        for edge in row.get("evolutions", []):
            if source_symbol in EXPECTED_TARGETS:
                actual_edges[source_symbol] = {
                    "target": normalize_symbol(edge.get("target_species_symbol")),
                    "method": edge.get("method_symbol"),
                    "parameter": edge.get("parameter_expression"),
                    "conditions": edge.get("condition_expression"),
                }

    missing_edges = []
    for source_symbol, expected_target in EXPECTED_TARGETS.items():
        observed = actual_edges.get(source_symbol)
        if observed is None or observed["target"] != expected_target:
            missing_edges.append({
                "source": source_symbol,
                "expected_target": expected_target,
                "observed": observed,
            })

    family_report = []
    for family_name, members in FAMILIES.items():
        family_report.append({
            "family": family_name,
            "species": [
                {
                    "national_dex": dex,
                    "species": symbol,
                    "evolves_to": EXPECTED_TARGETS.get(symbol),
                }
                for dex, symbol in members.items()
            ],
        })

    missing_graphics_count = sum(
        not row["target_graphics_complete"] for row in species_report
    )
    missing_cry_count = sum(not row["target_cry_present"] for row in species_report)
    missing_id_count = sum(
        row["production_emerald_species_id"] is None for row in species_report
    )
    counts = {
        "pilot_families": len(FAMILIES),
        "pilot_species": len(species_report),
        "species_with_complete_source_stats": len(species_report),
        "species_with_level_up_learnsets": sum(
            row["learnset_move_count"] > 0 for row in species_report
        ),
        "distinct_level_up_moves": len(pilot_move_symbols),
        "distinct_moves_missing_target_battle_records": len(missing_pilot_moves),
        "evolution_edges_expected": len(EXPECTED_TARGETS),
        "evolution_edges_missing_or_mismatched": len(missing_edges),
        "species_without_production_internal_ids": missing_id_count,
        "species_without_complete_target_graphics": missing_graphics_count,
        "species_without_target_cry_entries": missing_cry_count,
    }

    blockers = []
    if missing_id_count:
        blockers.append({
            "area": "production species IDs",
            "species_count": missing_id_count,
            "detail": "IDs remain unallocated until the global index-consumer and save-migration gates pass.",
        })
    if missing_pilot_moves:
        blockers.append({
            "area": "battle move records",
            "move_count": len(missing_pilot_moves),
            "symbols": sorted(missing_pilot_moves),
        })
    if missing_edges:
        blockers.append({
            "area": "evolution links",
            "edge_count": len(missing_edges),
            "details": missing_edges,
        })
    if missing_graphics_count:
        blockers.append({
            "area": "graphics",
            "species_count": missing_graphics_count,
            "detail": "Emerald-format front/back sprites, animations, icons, footprints and palettes are not complete for every pilot species.",
        })
    if missing_cry_count:
        blockers.append({
            "area": "cries",
            "species_count": missing_cry_count,
            "detail": "Target cry-table entries/audio assets are not complete for every pilot species.",
        })

    return {
        "schema_version": 1,
        "status": "pilot_family_pre_runtime_audit",
        "runtime_activation_allowed": False,
        "identity_domain": "national_dex",
        "scope": {
            "generation": 4,
            "national_dex_range": [387, 493],
            "selected_families": list(FAMILIES),
            "selected_species": [
                {"national_dex": dex, "species": symbol}
                for dex, symbol in sorted(wanted.items())
            ],
        },
        "counts": counts,
        "families": family_report,
        "species": species_report,
        "pilot_unique_moves_missing_battle_records": sorted(missing_pilot_moves),
        "evolution_links": actual_edges,
        "blockers": blockers,
        "safety_invariants": [
            "No production Emerald species ID is assigned by this pilot.",
            "NUM_SPECIES, SPECIES_EGG and the auxiliary Unown ID range remain unchanged.",
            "National Dex numbers are identity keys and are never runtime array indices.",
            "No production SpeciesInfo, learnset, evolution, graphics or cry table is modified.",
            "This report is not evidence that the selected Pokémon are playable in a ROM.",
        ],
    }


def main() -> int:
    try:
        report = audit()
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({
            "output": str(REPORT.relative_to(ROOT)),
            "counts": report["counts"],
            "runtime_activation_allowed": report["runtime_activation_allowed"],
        }, indent=2))
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as error:
        print(f"GEN 4 SPECIES PILOT AUDIT FAILED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
