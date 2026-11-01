#!/usr/bin/env python3
"""Build explicit Gen 8 canonical reference tables and runtime blocker audit.

Outputs are source-derived staging data only. This tool never edits production
species IDs, NUM_SPECIES, live runtime tables, or save structures.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
import gen8_convert_emerald as converter  # noqa: E402

REPORTS = ROOT / "reports/gen8-conversion"
OUT = ROOT / "data/pokemon/gen8_reference_tables.json"
REPORT = REPORTS / "pending_tables_report.json"
VENDOR = ROOT / "tools/vendor/pokeemerald-expansion"

REQUIRED_GRAPHICS = (
    "front.png", "anim_front.png", "back.png", "icon.png",
    "footprint.png", "normal.pal", "shiny.pal",
)
TARGET_DIRECT_EVOLUTION_METHODS = {"EVO_LEVEL", "EVO_TRADE", "EVO_ITEM"}


def read(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"Missing required table input: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def numeric(raw):
    if raw is None:
        return None
    value = raw.strip()
    if re.fullmatch(r"(?:0x[0-9A-Fa-f]+|\d+)", value):
        return int(value, 0)
    return None


def literals(raw: str) -> str | None:
    if not raw:
        return None
    found = re.findall(r'"(?:\\.|[^"\\])*"', raw, re.S)
    if not found:
        return None
    try:
        return "".join(ast.literal_eval(token) for token in found)
    except (SyntaxError, ValueError):
        return None


def camel_name(symbol: str) -> str:
    return "".join(part[:1] + part[1:].lower() for part in symbol.split("_") if part)


def balanced_move_records(text: str) -> dict[str, dict]:
    """Read MOVE designated initializer blocks without truncating nested values."""
    start_re = re.compile(r"^\s*\[MOVE_([A-Z0-9_]+)\]\s*=\s*", re.M)
    result = {}
    for match in start_re.finditer(text):
        start = match.end()
        while start < len(text) and text[start].isspace():
            start += 1
        if start >= len(text) or text[start] != "{":
            continue
        depth = 0
        in_string = escaped = False
        i = start
        while i < len(text):
            ch = text[i]
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
            else:
                if ch == '"':
                    in_string = True
                elif ch == "{":
                    depth += 1
                elif ch == "}":
                    depth -= 1
                    if depth == 0:
                        i += 1
                        break
            i += 1
        if depth:
            continue
        body = text[start + 1:i - 1]
        result[match.group(1)] = converter.extract_designated_fields(body)
    return result


def parse_evolution_expression(raw: str | None, target_species: set[str],
                               target_items: dict[str, int]) -> dict:
    if raw is None or raw.strip() in ("", "NULL", "0"):
        return {
            "status": "resolved_no_evolution",
            "source_expression": raw,
            "entries": [],
            "semantic": "C static zero-initialization yields a null evolution pointer",
        }
    match = re.fullmatch(r"\s*EVOLUTION\s*\(([\s\S]*)\)\s*", raw)
    if not match:
        return {
            "status": "unresolved_expression",
            "source_expression": raw,
            "entries": [],
        }

    entries = []
    unparsed = []
    for argument in converter.split_c_arguments(match.group(1)):
        token = argument.strip()
        if not token:
            continue
        if token.startswith("{") and token.endswith("}"):
            parts = converter.split_c_arguments(token[1:-1])
        else:
            parts = converter.split_c_arguments(token)
        if not parts:
            unparsed.append(token)
            continue
        method_match = re.search(r"\b(EVO_[A-Z0-9_]+)\b", parts[0])
        method = method_match.group(1) if method_match else None
        species_match = re.search(r"\bSPECIES_([A-Z0-9_]+)\b", token)
        item_match = re.search(r"\bITEM_([A-Z0-9_]+)\b", token)
        target_symbol = species_match.group(1) if species_match else None
        item_symbol = item_match.group(1) if item_match else None
        extra_conditions = [
            x for x in re.findall(r"\b(?:CONDITIONS|IF_[A-Z0-9_]+|REGION_[A-Z0-9_]+)\b", token)
        ]
        parameter = parts[1].strip() if len(parts) > 1 else None
        if parameter and re.fullmatch(r"SPECIES_[A-Z0-9_]+", parameter):
            parameter = None
        item_target_id = target_items.get(item_symbol) if item_symbol else None
        if method == "EVO_NONE":
            compatibility = "source_form_restriction_not_runtime_evolution"
        elif method in TARGET_DIRECT_EVOLUTION_METHODS and not extra_conditions:
            compatibility = "method_symbol_supported_review_parameter_semantics"
        elif method in TARGET_DIRECT_EVOLUTION_METHODS:
            compatibility = "requires_condition_handler"
        elif method:
            compatibility = "requires_new_target_evolution_handler"
        else:
            compatibility = "unresolved_method"
        entries.append({
            "source_expression": token,
            "method_symbol": method,
            "parameter_expression": parameter,
            "target_species_symbol": target_symbol,
            "target_species_symbol_exists_in_emerald_constants": (
                target_symbol in target_species if target_symbol else None
            ),
            "held_item_symbol": item_symbol,
            "held_item_emerald_id": item_target_id,
            "condition_symbols": extra_conditions,
            "target_compatibility": compatibility,
        })
    if unparsed:
        return {
            "status": "partially_unresolved",
            "source_expression": raw,
            "entries": entries,
            "unparsed_entries": unparsed,
        }
    return {
        "status": "parsed_source_entries",
        "source_expression": raw,
        "entries": entries,
    }


def parse_shared_dex_text(text: str) -> dict[str, str]:
    result = {}
    pattern = re.compile(
        r"const\s+u8\s+([A-Za-z0-9_]+)\s*\[\s*\]\s*=\s*_\s*\(([\s\S]*?)\)\s*;",
        re.M,
    )
    for match in pattern.finditer(text):
        value = literals(match.group(2))
        if value is not None:
            result[match.group(1)] = value
    return result


def main() -> int:
    try:
        canonical = json.loads(read(REPORTS / "species_info_by_national_dex.json"))
        compact = json.loads(read(REPORTS / "species_info_compact.json"))
        learnsets = json.loads(read(REPORTS / "level_up_learnsets.json"))
        conversion = json.loads(read(REPORTS / "conversion_report.json"))
        manifest = json.loads(read(ROOT / "data/pokemon/gen8_species_manifest.json"))

        source_records = compact["compact_records"] + compact["unresolved_records"]
        source_by_symbol = {row["species_symbol"]: row for row in source_records}
        if len(source_by_symbol) != len(source_records):
            raise RuntimeError("Duplicate SpeciesInfo symbols in parsed source inventory")

        source_pokemon = read(VENDOR / "include/constants/pokemon.h")
        source_abilities_text = read(VENDOR / "include/constants/abilities.h")
        source_items_text = read(VENDOR / "include/constants/items.h")
        source_moves_text = read(VENDOR / "include/constants/moves.h")
        source_moves_info_text = read(VENDOR / "src/data/moves_info.h")
        source_cry_text = read(VENDOR / "sound/cry_tables.inc")
        shared_dex_text = read(VENDOR / "src/data/pokemon/species_info/shared_dex_text.h")

        target_pokemon = read(ROOT / "include/constants/pokemon.h")
        target_abilities_text = read(ROOT / "include/constants/abilities.h")
        target_items_text = read(ROOT / "include/constants/items.h")
        target_moves_text = read(ROOT / "include/constants/moves.h")
        target_battle_text = read(ROOT / "src/data/battle_moves.h")
        target_contest_text = read(ROOT / "src/data/contest_moves.h")
        target_cry_text = read(ROOT / "sound/cry_tables.inc")

        source_abilities = {x["symbol"]: x["id"] for x in converter.symbols(source_abilities_text, "ABILITY_", enum=True)}
        target_abilities = {x["symbol"]: x["id"] for x in converter.symbols(target_abilities_text, "ABILITY_")}
        source_items = {x["symbol"]: x["id"] for x in converter.symbols(source_items_text, "ITEM_", enum=True)}
        target_items = {x["symbol"]: x["id"] for x in converter.symbols(target_items_text, "ITEM_")}
        source_types = {x["symbol"]: x["id"] for x in converter.symbols(source_pokemon, "TYPE_", enum=True)}
        target_types = {x["symbol"]: x["id"] for x in converter.symbols(target_pokemon, "TYPE_")}
        source_eggs = {x["symbol"]: x["id"] for x in converter.symbols(source_pokemon, "EGG_GROUP_", enum=True)}
        target_eggs = {x["symbol"]: x["id"] for x in converter.symbols(target_pokemon, "EGG_GROUP_")}
        source_growth = {x["symbol"]: x["id"] for x in converter.symbols(source_pokemon, "GROWTH_", enum=True)}
        target_growth = {x["symbol"]: x["id"] for x in converter.symbols(target_pokemon, "GROWTH_")}
        target_species = {x["symbol"] for x in converter.symbols(read(ROOT / "include/constants/species.h"), "SPECIES_")}
        source_move_ids = {x["symbol"]: x["id"] for x in converter.symbols(source_moves_text, "MOVE_", enum=True)}
        target_move_ids = {x["symbol"]: x["id"] for x in converter.symbols(target_moves_text, "MOVE_")}

        source_move_records = balanced_move_records(source_moves_info_text)
        target_battle_records = set(re.findall(r"\[MOVE_([A-Z0-9_]+)\]\s*=", target_battle_text))
        target_contest_records = set(re.findall(r"\[MOVE_([A-Z0-9_]+)\]\s*=", target_contest_text))
        source_cry_labels = set(re.findall(r"\bCry_[A-Za-z0-9_]+\b", source_cry_text))
        target_cry_labels = set(re.findall(r"\bCry_[A-Za-z0-9_]+\b", target_cry_text))
        shared_texts = parse_shared_dex_text(shared_dex_text)
        dex_to_slug = {
            row["national_dex"]: row["slug"]
            for row in manifest["species"]
        }

        gen8_learnsets = [row for row in learnsets if row.get("generation") == 8]
        learnset_by_species = {}
        for row in gen8_learnsets:
            learnset_by_species.setdefault(row["source_species"], []).append(row)
        used_moves = set()
        species_tables = []
        missing_source_symbols = []
        missing_learnsets = []
        unresolved_evolutions = []
        missing_pokedex_text = []
        missing_cry_refs = []
        missing_graphics_refs = []
        evolution_method_counts = {}
        ability_use_counts = {}
        item_use_counts = {}
        type_use_counts = {}
        egg_use_counts = {}
        growth_use_counts = {}

        for dex_row in canonical:
            dex = dex_row["national_dex"]
            national_symbol = dex_row["national_symbol"]
            source_symbol = national_symbol if national_symbol in source_by_symbol else dex_row["source_record_symbol"]
            source_record = source_by_symbol.get(source_symbol)
            if source_record is None:
                missing_source_symbols.append({"national_dex": dex, "symbol": source_symbol})
                continue
            fields = source_record.get("source_expanded_fields") or source_record.get("resolved_source_fields") or {}
            if not fields:
                missing_source_symbols.append({"national_dex": dex, "symbol": source_symbol, "reason": "no_expanded_fields"})
                continue

            evolution = parse_evolution_expression(fields.get("evolutions"), target_species, target_items)
            if evolution["status"] in ("unresolved_expression", "partially_unresolved"):
                unresolved_evolutions.append(dex)
            for entry in evolution.get("entries", []):
                if entry.get("method_symbol"):
                    key = entry["method_symbol"]
                    evolution_method_counts[key] = evolution_method_counts.get(key, 0) + 1

            name_expr = fields.get("speciesName")
            category_expr = fields.get("categoryName")
            description_expr = fields.get("description")
            description_ref = None
            description_text = literals(description_expr or "")
            if description_text is None and description_expr:
                ref_match = re.fullmatch(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*", description_expr)
                if ref_match:
                    description_ref = ref_match.group(1)
                    description_text = shared_texts.get(description_ref)
            if description_text is None:
                missing_pokedex_text.append(dex)

            cry_expr = fields.get("cryId")
            cry_match = re.search(r"\bCRY_([A-Z0-9_]+)\b", cry_expr or "")
            cry_symbol = cry_match.group(1) if cry_match else None
            cry_label = "Cry_" + camel_name(cry_symbol) if cry_symbol else None
            source_cry_found = cry_label in source_cry_labels if cry_label else False
            target_cry_found = cry_label in target_cry_labels if cry_label else False
            if not cry_symbol or not source_cry_found:
                missing_cry_refs.append(dex)

            slug = dex_to_slug.get(dex)
            graphics_folder = ROOT / "graphics/pokemon" / (slug.replace("-", "_") if slug else "__missing_slug__")
            target_assets = {
                asset: (graphics_folder / asset).is_file()
                for asset in REQUIRED_GRAPHICS
            }
            graphics_refs = {
                key: fields.get(key)
                for key in (
                    "frontPic", "backPic", "iconSprite", "palette", "shinyPalette",
                    "frontAnimFrames", "frontAnimId", "backAnimId", "frontPicSize",
                    "frontPicYOffset", "backPicSize", "backPicYOffset",
                )
            }
            missing_graphics_refs.extend(
                {"national_dex": dex, "field": key}
                for key in ("frontPic", "backPic", "iconSprite", "palette", "shinyPalette")
                if not fields.get(key)
            )

            ability_expr = fields.get("abilities", "")
            ability_names = re.findall(r"\bABILITY_([A-Z0-9_]+)\b", ability_expr)
            ability_names = (ability_names + ["NONE", "NONE", "NONE"])[:3]
            abilities = []
            for name in ability_names:
                if name == "NONE":
                    continue
                ability_use_counts[name] = ability_use_counts.get(name, 0) + 1
                abilities.append({
                    "symbol": name,
                    "source_id": source_abilities.get(name),
                    "emerald_id": target_abilities.get(name),
                    "compatibility": "target_symbol_present_requires_handler_audit" if name in target_abilities else "target_ability_missing",
                })

            held_items = {}
            for field_name, short_name in (("itemCommon", "common"), ("itemRare", "rare")):
                expr = fields.get(field_name)
                match = re.search(r"\bITEM_([A-Z0-9_]+)\b", expr or "")
                name = match.group(1) if match else ("NONE" if expr is None else None)
                if name and name != "NONE":
                    item_use_counts[name] = item_use_counts.get(name, 0) + 1
                held_items[short_name] = {
                    "symbol": name,
                    "source_id": source_items.get(name) if name else None,
                    "emerald_id": target_items.get(name) if name else None,
                    "source_default_none": expr is None,
                    "compatibility": (
                        "target_symbol_present_requires_effect_audit" if name in target_items
                        else "target_item_missing" if name not in (None, "NONE")
                        else "none_or_source_default"
                    ),
                }

            type_names = re.findall(r"\bTYPE_([A-Z0-9_]+)\b", fields.get("types", ""))
            egg_names = re.findall(r"\bEGG_GROUP_([A-Z0-9_]+)\b", fields.get("eggGroups", ""))
            growth_match = re.search(r"\bGROWTH_([A-Z0-9_]+)\b", fields.get("growthRate", ""))
            for name in set(type_names):
                type_use_counts[name] = type_use_counts.get(name, 0) + 1
            for name in set(egg_names):
                egg_use_counts[name] = egg_use_counts.get(name, 0) + 1
            growth_name = growth_match.group(1) if growth_match else None
            if growth_name:
                growth_use_counts[growth_name] = growth_use_counts.get(growth_name, 0) + 1

            base_symbol = converter.BASE_ALIASES.get(national_symbol, national_symbol)
            learnset_key = camel_name(base_symbol)
            candidates = learnset_by_species.get(learnset_key, [])
            chosen_learnset = candidates[0] if candidates else None
            if chosen_learnset is None:
                missing_learnsets.append({"national_dex": dex, "learnset_symbol": learnset_key})
                moves = []
            else:
                moves = chosen_learnset["moves"]
                used_moves.update(move["move"] for move in moves)

            source_fields_present = sorted(fields.keys())
            species_tables.append({
                "national_dex": dex,
                "canonical_symbol": national_symbol,
                "source_record_symbol": source_symbol,
                "source_family_generation": source_record.get("generation"),
                "evolution": evolution,
                "pokedex": {
                    "species_name_expression": name_expr,
                    "species_name_text": literals(name_expr or ""),
                    "category_expression": category_expr,
                    "category_text": literals(category_expr or ""),
                    "height_expression": fields.get("height"),
                    "height_dm": numeric(fields.get("height")),
                    "weight_expression": fields.get("weight"),
                    "weight_hg": numeric(fields.get("weight")),
                    "description_expression": description_expr,
                    "description_reference": description_ref,
                    "description_text": description_text,
                },
                "cry": {
                    "source_expression": cry_expr,
                    "source_symbol": cry_symbol,
                    "expected_assembly_label": cry_label,
                    "source_assembly_label_found": source_cry_found,
                    "emerald_assembly_label_found": target_cry_found,
                    "audio_asset_imported": False,
                },
                "graphics": {
                    "source_references": graphics_refs,
                    "target_folder": str(graphics_folder.relative_to(ROOT)) if slug else None,
                    "target_assets": target_assets,
                    "target_assets_complete": all(target_assets.values()),
                },
                "compatibility": {
                    "types": [
                        {"symbol": name, "source_id": source_types.get(name),
                         "emerald_id": target_types.get(name),
                         "compatibility": "target_symbol_present" if name in target_types else "target_type_missing"}
                        for name in type_names
                    ],
                    "abilities": abilities,
                    "egg_groups": [
                        {"symbol": name, "source_id": source_eggs.get(name),
                         "emerald_id": target_eggs.get(name),
                         "compatibility": "target_symbol_present" if name in target_eggs else "target_egg_group_missing"}
                        for name in egg_names
                    ],
                    "growth_rate": {
                        "symbol": growth_name,
                        "source_id": source_growth.get(growth_name) if growth_name else None,
                        "emerald_id": target_growth.get(growth_name) if growth_name else None,
                        "compatibility": (
                            "target_symbol_present" if growth_name in target_growth
                            else "target_growth_rate_missing" if growth_name else "unresolved"
                        ),
                    },
                    "held_items": held_items,
                },
                "learnset": {
                    "source_generation": 8,
                    "source_symbol": learnset_key,
                    "entry_count": len(moves),
                    "moves": moves,
                },
                "source_fields_present": source_fields_present,
            })

        used_moves = sorted(used_moves)
        move_table = []
        missing_target_move_ids = []
        missing_target_battle = []
        missing_target_contest = []
        for name in used_moves:
            source_id = source_move_ids.get(name)
            target_id = target_move_ids.get(name)
            source_info = source_move_records.get(name, {})
            item = {
                "symbol": name,
                "source_id": source_id,
                "emerald_id": target_id,
                "source_move_info_present": name in source_move_records,
                "target_battle_record_present": name in target_battle_records,
                "target_contest_record_present": name in target_contest_records,
                "source_contest_effect_expression": source_info.get("contestEffect"),
                "source_contest_category_expression": source_info.get("contestCategory"),
                "source_battle_effect_expression": source_info.get("effect"),
                "compatibility": (
                    "target_move_and_battle_and_contest_present"
                    if target_id is not None and name in target_battle_records and name in target_contest_records
                    else "missing_target_move_id" if target_id is None
                    else "missing_target_battle_record" if name not in target_battle_records
                    else "missing_target_contest_record"
                ),
            }
            if target_id is None:
                missing_target_move_ids.append(name)
            if name not in target_battle_records:
                missing_target_battle.append(name)
            if name not in target_contest_records:
                missing_target_contest.append(name)
            move_table.append(item)

        used_abilities = sorted(ability_use_counts)
        missing_target_abilities = [name for name in used_abilities if name not in target_abilities]
        used_items = sorted(item_use_counts)
        missing_target_items = [name for name in used_items if name not in target_items]
        used_types = sorted(type_use_counts)
        missing_target_types = [name for name in used_types if name not in target_types]
        used_eggs = sorted(egg_use_counts)
        missing_target_eggs = [name for name in used_eggs if name not in target_eggs]
        used_growth = sorted(growth_use_counts)
        missing_target_growth = [name for name in used_growth if name not in target_growth]
        all_assets_complete = sum(1 for row in species_tables if row["graphics"]["target_assets_complete"])
        source_pokedex_text_resolved = sum(1 for row in species_tables if row["pokedex"]["description_text"] is not None)
        source_cry_resolved = sum(1 for row in species_tables if row["cry"]["source_assembly_label_found"])
        evolution_entries = sum(len(row["evolution"].get("entries", [])) for row in species_tables)
        evolution_unsupported = sorted({
            entry["method_symbol"]
            for row in species_tables for entry in row["evolution"].get("entries", [])
            if entry.get("target_compatibility") in (
                "requires_new_target_evolution_handler", "requires_condition_handler", "unresolved_method"
            )
        })

        summary = {
            "canonical_species_rows": len(species_tables),
            "canonical_species_expected": 898,
            "missing_source_species_records": missing_source_symbols,
            "gen8_learnset_rows": len(species_tables) - len(missing_learnsets),
            "missing_gen8_learnsets": missing_learnsets,
            "evolution": {
                "rows": len(species_tables),
                "rows_with_source_evolutions": sum(1 for row in species_tables if row["evolution"].get("entries")),
                "parsed_entries": evolution_entries,
                "unresolved_rows": unresolved_evolutions,
                "unsupported_or_conditioned_methods": evolution_unsupported,
                "method_use_counts": evolution_method_counts,
            },
            "pokedex": {
                "rows": len(species_tables),
                "rows_with_category": sum(1 for row in species_tables if row["pokedex"]["category_text"] or row["pokedex"]["category_expression"]),
                "rows_with_species_name": sum(1 for row in species_tables if row["pokedex"]["species_name_text"] or row["pokedex"]["species_name_expression"]),
                "rows_with_description_source": sum(1 for row in species_tables if row["pokedex"]["description_expression"]),
                "descriptions_resolved_to_text": source_pokedex_text_resolved,
                "descriptions_unresolved": missing_pokedex_text,
            },
            "cries": {
                "rows": len(species_tables),
                "source_assembly_labels_resolved": source_cry_resolved,
                "source_assembly_labels_missing": missing_cry_refs,
                "labels_already_present_in_emerald": sum(1 for row in species_tables if row["cry"]["emerald_assembly_label_found"]),
                "audio_assets_imported": False,
            },
            "graphics": {
                "rows": len(species_tables),
                "rows_with_all_target_assets": all_assets_complete,
                "rows_missing_one_or_more_target_assets": len(species_tables) - all_assets_complete,
                "required_asset_names": list(REQUIRED_GRAPHICS),
                "missing_source_graphic_references": missing_graphics_refs,
            },
            "moves": {
                "canonical_learnset_species": len(species_tables) - len(missing_learnsets),
                "unique_moves_used_by_canonical_gen8_learnsets": len(used_moves),
                "source_move_info_rows": sum(1 for row in move_table if row["source_move_info_present"]),
                "missing_target_move_ids": missing_target_move_ids,
                "missing_target_battle_records": missing_target_battle,
                "missing_target_contest_records": missing_target_contest,
            },
            "abilities": {
                "unique_canonical_abilities": len(used_abilities),
                "missing_target_abilities": missing_target_abilities,
                "source_use_counts": ability_use_counts,
            },
            "items": {
                "unique_canonical_held_items": len(used_items),
                "missing_target_items": missing_target_items,
                "source_use_counts": item_use_counts,
            },
            "types": {
                "unique_canonical_types": len(used_types),
                "missing_target_types": missing_target_types,
                "source_use_counts": type_use_counts,
            },
            "egg_groups": {
                "unique_canonical_egg_groups": len(used_eggs),
                "missing_target_egg_groups": missing_target_eggs,
                "source_use_counts": egg_use_counts,
            },
            "growth_rates": {
                "unique_canonical_growth_rates": len(used_growth),
                "missing_target_growth_rates": missing_target_growth,
                "source_use_counts": growth_use_counts,
            },
            "source_info_report": conversion.get("counts", {}),
        }
        source_tables_complete = (
            len(species_tables) == 898
            and not missing_source_symbols
            and not missing_learnsets
            and len([row for row in species_tables if row["pokedex"]["description_expression"]]) == 898
            and len([row for row in species_tables if row["cry"]["source_symbol"]]) == 898
            and len([row for row in species_tables if row["graphics"]["source_references"].get("frontPic")]) == 898
        )
        runtime_tables_ready = (
            source_tables_complete
            and not unresolved_evolutions
            and not missing_target_move_ids
            and not missing_target_battle
            and not missing_target_contest
            and not missing_target_abilities
            and not missing_target_items
            and not missing_target_types
            and not missing_target_eggs
            and not missing_target_growth
            and all_assets_complete == 898
            and source_cry_resolved == 898
            and False  # Audio import and runtime callback audits are separate gates.
        )
        report = {
            "scope": "Canonical National Dex 1-898; Generation 8 data",
            "source_tables_complete": source_tables_complete,
            "runtime_tables_ready": runtime_tables_ready,
            "species_ids_allocated": False,
            "num_species_change_allowed": False,
            "summary": summary,
            "blocking_table_families": [
                "evolution_methods_and_condition_handlers",
                "move_ids_battle_effects_and_contest_effects",
                "abilities_and_execution_handlers",
                "held_items_and_item_effects",
                "fairy_type_and_type_chart",
                "cry_audio_assets_and_target_cry_index",
                "front_back_animation_icon_footprint_palette_assets",
                "save_and_pokedex_runtime_storage",
            ],
        }
        output = {
            "metadata": {
                "source": "pinned pokeemerald-expansion source snapshot",
                "target": "vanilla pokeemerald",
                "canonical_species_count": 898,
                "runtime_ids_assigned": False,
                "num_species_modified": False,
            },
            "species": species_tables,
            "moves": move_table,
            "report": report,
        }
        write_json(OUT, output)
        write_json(REPORT, report)

        print(json.dumps({
            "canonical_species_rows": len(species_tables),
            "source_tables_complete": source_tables_complete,
            "runtime_tables_ready": runtime_tables_ready,
            "gen8_learnset_rows": summary["gen8_learnset_rows"],
            "unique_moves": len(used_moves),
            "missing_move_ids": len(missing_target_move_ids),
            "missing_battle_records": len(missing_target_battle),
            "missing_contest_records": len(missing_target_contest),
            "abilities_missing": len(missing_target_abilities),
            "items_missing": len(missing_target_items),
            "types_missing": len(missing_target_types),
            "evolution_unresolved": len(unresolved_evolutions),
            "pokedex_text_unresolved": len(missing_pokedex_text),
            "cry_refs_unresolved": len(missing_cry_refs),
            "graphics_complete": all_assets_complete,
        }, indent=2))

        if len(species_tables) != 898:
            raise RuntimeError(f"Expected 898 canonical table rows, found {len(species_tables)}")
        if missing_source_symbols:
            raise RuntimeError(f"Missing SpeciesInfo source records: {len(missing_source_symbols)}")
        if missing_learnsets:
            raise RuntimeError(f"Missing canonical Gen 8 learnsets: {len(missing_learnsets)}")
        if not source_tables_complete:
            raise RuntimeError("Canonical source tables are incomplete; inspect pending_tables_report.json")
        print("PASS: generated explicit 898-species source tables; runtime blockers remain separately reported.")
        return 0
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"GEN 8 PENDING TABLE AUDIT FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
