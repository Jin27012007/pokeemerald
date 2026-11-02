#!/usr/bin/env python3
"""Inventory all Expansion SpeciesInfo candidates grouped by National Dex identity."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
SPEC = importlib.util.spec_from_file_location("gen8_convert_emerald", TOOLS / "gen8_convert_emerald.py")
assert SPEC and SPEC.loader
conv = importlib.util.module_from_spec(SPEC)
import sys
sys.modules[SPEC.name] = conv
SPEC.loader.exec_module(conv)

VENDOR = ROOT / "tools/vendor/pokeemerald-expansion"
OUT = ROOT / "reports/gen8-conversion/species_info_candidates_by_dex.json"

def main() -> int:
    source_files = sorted((VENDOR / "src/data/pokemon/species_info").glob("gen_*_families.h"))
    source_texts = {path.name: path.read_text(encoding="utf-8") for path in source_files}
    combined = "\n".join(source_texts.values())
    generations = {}
    for path in source_files:
        for row in conv.balanced_species_records(source_texts[path.name]):
            generations[row["symbol"]] = int(path.stem.split("_")[1])
    target_pokemon = (ROOT / "include/constants/pokemon.h").read_text(encoding="utf-8")
    source_pokemon = (VENDOR / "include/constants/pokemon.h").read_text(encoding="utf-8")
    source_abilities = (VENDOR / "include/constants/abilities.h").read_text(encoding="utf-8")
    source_items = (VENDOR / "include/constants/items.h").read_text(encoding="utf-8")
    target_info = (ROOT / "src/data/pokemon/species_info.h").read_text(encoding="utf-8")
    target_abilities = (ROOT / "include/constants/abilities.h").read_text(encoding="utf-8")
    target_items = (ROOT / "include/constants/items.h").read_text(encoding="utf-8")
    macros = {}
    for text in source_texts.values():
        macros.update(conv.extract_c_macros(conv.resolve_source_conditionals(text, 8)))
    macros.update(conv.extract_c_macros(conv.resolve_source_conditionals(source_pokemon, 8)))
    macros["__catalog__"] = macros.copy()
    parsed = conv.parse_species_info(
        combined, target_info, target_pokemon, target_abilities, target_items,
        generations, source_abilities, source_items, source_pokemon, macros
    )
    pokedex = {
        row["symbol"]: row["id"]
        for row in conv.symbols(
            (ROOT / "include/constants/pokedex.h").read_text(encoding="utf-8"),
            "NATIONAL_DEX_", enum=True
        )
    }
    groups = {dex: [] for dex in range(1, 899)}
    for row in parsed["compact_records"] + parsed["unresolved_records"]:
        symbol = row.get("national_dex_symbol")
        dex = pokedex.get(symbol) if symbol else None
        if dex in groups:
            groups[dex].append({
                "species_symbol": row["species_symbol"],
                "national_dex_symbol": symbol,
                "generation": row["generation"],
                "status": row["status"],
                "source_complete": row.get("source_complete", False),
                "source_fields_resolved": row.get("source_fields_resolved", False),
                "compact_compatible": row.get("compact_compatible", False),
                "runtime_gaps": row.get("runtime_gaps", []),
                "unresolved": row.get("unresolved", []),
            })
    result = {
        "source": "pinned pokeemerald-expansion SpeciesInfo families",
        "canonical_dex_candidate_groups": len(groups),
        "candidate_record_count": sum(len(rows) for rows in groups.values()),
        "groups": {str(dex): rows for dex, rows in groups.items()},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate_record_count": result["candidate_record_count"],
        "dex_groups_with_candidates": sum(bool(rows) for rows in groups.values()),
        "dex_groups_without_candidates": sum(not rows for rows in groups.values()),
        "ambiguous_dex_groups": sum(len(rows) > 1 for rows in groups.values()),
        "output": str(OUT.relative_to(ROOT)),
    }, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
