#!/usr/bin/env python3
"""Quantify Gen 8 RAM/save and data compatibility gates without modifying runtime C."""
from __future__ import annotations
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports/gen8-conversion"

def read(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"Missing audit input: {path}")
    return path.read_text(encoding="utf-8")

def block(text: str, name: str) -> str:
    at = text.find(name)
    if at < 0:
        return ""
    start = text.find("{", at)
    depth = 1
    i = start + 1
    while i < len(text) and depth:
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
        i += 1
    return text[at:i]

def struct_size(text: str, fallback: int) -> int:
    match = re.search(r"sizeof:\s*(0x[0-9A-Fa-f]+)", text)
    return int(match.group(1), 16) if match else fallback

def main() -> int:
    global_h = read(ROOT / "include/global.h")
    save_h = read(ROOT / "include/save.h")
    pokemon_constants = read(ROOT / "include/constants/pokemon.h")
    vendor_info_dir = ROOT / "tools/vendor/pokeemerald-expansion/src/data/pokemon/species_info"
    vendor_info_files = sorted(vendor_info_dir.glob("*.h"))
    source_info = "\\n".join(read(path) for path in vendor_info_files)
    if not vendor_info_files:
        raise RuntimeError("No vendored Expansion SpeciesInfo headers found")
    target_info = read(ROOT / "src/data/pokemon/species_info.h")
    source_species = read(ROOT / "tools/vendor/pokeemerald-expansion/include/constants/species.h")
    source_moves = read(ROOT / "tools/vendor/pokeemerald-expansion/include/constants/moves.h")
    source_learn = read(ROOT / "tools/vendor/pokeemerald-expansion/src/data/pokemon/level_up_learnsets/gen_8.h")
    abilities_h = read(ROOT / "include/constants/abilities.h")
    items_h = read(ROOT / "include/constants/items.h")
    cry_table = read(ROOT / "sound/cry_tables.inc")

    save1 = block(global_h, "struct SaveBlock1")
    save2 = block(global_h, "struct SaveBlock2")
    pokedex = block(global_h, "struct Pokedex")
    storage = block(read(ROOT / "include/pokemon_storage_system.h"), "struct PokemonStorage")
    sector_match = re.search(r"#define SECTOR_DATA_SIZE\s+(\d+)", save_h)
    if not sector_match:
        raise RuntimeError("SECTOR_DATA_SIZE not found")
    sector_bytes = int(sector_match.group(1))

    save1_bytes = struct_size(save1, 0x3D88)
    save2_bytes = struct_size(save2, 0xF2C)
    storage_bytes = struct_size(storage, 0x83C3)
    dex_count = 898
    dex_bytes_per_set = (dex_count + 7) // 8
    # The current redundant model has three seen copies and one owned copy:
    # SaveBlock2 seen + SaveBlock2 owned + SaveBlock1 seen1 + seen2.
    required_seen_owned_bytes = 2 * dex_bytes_per_set
    required_total_flag_bytes = 4 * dex_bytes_per_set
    current_species_bytes = 4 * ((412 + 7) // 8)
    reserved = re.search(r"unused_3598\[(0x[0-9A-Fa-f]+)\]", save1)
    reserved_save1_bytes = int(reserved.group(1), 16) if reserved else 0
    if reserved_save1_bytes != 0x180:
        raise RuntimeError(f"Unexpected SaveBlock1 reserved area: {reserved_save1_bytes:#x}")

    source_info_blocks = len(re.findall(r"^\s*\[SPECIES_[A-Z0-9_]+\]\s*=", source_info, re.M))
    source_info_symbols = re.findall(r"^\s*\[SPECIES_([A-Z0-9_]+)\]\s*=", source_info, re.M)
    source_info_unique_symbols = sorted(set(source_info_symbols))
    source_info_duplicate_designators = len(source_info_symbols) - len(source_info_unique_symbols)
    source_fields = set(re.findall(r"^\s*\.([A-Za-z0-9_]+)\s*=", source_info, re.M))
    target_fields = set(re.findall(r"^\s*\.([A-Za-z0-9_]+)\s*=", target_info, re.M))
    missing_fields = sorted(source_fields - target_fields)

    source_move_ids = {
        int(value)
        for value in re.findall(r"^\s*MOVE_[A-Z0-9_]+\s*=\s*(\d+)", source_moves, re.M)
    }
    new_moves_after_gen3 = len({value for value in source_move_ids if 354 < value <= 847})
    learnset_blocks = len(re.findall(
        r"static const struct LevelUpMove s[A-Za-z0-9]+LevelUpLearnset\[\]\s*=",
        source_learn
    ))

    source_abilities = set(re.findall(r"\bABILITY_([A-Z0-9_]+)\b", source_info))
    target_abilities = set(re.findall(r"^#define ABILITY_([A-Z0-9_]+)\s+", abilities_h, re.M))
    source_items = set(re.findall(r"\bITEM_([A-Z0-9_]+)\b", source_info))
    target_items = set(re.findall(r"^\s*ITEM_([A-Z0-9_]+)\s*,", items_h, re.M))
    source_types = set(re.findall(r"\bTYPE_([A-Z0-9_]+)\b", source_info))
    target_types = set(re.findall(r"^#define TYPE_([A-Z0-9_]+)\s+", pokemon_constants, re.M))

    source_cries = set(re.findall(r"\bCRY_([A-Z0-9_]+)\b", source_info))
    target_cries = {name.upper() for name in re.findall(
        r"^\s*cry(?:_reverse)?\s+Cry_([A-Za-z0-9_]+)", cry_table, re.M
    )}

    missing_identifiers = {
        "abilities": sorted(source_abilities - target_abilities),
        "items": sorted(source_items - target_items),
        "types": sorted(source_types - target_types),
    }
    report = {
        "save_layout": {
            "sector_data_bytes": sector_bytes,
            "saveblock1_bytes": save1_bytes,
            "saveblock1_capacity_bytes": 4 * sector_bytes,
            "saveblock1_headroom_bytes": 4 * sector_bytes - save1_bytes,
            "saveblock1_unused_internal_bytes": reserved_save1_bytes,
            "saveblock2_bytes": save2_bytes,
            "saveblock2_capacity_bytes": sector_bytes,
            "saveblock2_headroom_bytes": sector_bytes - save2_bytes,
            "pokemon_storage_bytes": storage_bytes,
            "pokemon_storage_capacity_bytes": 9 * sector_bytes,
            "national_dex_count": dex_count,
            "required_pokedex_flag_bytes_per_set": dex_bytes_per_set,
            "required_seen_owned_flag_bytes": required_seen_owned_bytes,
            "required_total_redundant_flag_bytes": required_total_flag_bytes,
            "current_species_flag_bytes": current_species_bytes,
            "additional_flag_bytes_needed": required_total_flag_bytes - current_species_bytes,
            "single_sector_extension_payload_bytes": sector_bytes - 16,
            "double_buffer_extension_bytes": 2 * (required_total_flag_bytes + 16),
            "saveblock1_candidate_extension_capacity_bytes": reserved_save1_bytes,
            "pokedex_struct_bytes": 0x78,
            "note": (
                "SaveBlock1 and SaveBlock2 are sector-bounded. Sectors 30 and 31 are "
                "currently reserved for Trainer Hill and Recorded Battle. No sector "
                "allocation is changed by this audit."
            ),
        },
        "source_inventory": {
            "vendored_species_info_files": [path.name for path in vendor_info_files],
            "vendored_species_info_file_count": len(vendor_info_files),
            "gen8_species_info_unique_symbol_count": len(source_info_unique_symbols),
            "gen8_species_info_duplicate_designators": source_info_duplicate_designators,
        },
        "data": {
            "vendored_species_info_files": [path.name for path in vendor_info_files],
            "gen8_species_info_records": source_info_blocks,
            "unique_gen8_species_info_species": len(source_info_unique_symbols),
            "duplicate_gen8_species_info_designators": source_info_duplicate_designators,
            "species_info_symbols_sample": source_info_unique_symbols[:12],
            "species_info_fields_not_in_vanilla": missing_fields,
            "new_moves_after_gen3_through_gen8": new_moves_after_gen3,
            "learnset_blocks": learnset_blocks,
            "missing_abilities": missing_identifiers["abilities"],
            "missing_items": missing_identifiers["items"],
            "missing_types": missing_identifiers["types"],
            "source_cry_ids": len(source_cries),
            "matching_cry_names": len(source_cries & target_cries),
            "unmatched_cry_ids": sorted(source_cries - target_cries),
        },
        "readiness": {
            "save_extension_sector_plan_validated": False,
            "save_extension_read_write_tests": False,
            "species_info_complete": False,
            "species_info_source_coverage_proven": False,
            "abilities_complete": not missing_identifiers["abilities"],
            "held_items_complete": not missing_identifiers["items"],
            "types_complete": not missing_identifiers["types"],
            "battle_and_contest_moves_complete": False,
            "evolutions_complete": False,
            "pokedex_text_complete": False,
            "cries_complete": False,
            "graphics_complete": False,
            "runtime_ready": False,
            "num_species_change_allowed": False,
        },
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "storage_architecture_audit.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "save_layout": report["save_layout"],
        "data_summary": {
            "gen8_species_info_records": source_info_blocks,
            "new_moves_after_gen3_through_gen8": new_moves_after_gen3,
            "learnset_blocks": learnset_blocks,
            "missing_abilities": len(missing_identifiers["abilities"]),
            "missing_items": len(missing_identifiers["items"]),
            "missing_types": len(missing_identifiers["types"]),
            "source_cry_ids": len(source_cries),
            "matching_cry_names": len(source_cries & target_cries),
        },
        "readiness": report["readiness"],
    }, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
