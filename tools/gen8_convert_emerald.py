#!/usr/bin/env python3
"""Generate a safe, reviewable Gen 8 -> vanilla Emerald conversion package.

This tool does NOT write runtime C tables or edit species.h / NUM_SPECIES.
It extracts canonical species identities, Gen 8 move dependencies, learnsets,
and species record field candidates into JSON/CSV reports. Any semantic
translation needed by vanilla Emerald remains explicitly unresolved.
"""
from __future__ import annotations
import argparse, csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "tools/vendor/pokeemerald-expansion"
OUT = ROOT / "reports/gen8-conversion"
SOURCE_SPECIES = VENDOR / "include/constants/species.h"
SOURCE_MOVES = VENDOR / "include/constants/moves.h"
SOURCE_INFO = VENDOR / "src/data/pokemon/species_info/gen_8_families.h"
SOURCE_LEARNSETS = VENDOR / "src/data/pokemon/level_up_learnsets/gen_8.h"
TARGET_SPECIES = ROOT / "include/constants/species.h"
TARGET_MOVES = ROOT / "include/constants/moves.h"
TARGET_INFO = ROOT / "src/data/pokemon/species_info.h"
TARGET_LEARNSETS = ROOT / "src/data/pokemon/level_up_learnsets.h"
TARGET_EVOS = ROOT / "src/data/pokemon/evolution.h"
TARGET_DEX = ROOT / "src/data/pokemon/pokedex_entries.h"
TARGET_ORDERS = ROOT / "src/data/pokemon/pokedex_orders.h"
TARGET_CRY = ROOT / "sound/cry_tables.inc"

def read(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"Missing required input: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")

def parse_enum(text: str, prefix: str) -> list[dict]:
    found = []
    rx = re.compile(rf"^\s*{re.escape(prefix)}([A-Z0-9_]+)\s*=\s*(0x[0-9a-fA-F]+|\d+)\s*,?\s*(?://.*)?$", re.M)
    for m in rx.finditer(text):
        found.append({"symbol": m.group(1), "id": int(m.group(2), 0)})
    return found

def parse_defines(text: str, prefix: str) -> list[dict]:
    found = []
    rx = re.compile(rf"^#define\s+{re.escape(prefix)}([A-Z0-9_]+)\s+(0x[0-9a-fA-F]+|\d+)\s*$", re.M)
    for m in rx.finditer(text):
        found.append({"symbol": m.group(1), "id": int(m.group(2), 0)})
    return found

def camel_to_symbol(name: str) -> str:
    # Preserve acronym-free CamelCase source learnset names.
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).upper()

def extract_learnsets(text: str) -> list[dict]:
    results = []
    block_rx = re.compile(r"static const struct LevelUpMove s([A-Za-z0-9]+)LevelUpLearnset\[\]\s*=\s*\{([\s\S]*?)\n\};")
    for m in block_rx.finditer(text):
        moves = [{"level": int(level), "move": move}
                 for level, move in re.findall(r"LEVEL_UP_MOVE\(\s*(\d+)\s*,\s*MOVE_([A-Z0-9_]+)\s*\)", m.group(2))]
        results.append({"source_species": m.group(1), "species_symbol_guess": camel_to_symbol(m.group(1)), "moves": moves})
    return results

def extract_species_records(text: str) -> dict:
    # Extract only balanced initializer blocks. This preserves source fields
    # verbatim for review; it does not try to compile Expansion-only macros.
    rows = []
    starts = list(re.finditer(r"^\s*\[SPECIES_([A-Z0-9_]+)\]\s*=\s*\{", text, re.M))
    for idx, m in enumerate(starts):
        depth = 1
        i = m.end()
        in_string = False
        escaped = False
        while i < len(text) and depth:
            ch = text[i]
            if in_string:
                if escaped: escaped = False
                elif ch == "\\\\": escaped = True
                elif ch == '"': in_string = False
            else:
                if ch == '"': in_string = True
                elif ch == "{": depth += 1
                elif ch == "}": depth -= 1
            i += 1
        if depth == 0:
            body = text[m.end():i-1]
            rows.append({"species_symbol": m.group(1), "raw_fields": body.strip()})
    return {"records": rows, "record_count": len(rows)}

def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="validate all source files and print counts without writing outputs")
    args = ap.parse_args()
    try:
        src_species_text = read(SOURCE_SPECIES)
        src_moves_text = read(SOURCE_MOVES)
        src_info_text = read(SOURCE_INFO)
        src_learn_text = read(SOURCE_LEARNSETS)
        target_species_text = read(TARGET_SPECIES)
        target_moves_text = read(TARGET_MOVES)
        # Read all target structures so generator fails early if target layout changes.
        target_info_text = read(TARGET_INFO)
        target_learn_text = read(TARGET_LEARNSETS)
        target_evo_text = read(TARGET_EVOS)
        target_dex_text = read(TARGET_DEX)
        target_orders_text = read(TARGET_ORDERS)
        target_cry_text = read(TARGET_CRY)

        source_species = parse_enum(src_species_text, "SPECIES_")
        target_species = parse_defines(target_species_text, "SPECIES_")
        source_moves = parse_enum(src_moves_text, "MOVE_")
        target_moves = parse_defines(target_moves_text, "MOVE_")
        target_species_names = {x["symbol"] for x in target_species}
        target_move_names = {x["symbol"] for x in target_moves}

        dex_species = sorted([x for x in source_species if 1 <= x["id"] <= 898], key=lambda x:x["id"])
        if [x["id"] for x in dex_species] != list(range(1, 899)):
            raise RuntimeError("Expansion species constants do not form canonical National Dex 1..898")
        if len({x["symbol"] for x in dex_species}) != 898:
            raise RuntimeError("Duplicate canonical species symbol in Expansion source")

        new_species = []
        for item in dex_species:
            if item["symbol"] not in target_species_names:
                new_species.append({"national_dex": item["id"], "source_symbol": item["symbol"], "emerald_internal_id": None, "status": "needs_internal_id_assignment"})
        source_move_by_name = {x["symbol"]:x for x in source_moves}
        learnsets = extract_learnsets(src_learn_text)
        used_moves = sorted({m["move"] for ls in learnsets for m in ls["moves"]})
        move_rows = []
        for name, item in source_move_by_name.items():
            if item["id"] <= 354:
                continue
            move_rows.append({"source_symbol": name, "source_id": item["id"], "emerald_id": None,
                              "used_by_gen8_learnset": name in used_moves,
                              "status": "needs_move_definition_and_contest_mapping"})
        species_info = extract_species_records(src_info_text)

        # Keep source structures separate from production C. Only copy values
        # when a direct field-name/value translation is proven by this tool.
        incompatible_fields = sorted(set(re.findall(r"^\s*\.([A-Za-z0-9_]+)\s*=", src_info_text, re.M)) -
                                     set(re.findall(r"^\s*\.([A-Za-z0-9_]+)\s*=", target_info_text, re.M)))
        evolution_source = {"status":"not_generated", "reason":"Gen 8 expansion vendor snapshot does not include evolution table source"}
        dex_source = {"status":"not_generated", "reason":"No complete Gen 8 Pokédex entry text dataset is present in pinned vendor snapshot"}
        cry_source = {"status":"not_generated", "reason":"No Gen 8 cry binary/source assets or cry mapping are present in pinned vendor snapshot"}
        report = {
            "scope":"canonical National Dex 1-898; no alternate forms as extra dex species",
            "production_tables_modified":False,
            "species_enum_or_NUM_SPECIES_modified":False,
            "source_counts":{"canonical_species":len(dex_species),"new_species":len(new_species),
                "source_move_identifiers":len(source_moves),"new_move_identifiers_after_gen3":len(move_rows),
                "learnset_blocks_extracted":len(learnsets),"unique_moves_in_extracted_learnsets":len(used_moves),
                "species_info_records_extracted":species_info["record_count"]},
            "new_species":new_species,
            "move_dependencies":move_rows,
            "move_symbols_missing_from_emerald":sorted(set(used_moves)-target_move_names),
            "learnsets":learnsets,
            "species_info":species_info,
            "species_info_fields_needing_translation":incompatible_fields,
            "evolutions":evolution_source,
            "pokedex_entries":dex_source,
            "cries":cry_source,
            "validation":{"canonical_dex_contiguous":True,"existing_species_ids_preserved":True,
                "new_species_ids_assigned":False,"learnset_moves_all_present_in_emerald":not bool(set(used_moves)-target_move_names),
                "ready_for_runtime_import":False}
        }
        if args.check:
            print(json.dumps(report["source_counts"], indent=2))
            print("Production tables untouched; runtime import readiness: BLOCKED")
            return 0
        OUT.mkdir(parents=True, exist_ok=True)
        write_json(OUT / "conversion_report.json", report)
        write_json(OUT / "species_records_raw.json", species_info)
        write_json(OUT / "learnsets_raw.json", learnsets)
        write_json(OUT / "species_id_mapping_template.json", new_species)
        write_json(OUT / "move_mapping_template.json", move_rows)
        with (OUT / "move_dependencies.csv").open("w", newline="", encoding="utf-8") as f:
            w=csv.DictWriter(f, fieldnames=["source_symbol","source_id","emerald_id","used_by_gen8_learnset","status"])
            w.writeheader(); w.writerows(move_rows)
        print("Generated reviewable conversion package in reports/gen8-conversion")
        print(json.dumps(report["source_counts"], indent=2))
        return 0
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"GEN8 CONVERSION FAILED: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
