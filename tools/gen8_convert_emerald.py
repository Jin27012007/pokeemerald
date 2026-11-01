#!/usr/bin/env python3
"""Build a safe Gen 8 staging package for Pokémon Emerald.

This tool only emits reviewable reports and isolated C helper data. It never
edits NUM_SPECIES, species IDs, move IDs, live SpeciesInfo tables, SaveBlock1,
SaveBlock2, or PokemonStorage.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "tools/vendor/pokeemerald-expansion"
OUT = ROOT / "reports/gen8-conversion"
SRC_SPECIES = VENDOR / "include/constants/species.h"
SRC_MOVES = VENDOR / "include/constants/moves.h"
SRC_LEARNSETS = VENDOR / "src/data/pokemon/level_up_learnsets/gen_8.h"
SRC_SPECIES_INFO = VENDOR / "src/data/pokemon/species_info/gen_8_families.h"
DST_SPECIES = ROOT / "include/constants/species.h"
DST_MOVES = ROOT / "include/constants/moves.h"
DST_INFO = ROOT / "src/data/pokemon/species_info.h"
DST_POKEMON_H = ROOT / "include/pokemon.h"
DST_POKEMON_CONSTANTS = ROOT / "include/constants/pokemon.h"
DST_ABILITIES = ROOT / "include/constants/abilities.h"
DST_ITEMS = ROOT / "include/constants/items.h"

BASE_ALIASES = {
    "CASTFORM_NORMAL": "CASTFORM", "DEOXYS_NORMAL": "DEOXYS",
    "BURMY_PLANT": "BURMY", "WORMADAM_PLANT": "WORMADAM",
    "MOTHIM_PLANT": "MOTHIM", "CHERRIM_OVERCAST": "CHERRIM",
    "SHELLOS_WEST": "SHELLOS", "GASTRODON_WEST": "GASTRODON",
    "GIRATINA_ALTERED": "GIRATINA", "SHAYMIN_LAND": "SHAYMIN",
    "ARCEUS_NORMAL": "ARCEUS", "BASCULIN_RED_STRIPED": "BASCULIN",
    "DARMANITAN_STANDARD": "DARMANITAN", "TORNADUS_INCARNATE": "TORNADUS",
    "THUNDURUS_INCARNATE": "THUNDURUS", "LANDORUS_INCARNATE": "LANDORUS",
    "KYUREM_NORMAL": "KYUREM", "KELDEO_ORDINARY": "KELDEO",
    "MELOETTA_ARIA": "MELOETTA", "LYCANROC_MIDDAY": "LYCANROC",
    "WISHIWASHI_SOLO": "WISHIWASHI", "ZYGARDE_50": "ZYGARDE",
    "MINIOR_METEOR_RED": "MINIOR", "TOXTRICITY_AMPED": "TOXTRICITY",
    "EISCUE_ICE": "EISCUE", "INDEEDEE_M": "INDEEDEE",
    "MORPEKO_FULL_BELLY": "MORPEKO", "ZACIAN_HERO": "ZACIAN",
    "ZAMAZENTA_HERO": "ZAMAZENTA", "URSHIFU_SINGLE_STRIKE": "URSHIFU",
}

# Only compact fields physically present in vanilla Emerald's struct SpeciesInfo.
COMPACT_FIELDS = (
    "baseHP", "baseAttack", "baseDefense", "baseSpeed", "baseSpAttack",
    "baseSpDefense", "catchRate", "expYield", "evYield_HP", "evYield_Attack",
    "evYield_Defense", "evYield_Speed", "evYield_SpAttack", "evYield_SpDefense",
    "genderRatio", "eggCycles", "friendship", "growthRate", "bodyColor",
)
ALL_COMPACT_FIELDS = set(COMPACT_FIELDS) | {
    "types", "abilities", "eggGroups", "itemCommon", "itemRare"
}

def read(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"Missing input: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")

def symbols(text: str, prefix: str, enum: bool = False) -> list[dict]:
    pattern = (
        rf"^\s*{re.escape(prefix)}([A-Z0-9_]+)\s*=\s*(\d+)\s*,?\s*(?://.*)?$"
        if enum else
        rf"^#define\s+{re.escape(prefix)}([A-Z0-9_]+)\s+(\d+)\s*$"
    )
    return [{"symbol": m.group(1), "id": int(m.group(2))}
            for m in re.finditer(pattern, text, re.M)]

def balanced_species_records(text: str) -> list[dict]:
    start_re = re.compile(r"^\s*\[SPECIES_([A-Z0-9_]+)\]\s*=\s*\{", re.M)
    records = []
    for m in start_re.finditer(text):
        i, depth, in_string, escaped = m.end(), 1, False, False
        while i < len(text) and depth:
            c = text[i]
            if in_string:
                if escaped:
                    escaped = False
                elif c == "\\\\":
                    escaped = True
                elif c == '"':
                    in_string = False
            else:
                if c == '"':
                    in_string = True
                elif c == "{":
                    depth += 1
                elif c == "}":
                    depth -= 1
            i += 1
        if depth == 0:
            records.append({"symbol": m.group(1), "body": text[m.end():i-1].strip()})
    return records

def extract_learnsets(text: str) -> list[dict]:
    block_re = re.compile(
        r"static const struct LevelUpMove s([A-Za-z0-9]+)LevelUpLearnset\[\]\s*=\s*\{([\s\S]*?)\n\};"
    )
    move_re = re.compile(r"LEVEL_UP_MOVE\(\s*(\d+)\s*,\s*MOVE_([A-Z0-9_]+)\s*\)")
    result = []
    for block in block_re.finditer(text):
        moves = [{"level": int(m.group(1)), "move": m.group(2)}
                 for m in move_re.finditer(block.group(2))]
        if moves:
            result.append({"source_species": block.group(1), "moves": moves})
    return result

def extract_designated_fields(body: str) -> dict:
    """Extract simple scalar designators; compound/macro expressions remain unresolved."""
    fields = {}
    scalar_re = re.compile(r"^\s*\.([A-Za-z0-9_]+)\s*=\s*([^,\n]+),", re.M)
    for m in scalar_re.finditer(body):
        fields[m.group(1)] = m.group(2).strip()
    return fields

def emit_species_header() -> str:
    return """// Generated by tools/gen8_convert_emerald.py. DO NOT EDIT BY HAND.
#ifndef GUARD_GEN8_SPECIES_MAP_H
#define GUARD_GEN8_SPECIES_MAP_H
#include "global.h"
#define GEN8_NATIONAL_DEX_COUNT 898
#define GEN8_EXISTING_BASE_SPECIES_COUNT 386
#define GEN8_UNALLOCATED_BASE_SPECIES_COUNT 512
struct Gen8SpeciesMapEntry
{
    u16 nationalDex;
    u16 emeraldSpecies; // SPECIES_NONE means no Emerald internal ID assigned.
};
extern const struct Gen8SpeciesMapEntry gGen8SpeciesMap[GEN8_NATIONAL_DEX_COUNT + 1];
#endif // GUARD_GEN8_SPECIES_MAP_H
"""

def emit_species_c(rows: list[dict]) -> str:
    lines = [
        "// Generated by tools/gen8_convert_emerald.py. DO NOT EDIT BY HAND.",
        '#include "global.h"', '#include "constants/species.h"',
        '#include "gen8_species_map.h"', "",
        "const struct Gen8SpeciesMapEntry gGen8SpeciesMap[GEN8_NATIONAL_DEX_COUNT + 1] =",
        "{", "    [0] = { .nationalDex = 0, .emeraldSpecies = SPECIES_NONE },",
    ]
    for row in rows:
        value = str(row["emerald_internal_id"]) if row["emerald_internal_id"] is not None else "SPECIES_NONE"
        lines.append(f'    [{row["national_dex"]}] = {{ .nationalDex = {row["national_dex"]}, .emeraldSpecies = {value} }}, // {row["source_symbol"]}')
    lines.extend(["};", ""])
    return "\n".join(lines)

def emit_readiness_header(counts: dict) -> str:
    return f"""// Generated by tools/gen8_convert_emerald.py. DO NOT EDIT BY HAND.
#ifndef GUARD_GEN8_CONVERSION_STATUS_H
#define GUARD_GEN8_CONVERSION_STATUS_H
#define GEN8_CANONICAL_NATIONAL_DEX_COUNT 898
#define GEN8_EXISTING_BASE_SPECIES_COUNT {counts["existing_species"]}
#define GEN8_UNALLOCATED_BASE_SPECIES_COUNT {counts["new_species"]}
#define GEN8_LEVEL_UP_LEARNSET_BLOCKS {counts["learnset_blocks"]}
#define GEN8_LEVEL_UP_MOVE_ENTRIES {counts["learnset_move_entries"]}
#define GEN8_DISTINCT_LEARNSET_MOVE_SYMBOLS {counts["distinct_learnset_moves"]}
#define GEN8_MISSING_EMERALD_MOVE_SYMBOLS {counts["missing_learnset_moves"]}
#define GEN8_SPECIES_INFO_BLOCKS_FOUND {counts["species_info_blocks"]}
#define GEN8_SPECIES_INFO_COMPACT_RECORDS {counts["species_info_compact_records"]}
#define GEN8_SPECIES_INFO_UNRESOLVED_RECORDS {counts["species_info_unresolved_records"]}
#define GEN8_SPECIES_ID_ASSIGNMENT_COMPLETE 0
#define GEN8_SAVE_EXTENSION_VALIDATED 0
#define GEN8_RUNTIME_TABLES_READY 0
#define GEN8_NUM_SPECIES_EXPANSION_ALLOWED 0
#endif // GUARD_GEN8_CONVERSION_STATUS_H
"""

def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def write_json(path: Path, value) -> None:
    write(path, json.dumps(value, indent=2, ensure_ascii=False) + "\\n")

def parse_species_info(source_text: str, target_info_text: str,
                       type_text: str, ability_text: str, item_text: str) -> dict:
    records = balanced_species_records(source_text)
    type_values = {x["symbol"]: x["id"] for x in symbols(type_text, "TYPE_")}
    ability_values = {x["symbol"]: x["id"] for x in symbols(ability_text, "ABILITY_")}
    egg_values = {x["symbol"]: x["id"] for x in symbols(type_text, "EGG_GROUP_")}
    item_values = {}
    enum_index = -1
    for line in item_text.splitlines():
        m = re.match(r"^\s*ITEM_([A-Z0-9_]+)\s*,", line)
        if m:
            enum_index += 1
            item_values[m.group(1)] = enum_index

    out, unresolved = [], []
    scalar_fields = (
        "baseHP", "baseAttack", "baseDefense", "baseSpeed", "baseSpAttack",
        "baseSpDefense", "catchRate", "expYield", "evYield_HP",
        "evYield_Attack", "evYield_Defense", "evYield_Speed",
        "evYield_SpAttack", "evYield_SpDefense", "genderRatio",
        "eggCycles", "friendship", "growthRate",
    )
    for record in records:
        body = record["body"]
        fields = extract_designated_fields(body)
        problems = []
        values = {}
        for field in scalar_fields:
            raw = fields.get(field)
            if raw is None:
                if field.startswith("evYield_"):
                    values[field] = 0
                    continue
                problems.append(f"missing_scalar:{field}")
                continue
            if re.fullmatch(r"(?:0x[0-9A-Fa-f]+|\d+)", raw):
                values[field] = int(raw, 0)
            else:
                problems.append(f"unresolved_scalar:{field}:{raw}")

        # Type mapping supports MON_TYPES(TYPE_X) or MON_TYPES(TYPE_X, TYPE_Y).
        type_match = re.search(
            r"\.types\s*=\s*MON_TYPES\(\s*TYPE_([A-Z0-9_]+)(?:\s*,\s*TYPE_([A-Z0-9_]+))?\s*\)",
            body,
        )
        type_pair = None
        if type_match:
            names = [type_match.group(1), type_match.group(2) or type_match.group(1)]
            if any(name not in type_values for name in names):
                problems.extend(f"unknown_type:{name}" for name in names if name not in type_values)
            else:
                type_pair = [type_values[name] for name in names]
        else:
            problems.append("unresolved_types")

        egg_match = re.search(
            r"\.eggGroups\s*=\s*MON_EGG_GROUPS\(\s*EGG_GROUP_([A-Z0-9_]+)\s*,\s*EGG_GROUP_([A-Z0-9_]+)\s*\)",
            body,
        )
        egg_pair = None
        if egg_match:
            names = [egg_match.group(1), egg_match.group(2)]
            if any(name not in egg_values for name in names):
                problems.extend(f"unknown_egg_group:{name}" for name in names if name not in egg_values)
            else:
                egg_pair = [egg_values[name] for name in names]
        else:
            problems.append("unresolved_egg_groups")

        ability_match = re.search(
            r"\.abilities\s*=\s*\{\s*ABILITY_([A-Z0-9_]+)\s*,\s*ABILITY_([A-Z0-9_]+)(?:\s*,\s*ABILITY_([A-Z0-9_]+))?\s*\}",
            body,
        )
        ability_pair = None
        if ability_match:
            names = [ability_match.group(1), ability_match.group(2)]
            if any(name not in ability_values for name in names):
                problems.extend(f"unknown_ability:{name}" for name in names if name not in ability_values)
            else:
                ability_pair = [ability_values[name] for name in names]
        else:
            problems.append("unresolved_abilities")

        rare_item_match = re.search(r"\.itemRare\s*=\s*ITEM_([A-Z0-9_]+)", body)
        common_item_match = re.search(r"\.itemCommon\s*=\s*ITEM_([A-Z0-9_]+)", body)
        # The source may omit itemCommon or itemRare; missing means ITEM_NONE.
        rare_name = rare_item_match.group(1) if rare_item_match else "NONE"
        common_name = common_item_match.group(1) if common_item_match else "NONE"
        if rare_name not in item_values:
            problems.append(f"unknown_item:{rare_name}")
        if common_name not in item_values:
            problems.append(f"unknown_item:{common_name}")

        body_color_match = re.search(r"\.bodyColor\s*=\s*BODY_COLOR_([A-Z0-9_]+)", body)
        body_color_names = {
            "RED": 0, "BLUE": 1, "YELLOW": 2, "GREEN": 3, "BLACK": 4,
            "BROWN": 5, "PURPLE": 6, "GRAY": 7, "WHITE": 8, "PINK": 9
        }
        body_color = None
        if body_color_match and body_color_match.group(1) in body_color_names:
            body_color = body_color_names[body_color_match.group(1)]
        else:
            problems.append("unresolved_body_color")

        record_data = {
            "species_symbol": record["symbol"],
            "statistics": values,
            "types": type_pair,
            "egg_groups": egg_pair,
            "abilities": ability_pair,
            "item_common": item_values.get(common_name) if common_name in item_values else None,
            "item_rare": item_values.get(rare_name) if rare_name in item_values else None,
            "body_color": body_color,
            "status": "compact_fields_resolved" if not problems else "manual_mapping_required",
            "unresolved": problems,
        }
        if not problems:
            out.append(record_data)
        else:
            unresolved.append(record_data)

    return {
        "source_record_count": len(records),
        "compact_records": out,
        "unresolved_records": unresolved,
    }

def generate(check: bool = False) -> dict:
    source_species = symbols(read(SRC_SPECIES), "SPECIES_", enum=True)
    target_species = symbols(read(DST_SPECIES), "SPECIES_")
    source_moves = symbols(read(SRC_MOVES), "MOVE_", enum=True)
    target_moves = symbols(read(DST_MOVES), "MOVE_")
    source_info_text = read(SRC_SPECIES_INFO)
    target_info_text = read(DST_INFO)
    learnsets = extract_learnsets(read(SRC_LEARNSETS))
    type_text, ability_text, item_text = read(DST_POKEMON_CONSTANTS), read(DST_ABILITIES), read(DST_ITEMS)
    info_result = parse_species_info(source_info_text, target_info_text, type_text, ability_text, item_text)

    by_dex = {}
    for item in source_species:
        if 1 <= item["id"] <= 898:
            by_dex.setdefault(item["id"], item["symbol"])
    if sorted(by_dex) != list(range(1, 899)):
        missing = sorted(set(range(1, 899)) - set(by_dex))
        raise RuntimeError(f"National Dex mapping incomplete: {missing}")
    target_by_name = {item["symbol"]: item["id"] for item in target_species}
    species_map = []
    for dex in range(1, 899):
        source_name = by_dex[dex]
        normalized = BASE_ALIASES.get(source_name, source_name)
        emerald_id = target_by_name.get(normalized)
        species_map.append({"national_dex": dex, "source_symbol": source_name,
            "normalized_symbol": normalized, "emerald_internal_id": emerald_id,
            "status": "existing_emerald_species" if emerald_id is not None else "new_species_id_required"})
    existing_count = sum(x["emerald_internal_id"] is not None for x in species_map)
    new_species = [x for x in species_map if x["emerald_internal_id"] is None]
    if existing_count != 386 or len(new_species) != 512:
        raise RuntimeError(f"Unexpected species split: existing={existing_count}, new={len(new_species)}")

    used_moves = sorted({m["move"] for row in learnsets for m in row["moves"]})
    target_move_names = {x["symbol"] for x in target_moves}
    missing_moves = sorted(set(used_moves) - target_move_names)
    source_move_by_name = {}
    for item in source_moves:
        if item["id"] <= 847:
            source_move_by_name.setdefault(item["symbol"], item["id"])
    move_dependencies = [
        {"source_symbol": name, "source_id": source_move_by_name[name],
         "emerald_id": next((m["id"] for m in target_moves if m["symbol"] == name), None),
         "used_by_gen8_learnset": name in used_moves,
         "requires_battle_definition": name not in target_move_names,
         "requires_contest_definition": name not in target_move_names}
        for name in sorted(source_move_by_name) if source_move_by_name[name] > 354
    ]
    counts = {
        "canonical_dex_entries": len(species_map), "existing_species": existing_count,
        "new_species": len(new_species), "source_moves_gen1_8": len({x["id"] for x in source_moves if x["id"] <= 847}),
        "learnset_blocks": len(learnsets), "learnset_move_entries": sum(len(x["moves"]) for x in learnsets),
        "distinct_learnset_moves": len(used_moves), "missing_learnset_moves": len(missing_moves),
        "species_info_blocks": info_result["source_record_count"],
        "species_info_compact_records": len(info_result["compact_records"]),
        "species_info_unresolved_records": len(info_result["unresolved_records"]),
    }
    report = {
        "source": "pinned pokeemerald-expansion source snapshot",
        "scope": "National Dex 1-898 canonical species only",
        "counts": counts,
        "readiness": {
            "canonical_dex_map_complete": True, "existing_species_ids_preserved": True,
            "new_species_ids_allocated": False, "learnsets_parsed_from_expansion_syntax": True,
            "all_learnset_move_symbols_have_emerald_ids": not missing_moves,
            "species_info_compact_stage_generated": len(info_result["compact_records"]) > 0,
            "species_info_complete": False, "save_extension_validated": False,
            "evolutions_ready": False, "pokedex_text_ready": False, "cries_ready": False,
            "graphics_ready": False, "battle_and_contest_moves_ready": False,
            "runtime_ready": False, "num_species_change_allowed": False,
        },
        "species_mapping": species_map,
        "missing_learnset_move_symbols": missing_moves,
        "species_info_compact_summary": counts,
    }
    if not check:
        OUT.mkdir(parents=True, exist_ok=True)
        write_json(OUT / "conversion_report.json", report)
        write_json(OUT / "species_id_mapping.json", species_map)
        write_json(OUT / "new_species_mapping.json", new_species)
        write_json(OUT / "move_dependencies.json", move_dependencies)
        write_json(OUT / "level_up_learnsets.json", learnsets)
        write_json(OUT / "missing_learnset_moves.json", missing_moves)
        write_json(OUT / "species_info_compact.json", info_result)
        with (OUT / "move_dependencies.csv").open("w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=list(move_dependencies[0].keys()))
            writer.writeheader()
            writer.writerows(move_dependencies)
        write(ROOT / "include/gen8_species_map.h", emit_species_header())
        write(ROOT / "src/data/gen8/species_map.c", emit_species_c(species_map))
        write(ROOT / "include/gen8_conversion_status.h", emit_readiness_header(counts))
        write_json(ROOT / "data/pokemon/gen8_species_map.json", species_map)
        write_json(ROOT / "data/pokemon/gen8_level_up_learnsets.json", learnsets)
        # Compact, canonical data table only. It is deliberately not linked into
        # gSpeciesInfo until internal IDs and runtime storage have been assigned.
        write(ROOT / "src/data/gen8/species_info_compact.json.h", json.dumps(info_result["compact_records"], indent=2) + "\n")
    return report

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    try:
        report = generate(check=args.check)
        print(json.dumps(report["counts"], indent=2))
        print("PASS: staging extraction completed; production IDs and save layouts untouched.")
        return 0
    except (OSError, RuntimeError, ValueError, KeyError) as e:
        print(f"GEN8 CONVERSION FAILED: {e}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
