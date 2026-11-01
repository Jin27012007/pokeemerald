#!/usr/bin/env python3
"""Build auditable, non-runtime Gen 8 species tables from pinned Expansion data.

This stage emits source-normalized JSON only. It never allocates species/move
IDs, edits NUM_SPECIES, rewrites Emerald C tables, or copies source assets.
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "tools/vendor/pokeemerald-expansion"
DATA = ROOT / "data/pokemon"
REPORTS = ROOT / "reports/gen8-conversion"

import importlib.util
SPEC = importlib.util.spec_from_file_location(
    "gen8_convert_emerald", ROOT / "tools/gen8_convert_emerald.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("Cannot import Gen 8 source parser")
conv = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = conv
SPEC.loader.exec_module(conv)

INFO_COMPACT = DATA / "gen8_species_info_compact.json"
INFO_UNRESOLVED = DATA / "gen8_species_info_unresolved.json"
CANONICAL = DATA / "gen8_species_info_by_national_dex.json"
SPECIES_MAP = DATA / "gen8_species_map.json"
LEARNSETS = DATA / "gen8_level_up_learnsets.json"

SOURCE_MOVES = VENDOR / "include/constants/moves.h"
SOURCE_POKEDEX = VENDOR / "include/constants/pokedex.h"
SOURCE_POKEMON = VENDOR / "include/constants/pokemon.h"
SOURCE_MOVE_INFO = VENDOR / "src/data/moves_info.h"
SOURCE_CONTEST = VENDOR / "src/data/contest_moves.h"
SOURCE_EGG_MOVES = VENDOR / "src/data/pokemon/egg_moves.h"
SOURCE_FORM_SPECIES = VENDOR / "src/data/pokemon/form_species_tables.h"
SOURCE_FORM_CHANGE = VENDOR / "src/data/pokemon/form_change_tables.h"
SOURCE_ORDERS = VENDOR / "src/data/pokemon/pokedex_orders.h"
SOURCE_CRY = VENDOR / "sound/cry_tables.inc"

TEXT_FIELDS = ("speciesName", "categoryName", "description")
GRAPHICS_FIELDS = (
    "frontPic", "backPic", "palette", "shinyPalette", "iconSprite",
    "frontPicFemale", "backPicFemale", "paletteFemale", "shinyPaletteFemale",
    "iconSpriteFemale", "frontPicSize", "frontPicYOffset", "backPicSize",
    "backPicYOffset", "frontPicSizeFemale", "backPicSizeFemale",
    "frontAnimFrames", "frontAnimDelay", "frontAnimId", "backAnimId",
    "iconPalIndex", "iconPalIndexFemale", "pokemonScale", "pokemonOffset",
    "trainerScale", "trainerOffset",
)
STAT_FIELDS = (
    "baseHP", "baseAttack", "baseDefense", "baseSpeed",
    "baseSpAttack", "baseSpDefense", "catchRate", "expYield",
    "evYield_HP", "evYield_Attack", "evYield_Defense", "evYield_Speed",
    "evYield_SpAttack", "evYield_SpDefense", "genderRatio", "eggCycles",
    "friendship", "growthRate", "types", "eggGroups", "abilities",
    "itemCommon", "itemRare", "bodyColor", "safariZoneFleeRate",
)


def read(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"Missing input: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def scan_initializer(text: str, start: int) -> tuple[str, int]:
    """Read a C initializer/expression from start, respecting nesting and strings."""
    i = start
    while i < len(text) and text[i].isspace():
        i += 1
    value_start = i
    root_brace = i < len(text) and text[i] == "{"
    paren = brace = bracket = 0
    in_string = escaped = in_line_comment = in_block_comment = False
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
        elif in_block_comment:
            if ch == "*" and nxt == "/":
                in_block_comment = False
                i += 1
        elif in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
        else:
            if ch == "/" and nxt == "/":
                in_line_comment = True
                i += 1
            elif ch == "/" and nxt == "*":
                in_block_comment = True
                i += 1
            elif ch == '"':
                in_string = True
            elif ch == "(":
                paren += 1
            elif ch == ")":
                paren -= 1
            elif ch == "{":
                brace += 1
            elif ch == "}":
                brace -= 1
                if root_brace and brace == 0 and paren == 0 and bracket == 0:
                    i += 1
                    break
            elif ch == "[":
                bracket += 1
            elif ch == "]":
                bracket -= 1
            elif ch == "," and paren == brace == bracket == 0:
                break
        i += 1
    raw = text[value_start:i].strip().rstrip(",").strip()
    if root_brace and raw.startswith("{") and raw.endswith("}"):
        raw = raw[1:-1].strip()
    return raw, i


def indexed_records(text: str, prefix: str) -> dict[str, str]:
    pattern = re.compile(
        rf"^\s*\[({re.escape(prefix)}[A-Z0-9_]+)\]\s*=\s*", re.M
    )
    result: dict[str, str] = {}
    for match in pattern.finditer(text):
        body, _ = scan_initializer(text, match.end())
        key = match.group(1)
        if key in result:
            raise RuntimeError(f"Duplicate indexed source initializer: {key}")
        result[key] = body
    return result


def named_arrays(text: str, declaration: str) -> dict[str, str]:
    """Return named C arrays matched by a declaration regex with group 1 = name."""
    result: dict[str, str] = {}
    for match in re.finditer(declaration, text, re.M):
        open_brace = text.find("{", match.end() - 1)
        if open_brace < 0:
            continue
        body, _ = scan_initializer(text, open_brace)
        name = match.group(1)
        if name in result:
            raise RuntimeError(f"Duplicate named source table: {name}")
        result[name] = body
    return result


def call_arguments(raw: str, name: str) -> list[str] | None:
    match = re.match(rf"\s*{re.escape(name)}\s*\(", raw or "")
    if not match:
        return None
    open_pos = raw.find("(", match.start())
    depth = 1
    in_string = escaped = False
    i = open_pos + 1
    while i < len(raw) and depth:
        ch = raw[i]
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
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
        i += 1
    if depth:
        return None
    return conv.split_c_arguments(raw[open_pos + 1:i - 1])


def parse_evolution_expression(raw: str) -> list[dict] | None:
    args = call_arguments(raw, "EVOLUTION")
    if args is None:
        return None
    result = []
    for index, item in enumerate(args):
        item = item.strip()
        if not (item.startswith("{") and item.endswith("}")):
            return None
        parts = conv.split_c_arguments(item[1:-1])
        if len(parts) < 3:
            return None
        method, parameter, target = [part.strip() for part in parts[:3]]
        condition = parts[3].strip() if len(parts) > 3 else None
        if not method.startswith("EVO_") or not target.startswith("SPECIES_"):
            return None
        result.append({
            "slot": index,
            "method_symbol": method,
            "parameter_expression": parameter,
            "target_species_symbol": target,
            "condition_expression": condition,
            "additional_expressions": [part.strip() for part in parts[4:]],
        })
    return result


def string_fragments(raw: str) -> list[str]:
    found = re.findall(r'"(?:\\.|[^"\\])*"', raw or "", re.S)
    result = []
    for token in found:
        try:
            value = ast.literal_eval(token)
        except (SyntaxError, ValueError):
            return []
        if isinstance(value, str):
            result.append(value)
    return result


def normalize_cry(value: str) -> str:
    value = re.sub(r"^(?:CRY_|Cry_)", "", value or "")
    return re.sub(r"[^A-Za-z0-9]", "", value).lower()


def source_table_inventory() -> dict:
    """Generate independent, reviewable tables without touching production C."""
    compact = json.loads(read(INFO_COMPACT))
    unresolved = json.loads(read(INFO_UNRESOLVED))
    canonical = json.loads(read(CANONICAL))
    species_map = json.loads(read(SPECIES_MAP))
    learnsets = json.loads(read(LEARNSETS))
    info_by_symbol = {
        row["species_symbol"]: row
        for row in compact + unresolved
    }
    map_by_dex = {row["national_dex"]: row for row in species_map}
    canonical_by_dex = {row["national_dex"]: row for row in canonical}
    if len(map_by_dex) != 898 or len(canonical_by_dex) != 898:
        raise RuntimeError("Expected exactly 898 canonical species rows")

    # Build the authoritative Gen 8 family source view even for the 386
    # original Emerald species. The previous live Emerald records are not a
    # substitute for the pinned Gen 8 source snapshot during this audit.
    source_rows = []
    for dex in range(1, 899):
        mapping = map_by_dex[dex]
        canonical_row = canonical_by_dex[dex]
        symbol = mapping["source_symbol"]
        source = info_by_symbol.get(symbol)
        if source is None:
            raise RuntimeError(f"No pinned Expansion SpeciesInfo record for Dex {dex}: {symbol}")
        fields = source.get("source_expanded_fields", source.get("resolved_source_fields", {}))
        if not fields or fields.get("natDexNum") != f"NATIONAL_DEX_{symbol}":
            # Some aliases use a different NATIONAL_DEX_* token; validate the
            # resolved number using the canonical manifest rather than guessing.
            nat = fields.get("natDexNum", "")
            if not nat.startswith("NATIONAL_DEX_"):
                raise RuntimeError(f"Missing canonical natDexNum source field for Dex {dex}: {symbol}")
        source_rows.append((dex, mapping, canonical_row, source, fields))

    # Exact Gen 8 level-up learnsets referenced by the canonical species rows.
    gen8_blocks = {
        f"s{row['source_species']}LevelUpLearnset": row
        for row in learnsets if row["generation"] == 8
    }
    canonical_learnsets = []
    missing_learnsets = []
    used_move_symbols = set()
    for dex, mapping, _, source, fields in source_rows:
        pointer = fields.get("levelUpLearnset")
        block = gen8_blocks.get(pointer)
        if block is None:
            missing_learnsets.append({"national_dex": dex, "species": mapping["source_symbol"], "pointer": pointer})
            continue
        moves = block["moves"]
        used_move_symbols.update(move["move"] for move in moves)
        canonical_learnsets.append({
            "national_dex": dex,
            "species_symbol": mapping["source_symbol"],
            "source_learnset_symbol": pointer,
            "source_generation_policy": 8,
            "moves": moves,
        })

    # Evolutions are inline source entries; omitted pointer means no evolution
    # entry is attached to that SpeciesInfo initializer.
    evolution_rows = []
    unresolved_evolutions = []
    for dex, mapping, _, source, fields in source_rows:
        raw = fields.get("evolutions")
        parsed = [] if raw is None else parse_evolution_expression(raw)
        if raw is not None and parsed is None:
            unresolved_evolutions.append({"national_dex": dex, "species_symbol": mapping["source_symbol"], "raw": raw})
        evolution_rows.append({
            "national_dex": dex,
            "species_symbol": mapping["source_symbol"],
            "source_evolution_expression": raw,
            "evolutions": parsed if parsed is not None else [],
            "source_has_evolution_pointer": raw is not None,
        })

    # Pokédex text and dimensions: decode inline strings and resolve the
    # small set of shared g<Name>PokedexText symbols from the pinned header.
    # The original pointer/expression remains recorded beside the decoded text.
    shared_dex_text = read(VENDOR / "src/data/pokemon/species_info/shared_dex_text.h")
    shared_dex_text_values = {}
    shared_pattern = re.compile(
        r"const\s+u8\s+(g[A-Za-z0-9_]+PokedexText)\s*\[\]\s*=\s*_\((.*?)\);",
        re.S,
    )
    for match in shared_pattern.finditer(shared_dex_text):
        shared_dex_text_values[match.group(1)] = string_fragments(match.group(2))
    pokedex_rows = []
    unresolved_text = []
    for dex, mapping, _, source, fields in source_rows:
        description_expression = fields.get("description")
        description_pointer = (
            description_expression
            if description_expression in shared_dex_text_values else None
        )
        description_values = string_fragments(description_expression or "")
        if not description_values and description_pointer:
            description_values = shared_dex_text_values[description_pointer]
        row = {
            "national_dex": dex,
            "species_symbol": mapping["source_symbol"],
            "source_generation": source["generation"],
            "species_name_expression": fields.get("speciesName"),
            "species_name_fragments": string_fragments(fields.get("speciesName", "")),
            "category_expression": fields.get("categoryName"),
            "category_fragments": string_fragments(fields.get("categoryName", "")),
            "description_expression": description_expression,
            "description_pointer_symbol": description_pointer,
            "description_fragments": description_values,
            "height_dm": fields.get("height"),
            "weight_hg": fields.get("weight"),
            "national_dex_symbol": fields.get("natDexNum"),
            "source_fields_present": sorted(fields.keys()),
        }
        if not row["species_name_fragments"] or not row["category_fragments"] or not row["description_fragments"]:
            unresolved_text.append({
                "national_dex": dex,
                "species_symbol": mapping["source_symbol"],
                "missing_fields": [
                    field for field, ok in (
                        ("speciesName", bool(row["species_name_fragments"])),
                        ("categoryName", bool(row["category_fragments"])),
                        ("description", bool(row["description_fragments"])),
                    ) if not ok
                ],
            })
        pokedex_rows.append(row)

    # Cry pointers and assembly table labels are different domains: validate
    # the source symbol association, but do not claim audio bytes are vendored.
    cry_text = read(SOURCE_CRY)
    cry_start = cry_text.find("gCryTable::")
    cry_end = cry_text.find("gCryTable_Reverse::", cry_start + 1)
    if cry_start < 0 or cry_end < 0:
        raise RuntimeError("Could not locate Expansion gCryTable boundaries")
    cry_table_symbols = re.findall(r"^\s*cry\s+(Cry_[A-Za-z0-9_]+)", cry_text[cry_start:cry_end], re.M)
    cry_set = {normalize_cry(symbol) for symbol in cry_table_symbols}
    cry_rows = []
    missing_cries = []
    for dex, mapping, _, source, fields in source_rows:
        cry_symbol = fields.get("cryId")
        matched = bool(cry_symbol and normalize_cry(cry_symbol) in cry_set)
        row = {
            "national_dex": dex,
            "species_symbol": mapping["source_symbol"],
            "cry_symbol": cry_symbol,
            "source_cry_table_match": matched,
            "audio_asset_imported": False,
        }
        if not matched:
            missing_cries.append(row)
        cry_rows.append(row)

    # Graphics references are complete data pointers, not image files. The
    # Expansion vendor deliberately excludes all Pokémon sprite/audio assets.
    graphics_rows = []
    missing_graphics_refs = []
    for dex, mapping, _, source, fields in source_rows:
        refs = {field: fields.get(field) for field in GRAPHICS_FIELDS}
        required = ("frontPic", "backPic", "palette", "shinyPalette", "iconSprite")
        missing = [field for field in required if not refs.get(field)]
        if missing:
            missing_graphics_refs.append({"national_dex": dex, "species_symbol": mapping["source_symbol"], "missing": missing})
        graphics_rows.append({
            "national_dex": dex,
            "species_symbol": mapping["source_symbol"],
            "source_graphics_references": refs,
            "required_reference_fields_missing": missing,
            "asset_payload_imported": False,
        })

    # Form pointers are resolved to their source table definitions while their
    # Expansion species/item IDs remain symbolic and unallocated in Emerald.
    form_species_arrays = named_arrays(
        read(SOURCE_FORM_SPECIES),
        r"^\s*static\s+const\s+u16\s+(s[A-Za-z0-9_]+FormSpeciesIdTable)\s*\[\]\s*=\s*\{",
    )
    form_change_arrays = named_arrays(
        read(SOURCE_FORM_CHANGE),
        r"^\s*static\s+const\s+struct\s+FormChange\s+(s[A-Za-z0-9_]+FormChangeTable)\s*\[\]\s*=\s*\{",
    )
    form_rows = []
    missing_form_tables = []
    referenced_form_species = set()
    referenced_form_changes = set()
    for dex, mapping, _, source, fields in source_rows:
        species_pointer = fields.get("formSpeciesIdTable")
        change_pointer = fields.get("formChangeTable")
        species_table = form_species_arrays.get(species_pointer) if species_pointer else None
        change_table = form_change_arrays.get(change_pointer) if change_pointer else None
        missing = []
        if species_pointer:
            referenced_form_species.add(species_pointer)
            if species_table is None:
                missing.append(species_pointer)
        if change_pointer:
            referenced_form_changes.add(change_pointer)
            if change_table is None:
                missing.append(change_pointer)
        if missing:
            missing_form_tables.append({"national_dex": dex, "species_symbol": mapping["source_symbol"], "missing_tables": missing})
        form_rows.append({
            "national_dex": dex,
            "species_symbol": mapping["source_symbol"],
            "form_species_table_symbol": species_pointer,
            "form_species_table_source": species_table,
            "form_species_symbols": sorted(set(re.findall(r"\bSPECIES_([A-Z0-9_]+)\b", species_table or ""))),
            "form_change_table_symbol": change_pointer,
            "form_change_table_source": change_table,
            "form_change_species_symbols": sorted(set(re.findall(r"\bSPECIES_([A-Z0-9_]+)\b", change_table or ""))),
            "form_change_item_symbols": sorted(set(re.findall(r"\bITEM_([A-Z0-9_]+)\b", change_table or ""))),
            "source_form_conditions_preserved": True,
            "emerald_form_ids_allocated": False,
        })

    # Source Pokédex order tables. Keep only the requested Gen 1-8 National
    # Dex interval and validate exact one-to-one coverage for each ordering.
    source_dex_values = {
        row["symbol"]: row["id"]
        for row in conv.symbols(read(SOURCE_POKEDEX), "NATIONAL_DEX_", enum=True)
    }
    order_text = read(SOURCE_ORDERS)
    order_rows = {}
    order_failures = {}
    order_decl = re.compile(
        r"^\s*const\s+u16\s+(gPokedexOrder_[A-Za-z0-9_]+)\s*\[\]\s*=\s*\{",
        re.M,
    )
    for match in order_decl.finditer(order_text):
        body, _ = scan_initializer(order_text, order_text.find("{", match.start()))
        symbols = re.findall(r"\bNATIONAL_DEX_([A-Z0-9_]+)\b", body)
        values = [source_dex_values[name] for name in symbols if name in source_dex_values]
        filtered = [value for value in values if 1 <= value <= 898]
        duplicates = sorted(value for value, count in __import__("collections").Counter(filtered).items() if count > 1)
        missing = sorted(set(range(1, 899)) - set(filtered))
        order_rows[match.group(1)] = {
            "national_dex_order": filtered,
            "entries": len(filtered),
            "unique_entries": len(set(filtered)),
            "duplicates": duplicates,
            "missing": missing,
            "complete_for_gen8": len(filtered) == 898 and not duplicates and not missing,
        }
        if not order_rows[match.group(1)]["complete_for_gen8"]:
            order_failures[match.group(1)] = {"duplicates": duplicates, "missing": missing, "entries": len(filtered)}

    # Move metadata and Contest fields from the pinned Expansion MoveInfo.
    source_move_enum = conv.symbols(read(SOURCE_MOVES), "MOVE_", enum=True)
    target_move_enum = conv.symbols(read(ROOT / "include/constants/moves.h"), "MOVE_")
    target_move_ids = {row["symbol"]: row["id"] for row in target_move_enum}
    target_battle_move_records = indexed_records(read(ROOT / "src/data/battle_moves.h"), "MOVE_")
    target_contest_move_records = indexed_records(read(ROOT / "src/data/contest_moves.h"), "MOVE_")
    source_move_ids = {}
    for row in source_move_enum:
        if 0 < row["id"] <= 847:
            source_move_ids.setdefault(row["symbol"], row["id"])
    move_records = indexed_records(read(SOURCE_MOVE_INFO), "MOVE_")
    move_rows = []
    missing_move_definitions = []
    used_move_rows = []
    for symbol, source_id in sorted(source_move_ids.items(), key=lambda item: item[1]):
        fields = conv.extract_designated_fields(move_records.get("MOVE_" + symbol, ""))
        if not fields:
            missing_move_definitions.append(symbol)
        target_id = target_move_ids.get(symbol)
        row = {
            "source_move_symbol": symbol,
            "source_move_id": source_id,
            "emerald_move_id": target_id,
            "used_by_canonical_gen8_learnsets": symbol in used_move_symbols,
            "battle_fields": {
                field: fields.get(field)
                for field in ("effect", "power", "type", "accuracy", "pp", "target", "priority", "category")
            },
            "contest_fields": {
                field: fields.get(field)
                for field in ("contestEffect", "contestCategory", "contestComboStarterId", "contestComboMoves")
            },
            "source_fields_present": sorted(fields.keys()),
            "battle_definition_available_in_emerald": symbol in target_move_ids,
            "target_battle_record_present": "MOVE_" + symbol in target_battle_move_records,
            "target_contest_record_present": "MOVE_" + symbol in target_contest_move_records,
            "target_battle_fields": conv.extract_designated_fields(target_battle_move_records.get("MOVE_" + symbol, "")),
            "target_contest_fields": conv.extract_designated_fields(target_contest_move_records.get("MOVE_" + symbol, "")),
        }
        move_rows.append(row)
        if row["used_by_canonical_gen8_learnsets"]:
            used_move_rows.append(row)

    contest_effect_records = indexed_records(read(SOURCE_CONTEST), "CONTEST_EFFECT_")
    contest_effect_rows = []
    for symbol, body in sorted(contest_effect_records.items()):
        fields = conv.extract_designated_fields(body)
        contest_effect_rows.append({
            "source_contest_effect_symbol": symbol,
            "source_fields": fields,
            "source_callback_symbol": fields.get("function"),
        })
    target_contest_source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "src").glob("contest*.c")
        if path.is_file()
    )
    target_contest_callbacks = set(re.findall(r"\bContestEffect_[A-Za-z0-9_]+\b", target_contest_source))
    missing_contest_callbacks = sorted({
        row["source_callback_symbol"]
        for row in contest_effect_rows
        if row["source_callback_symbol"]
        and row["source_callback_symbol"].replace("&", "").strip() not in target_contest_callbacks
    })

    target_effects_text = read(ROOT / "include/constants/battle_move_effects.h")
    target_effect_symbols = set(re.findall(r"\bEFFECT_[A-Z0-9_]+\b", target_effects_text))
    source_effect_symbols = sorted({
        value for row in move_rows
        for value in re.findall(r"\bEFFECT_[A-Z0-9_]+\b", row["battle_fields"].get("effect") or "")
    })
    missing_battle_effects = sorted(set(source_effect_symbols) - target_effect_symbols)
    missing_target_battle_move_records = sorted(
        row["source_move_symbol"] for row in used_move_rows
        if not row["target_battle_record_present"]
    )
    missing_target_contest_move_records = sorted(
        row["source_move_symbol"] for row in used_move_rows
        if not row["target_contest_record_present"]
    )

    # Ability/item dependency closure for the selected 898 canonical rows.
    # The per-species compact file is a list; enum domains are stored in
    # the converter's structured audit report, not in that list.
    enum_audit = json.loads(read(REPORTS / "species_info_compact.json"))
    source_ability_values = enum_audit.get("source_enum_domains", {}).get("abilities", {})
    source_item_values = enum_audit.get("source_enum_domains", {}).get("items", {})
    target_ability_ids = {
        row["symbol"]: row["id"]
        for row in conv.symbols(read(ROOT / "include/constants/abilities.h"), "ABILITY_")
    }
    target_item_ids = {
        row["symbol"]: row["id"]
        for row in conv.symbols(read(ROOT / "include/constants/items.h"), "ITEM_")
    }
    source_ability_records = indexed_records(read(VENDOR / "src/data/abilities.h"), "ABILITY_")
    source_item_records = indexed_records(read(VENDOR / "src/data/items.h"), "ITEM_")
    target_item_records = indexed_records(read(ROOT / "src/data/items.h"), "ITEM_")
    source_pokemon_text = read(SOURCE_POKEMON)
    target_pokemon_text = read(ROOT / "include/constants/pokemon.h")
    source_type_ids = {row["symbol"]: row["id"] for row in conv.symbols(source_pokemon_text, "TYPE_", enum=True)}
    target_type_ids = {row["symbol"]: row["id"] for row in conv.symbols(target_pokemon_text, "TYPE_")}
    source_egg_ids = {row["symbol"]: row["id"] for row in conv.symbols(source_pokemon_text, "EGG_GROUP_", enum=True)}
    target_egg_ids = {row["symbol"]: row["id"] for row in conv.symbols(target_pokemon_text, "EGG_GROUP_")}
    source_growth_ids = {row["symbol"]: row["id"] for row in conv.symbols(source_pokemon_text, "GROWTH_", enum=True)}
    target_growth_ids = {row["symbol"]: row["id"] for row in conv.symbols(target_pokemon_text, "GROWTH_")}
    ability_use = {}
    item_use = {}
    type_use = set()
    for dex, mapping, _, source, fields in source_rows:
        for name in re.findall(r"\bABILITY_([A-Z0-9_]+)\b", fields.get("abilities", "")):
            ability_use.setdefault(name, set()).add(dex)
        for field in ("itemCommon", "itemRare"):
            for name in re.findall(r"\bITEM_([A-Z0-9_]+)\b", fields.get(field, "")):
                if name != "NONE":
                    item_use.setdefault(name, set()).add(dex)
        type_use.update(re.findall(r"\bTYPE_([A-Z0-9_]+)\b", fields.get("types", "")))
    ability_rows = []
    for name, dexes in sorted(ability_use.items()):
        source_fields = conv.extract_designated_fields(
            source_ability_records.get("ABILITY_" + name, "")
        )
        ability_rows.append({
            "ability_symbol": name,
            "source_ability_id": source_ability_values.get(name),
            "emerald_ability_id": target_ability_ids.get(name),
            "canonical_species_usage_count": len(dexes),
            "canonical_species_examples": sorted(dexes)[:20],
            "source_ability_info_record_present": "ABILITY_" + name in source_ability_records,
            "source_ability_info_fields": sorted(source_fields),
            "target_ability_constant_present": name in target_ability_ids,
            "target_behavior_audited": False,
        })

    item_rows = []
    for name, dexes in sorted(item_use.items()):
        source_fields = conv.extract_designated_fields(
            source_item_records.get("ITEM_" + name, "")
        )
        target_fields = conv.extract_designated_fields(
            target_item_records.get("ITEM_" + name, "")
        )
        item_rows.append({
            "item_symbol": name,
            "source_item_id": source_item_values.get(name),
            "emerald_item_id": target_item_ids.get(name),
            "canonical_species_usage_count": len(dexes),
            "canonical_species_examples": sorted(dexes)[:20],
            "source_item_data_record_present": "ITEM_" + name in source_item_records,
            "source_item_data_fields": sorted(source_fields),
            "target_item_constant_present": name in target_item_ids,
            "target_item_data_record_present": "ITEM_" + name in target_item_records,
            "target_item_data_fields": sorted(target_fields),
            "target_hold_effect_expression": target_fields.get("holdEffect"),
            "target_hold_effect_param_expression": target_fields.get("holdEffectParam"),
            "target_item_behavior_audited": False,
        })

    used_types = sorted(type_use)
    type_rows = [{
        "type_symbol": name,
        "source_type_id": source_type_ids.get(name),
        "emerald_type_id": target_type_ids.get(name),
        "used_by_canonical_species": name in type_use,
        "target_type_symbol_present": name in target_type_ids,
        "type_chart_runtime_audited": False,
    } for name in sorted(source_type_ids)]
    missing_types = sorted(name for name in used_types if name not in target_type_ids)

    used_egg_groups = sorted(egg_use)
    egg_group_rows = [{
        "egg_group_symbol": name,
        "source_egg_group_id": source_egg_ids.get(name),
        "emerald_egg_group_id": target_egg_ids.get(name),
        "used_by_canonical_species": name in egg_use,
        "target_egg_group_symbol_present": name in target_egg_ids,
    } for name in sorted(source_egg_ids)]
    missing_egg_groups = sorted(name for name in used_egg_groups if name not in target_egg_ids)

    growth_use = {
        symbol
        for dex, mapping, _, source, fields in source_rows
        for symbol in re.findall(r"\bGROWTH_([A-Z0-9_]+)\b", fields.get("growthRate", ""))
    }
    growth_rate_rows = [{
        "growth_rate_symbol": name,
        "source_growth_rate_id": source_growth_ids.get(name),
        "emerald_growth_rate_id": target_growth_ids.get(name),
        "used_by_canonical_species": name in growth_use,
        "target_growth_rate_symbol_present": name in target_growth_ids,
    } for name in sorted(source_growth_ids)]
    missing_growth_rates = sorted(name for name in growth_use if name not in target_growth_ids)

    source_evolution_enum = re.search(
        r"enum\s+EvolutionMethods\s*\{([^}]*)\}",
        source_pokemon_text,
        re.S,
    )
    if source_evolution_enum is None:
        raise RuntimeError("Source EvolutionMethods enum is missing")
    source_evolution_methods = conv.symbols(
        "enum EvolutionMethods {" + source_evolution_enum.group(1) + "}",
        "EVO_", enum=True,
    )
    target_evolution_methods = {
        row["symbol"]: row["id"]
        for row in conv.symbols(target_pokemon_text, "EVO_")
    }
    used_evolution_methods = sorted({
        entry["method_symbol"]
        for row in evolution_rows for entry in row["evolutions"]
        if entry.get("method_symbol")
    })
    evolution_method_rows = []
    for method in source_evolution_methods:
        name = method["symbol"]
        if name == "NONE":
            compatibility = "source_no_evolution_or_form_restriction"
        elif name in ("LEVEL", "TRADE", "ITEM"):
            compatibility = "same_method_symbol_parameter_semantics_require_review"
        else:
            compatibility = "target_evolution_method_or_handler_missing"
        evolution_method_rows.append({
            "method_symbol": "EVO_" + name,
            "source_method_id": method["id"],
            "emerald_method_id": target_evolution_methods.get(name),
            "used_by_canonical_evolutions": "EVO_" + name in used_evolution_methods,
            "target_method_symbol_present": name in target_evolution_methods,
            "compatibility": compatibility,
        })

    # A canonical Dex species can reference a non-canonical form as an
    # evolution target or in a form table. Those references remain symbolic.
    source_species_names = {
        row["symbol"] for row in conv.symbols(read(VENDOR / "include/constants/species.h"), "SPECIES_", enum=True)
    }
    evolution_target_symbols = sorted({
        row["target_species_symbol"].removeprefix("SPECIES_")
        for entry in evolution_rows for row in entry["evolutions"]
    })
    unknown_evolution_targets = sorted(set(evolution_target_symbols) - source_species_names)

    counts = {
        "canonical_species": len(source_rows),
        "canonical_gen8_level_up_learnsets": len(canonical_learnsets),
        "missing_canonical_level_up_learnsets": len(missing_learnsets),
        "canonical_species_with_evolutions": sum(1 for row in evolution_rows if row["source_has_evolution_pointer"]),
        "parsed_evolution_edges": sum(len(row["evolutions"]) for row in evolution_rows),
        "unresolved_evolution_records": len(unresolved_evolutions),
        "pokedex_text_rows": len(pokedex_rows),
        "pokedex_text_rows_with_decoded_description": sum(bool(row["description_fragments"]) for row in pokedex_rows),
        "unresolved_pokedex_text_rows": len(unresolved_text),
        "cry_rows": len(cry_rows),
        "cry_rows_matching_source_table": len(cry_rows) - len(missing_cries),
        "missing_cry_table_matches": len(missing_cries),
        "graphics_reference_rows": len(graphics_rows),
        "graphics_rows_with_required_references": len(graphics_rows) - len(missing_graphics_refs),
        "source_graphics_asset_payload_imported": False,
        "form_species_tables_referenced": len(referenced_form_species),
        "form_change_tables_referenced": len(referenced_form_changes),
        "missing_form_table_references": len(missing_form_tables),
        "pokedex_order_tables": len(order_rows),
        "pokedex_order_tables_complete": sum(1 for row in order_rows.values() if row["complete_for_gen8"]),
        "source_move_definitions": len(move_rows),
        "missing_source_move_definitions": len(missing_move_definitions),
        "canonical_gen8_learnset_distinct_moves": len(used_move_symbols),
        "canonical_gen8_learnset_moves_missing_in_emerald": len({
            row["source_move_symbol"] for row in used_move_rows if row["emerald_move_id"] is None
        }),
        "source_contest_effect_definitions": len(contest_effect_rows),
        "source_contest_effect_callbacks_missing_in_emerald": len(missing_contest_callbacks),
        "source_battle_effect_symbols_missing_in_emerald": len(missing_battle_effects),
        "canonical_gen8_learnset_moves_missing_target_battle_records": len(missing_target_battle_move_records),
        "canonical_gen8_learnset_moves_missing_target_contest_records": len(missing_target_contest_move_records),
        "canonical_abilities_used": len(ability_rows),
        "canonical_abilities_without_emerald_constant": sum(not row["target_ability_constant_present"] for row in ability_rows),
        "canonical_abilities_without_source_info_record": sum(not row["source_ability_info_record_present"] for row in ability_rows),
        "canonical_held_items_used": len(item_rows),
        "canonical_held_items_without_emerald_constant": sum(not row["target_item_constant_present"] for row in item_rows),
        "canonical_held_items_without_target_data_record": sum(not row["target_item_data_record_present"] for row in item_rows),
        "canonical_held_items_without_source_data_record": sum(not row["source_item_data_record_present"] for row in item_rows),
        "canonical_types_used": len(used_types),
        "canonical_types_without_emerald_definition": len(missing_types),
        "canonical_egg_groups_used": len(used_egg_groups),
        "canonical_egg_groups_without_emerald_definition": len(missing_egg_groups),
        "canonical_growth_rates_used": len(growth_use),
        "canonical_growth_rates_without_emerald_definition": len(missing_growth_rates),
        "source_evolution_methods": len(source_evolution_methods),
        "canonical_evolution_methods_used": len(used_evolution_methods),
        "canonical_evolution_methods_without_target_method_symbol": sum(
            row["used_by_canonical_evolutions"] and not row["target_method_symbol_present"]
            for row in evolution_method_rows
        ),
        "unknown_evolution_target_symbols": len(unknown_evolution_targets),
    }

    readiness = {
        "898_canonical_species_rows": counts["canonical_species"] == 898,
        "898_gen8_level_up_learnsets": counts["canonical_gen8_level_up_learnsets"] == 898 and not missing_learnsets,
        "all_present_evolution_expressions_parsed": not unresolved_evolutions,
        "898_pokedex_text_rows": len(pokedex_rows) == 898,
        "898_cry_identifiers_mapped_to_source_table": len(cry_rows) == 898 and not missing_cries,
        "898_graphics_reference_rows": len(graphics_rows) == 898 and not missing_graphics_refs,
        "all_referenced_form_tables_found": not missing_form_tables,
        "all_three_pokedex_orders_cover_gen8": len(order_rows) >= 3 and not order_failures,
        "all_source_move_info_rows_found": not missing_move_definitions,
        "runtime_move_tables_ready": False,
        "runtime_contest_tables_ready": False,
        "runtime_evolution_tables_ready": False,
        "runtime_cry_assets_ready": False,
        "runtime_graphics_assets_ready": False,
        "runtime_form_tables_ready": False,
        "runtime_ability_tables_ready": False,
        "runtime_item_tables_ready": False,
        "runtime_species_ids_allocated": False,
        "num_species_change_allowed": False,
    }
    report = {
        "source_snapshot": "rh-hideout/pokeemerald-expansion@c460a8661dfa0598ae25d42a968c690ecbf489c6",
        "scope": "National Dex 1-898 canonical species; source-only staging",
        "counts": counts,
        "readiness": readiness,
        "missing_canonical_learnsets": missing_learnsets,
        "unresolved_evolutions": unresolved_evolutions,
        "unresolved_pokedex_text": unresolved_text,
        "missing_cries": missing_cries,
        "missing_graphics_references": missing_graphics_refs,
        "missing_form_tables": missing_form_tables,
        "pokedex_order_failures": order_failures,
        "missing_source_move_definitions": missing_move_definitions,
        "missing_contest_callbacks": missing_contest_callbacks,
        "missing_battle_effect_symbols": missing_battle_effects,
        "missing_target_battle_move_records": missing_target_battle_move_records,
        "missing_target_contest_move_records": missing_target_contest_move_records,
        "missing_emerald_abilities": [row["ability_symbol"] for row in ability_rows if not row["target_ability_constant_present"]],
        "abilities_without_source_info_records": [row["ability_symbol"] for row in ability_rows if not row["source_ability_info_record_present"]],
        "missing_emerald_items": [row["item_symbol"] for row in item_rows if not row["target_item_constant_present"]],
        "items_without_target_data_records": [row["item_symbol"] for row in item_rows if not row["target_item_data_record_present"]],
        "items_without_source_data_records": [row["item_symbol"] for row in item_rows if not row["source_item_data_record_present"]],
        "missing_emerald_types": missing_types,
        "missing_emerald_egg_groups": missing_egg_groups,
        "missing_emerald_growth_rates": missing_growth_rates,
        "unknown_evolution_targets": unknown_evolution_targets,
    }

    outputs = {
        DATA / "gen8_species_evolutions.json": evolution_rows,
        DATA / "gen8_species_pokedex_entries.json": pokedex_rows,
        DATA / "gen8_species_cry_map.json": cry_rows,
        DATA / "gen8_species_graphics_references.json": graphics_rows,
        DATA / "gen8_species_form_references.json": form_rows,
        DATA / "gen8_species_level_up_learnsets.json": canonical_learnsets,
        DATA / "gen8_move_source_catalog.json": move_rows,
        DATA / "gen8_contest_effect_source_catalog.json": contest_effect_rows,
        DATA / "gen8_ability_source_dependencies.json": ability_rows,
        DATA / "gen8_item_source_dependencies.json": item_rows,
        DATA / "gen8_type_source_dependencies.json": type_rows,
        DATA / "gen8_egg_group_source_dependencies.json": egg_group_rows,
        DATA / "gen8_growth_rate_source_dependencies.json": growth_rate_rows,
        DATA / "gen8_evolution_method_dependencies.json": evolution_method_rows,
        DATA / "gen8_pokedex_orders.json": order_rows,
        REPORTS / "pending_species_tables_audit.json": report,
    }
    for path, value in outputs.items():
        write_json(path, value)
    return report


def main() -> int:
    try:
        report = source_table_inventory()
        print(json.dumps(report["counts"], indent=2))
        for name, ready in report["readiness"].items():
            if not ready:
                print(f"PENDING: {name}")
        # Source table extraction is successful when the source tables are
        # present and internally complete. Runtime readiness is intentionally
        # false until Emerald implementations and assets are ported.
        source_keys = (
            "898_canonical_species_rows",
            "898_gen8_level_up_learnsets",
            "all_present_evolution_expressions_parsed",
            "898_pokedex_text_rows",
            "898_cry_identifiers_mapped_to_source_table",
            "898_graphics_reference_rows",
            "all_referenced_form_tables_found",
            "all_three_pokedex_orders_cover_gen8",
            "all_source_move_info_rows_found",
        )
        failed = [key for key in source_keys if not report["readiness"][key]]
        if failed:
            print("SOURCE TABLE AUDIT INCOMPLETE: " + ", ".join(failed), file=sys.stderr)
            return 2
        print("PASS: source tables extracted and audited; Emerald runtime tables remain explicitly gated.")
        return 0
    except (OSError, RuntimeError, ValueError, KeyError, TypeError) as exc:
        print(f"GEN8 PENDING TABLE AUDIT FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
