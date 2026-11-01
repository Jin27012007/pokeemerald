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
SRC_LEARNSET_DIR = VENDOR / "src/data/pokemon/level_up_learnsets"
SRC_SPECIES_INFO_DIR = VENDOR / "src/data/pokemon/species_info"
SOURCE_GENERATIONS = (1, 2, 3, 4, 5, 6, 7, 8)
LEARNSET_GENERATIONS = (4, 5, 6, 7, 8)
TARGET_GAME_GENERATION = 8

DST_SPECIES = ROOT / "include/constants/species.h"
DST_MOVES = ROOT / "include/constants/moves.h"
DST_INFO = ROOT / "src/data/pokemon/species_info.h"
DST_POKEMON_H = ROOT / "include/pokemon.h"
DST_POKEMON_CONSTANTS = ROOT / "include/constants/pokemon.h"
DST_ABILITIES = ROOT / "include/constants/abilities.h"
DST_ITEMS = ROOT / "include/constants/items.h"
DST_POKEDEX = ROOT / "include/constants/pokedex.h"

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
    if not enum:
        pattern = rf"^#define\s+{re.escape(prefix)}([A-Z0-9_]+)\s+(\d+)\s*$"
        return [{"symbol": m.group(1), "id": int(m.group(2))}
                for m in re.finditer(pattern, text, re.M)]

    # Resolve enums independently: implicit enum values restart at zero for
    # each enum declaration. Only inspect members inside one enum body.
    enum_blocks = re.finditer(r"enum(?:\s+__attribute__\s*\(\([^)]*\)\))?[^{]*\{([^}]*)\}", text, re.S)
    result = []
    member_re = re.compile(
        rf"^\s*{re.escape(prefix)}([A-Z0-9_]+)\s*(?:=\s*([^,]+))?\s*,?\s*(?://.*)?$",
        re.M,
    )
    for block in enum_blocks:
        next_value = 0
        for match in member_re.finditer(block.group(1)):
            symbol, raw = match.group(1), match.group(2)
            if raw is not None:
                raw = raw.strip()
                if re.fullmatch(r"(?:0x[0-9A-Fa-f]+|\d+)", raw):
                    next_value = int(raw, 0)
                else:
                    # Do not invent values for expressions or symbolic aliases.
                    continue
            result.append({"symbol": symbol, "id": next_value})
            next_value += 1
    return result

def balanced_species_records(text: str) -> list[dict]:
    """Read C designated initializers whose RHS is either a brace block or macro."""
    start_re = re.compile(r"^\s*\[SPECIES_([A-Z0-9_]+)\]\s*=\s*", re.M)
    records = []
    for match in start_re.finditer(text):
        start = match.end()
        while start < len(text) and text[start].isspace():
            start += 1
        if start >= len(text):
            continue
        i = start
        paren = brace = bracket = 0
        in_string = escaped = False
        is_brace_block = text[start] == "{"
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
                elif ch == "(":
                    paren += 1
                elif ch == ")":
                    paren -= 1
                elif ch == "{":
                    brace += 1
                elif ch == "}":
                    brace -= 1
                    if is_brace_block and brace == 0 and paren == 0 and bracket == 0:
                        i += 1
                        break
                elif ch == "[":
                    bracket += 1
                elif ch == "]":
                    bracket -= 1
                elif ch == "," and paren == brace == bracket == 0:
                    break
            i += 1
        raw = text[start:i].strip().rstrip(",")
        if not raw:
            continue
        if is_brace_block and raw.startswith("{") and raw.endswith("}"):
            body = raw[1:-1].strip()
        else:
            body = raw
        records.append({"symbol": match.group(1), "body": body})
    return records


def split_c_arguments(raw: str) -> list[str]:
    """Split macro arguments at commas that are not nested or quoted."""
    args, start = [], 0
    paren = brace = bracket = 0
    in_string = escaped = False
    for i, ch in enumerate(raw):
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch == "(":
            paren += 1
        elif ch == ")":
            paren -= 1
        elif ch == "{":
            brace += 1
        elif ch == "}":
            brace -= 1
        elif ch == "[":
            bracket += 1
        elif ch == "]":
            bracket -= 1
        elif ch == "," and paren == brace == bracket == 0:
            args.append(raw[start:i].strip())
            start = i + 1
    tail = raw[start:].strip()
    if tail or args:
        args.append(tail)
    return args


def extract_c_macros(text: str) -> dict:
    """Capture object/function macros, joining C continuation lines."""
    macros = {}
    lines = text.splitlines()
    i = 0
    define_re = re.compile(r"^\s*#define\s+([A-Za-z_][A-Za-z0-9_]*)(?:\(([^)]*)\))?\s*(.*)$")
    while i < len(lines):
        match = define_re.match(lines[i])
        if not match:
            i += 1
            continue
        name, params_raw, body = match.group(1), match.group(2), match.group(3)
        parts = [body]
        while parts[-1].rstrip().endswith("\\") and i + 1 < len(lines):
            parts[-1] = parts[-1].rstrip()[:-1]
            i += 1
            parts.append(lines[i])
        params = None if params_raw is None else [
            x.strip() for x in params_raw.split(",") if x.strip()
        ]
        macros[name] = {"params": params, "body": " ".join(parts).strip()}
        i += 1
    return macros


def expand_c_macro_text(text: str, macros: dict, depth: int = 0) -> str:
    """Expand local family macros needed for SpeciesInfo compact fields."""
    if depth > 12 or not macros:
        return text
    result = text
    for _ in range(8):
        changed = False
        # Expand function-like macros by scanning balanced invocation parens.
        pos = 0
        while pos < len(result):
            match = re.search(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", result[pos:])
            if not match:
                break
            name = match.group(1)
            definition = macros.get(name)
            absolute = pos + match.start()
            open_pos = pos + match.end() - 1
            if definition is None or definition["params"] is None:
                pos = open_pos + 1
                continue
            level, end, in_string, escaped = 1, open_pos + 1, False, False
            while end < len(result) and level:
                ch = result[end]
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
                        level += 1
                    elif ch == ")":
                        level -= 1
                end += 1
            if level:
                pos = open_pos + 1
                continue
            args = split_c_arguments(result[open_pos + 1:end - 1])
            params = definition["params"]
            if len(args) != len(params):
                pos = end
                continue
            body = definition["body"]
            replacements = dict(zip(params, args))
            param_re = re.compile(
                r"\b(" + "|".join(re.escape(x) for x in sorted(params, key=len, reverse=True)) + r")\b"
            ) if params else None
            if param_re:
                body = param_re.sub(lambda m: replacements[m.group(1)], body)
            body = re.sub(r"\s*##\s*", "", body)
            body = expand_c_macro_text(body, macros, depth + 1)
            result = result[:absolute] + body + result[end:]
            changed = True
            pos = absolute + len(body)
        # Expand standalone object-like macro identifiers used as field values.
        for name, definition in macros.items():
            if definition["params"] is not None:
                continue
            token = re.compile(r"\b" + re.escape(name) + r"\b")
            new_result, n = token.subn(definition["body"], result)
            if n and new_result != result:
                result = new_result
                changed = True
        result = re.sub(r"\s*##\s*", "", result)
        if not changed:
            break
    return result


def evaluate_source_condition(condition: str, target_generation: int) -> bool:
    condition = condition.strip().strip("() ").strip()
    match = re.fullmatch(
        r"(?:P_UPDATED_[A-Z0-9_]+)\s*(>=|>|<=|<|==|!=)\s*GEN_(\d+)",
        condition,
    )
    if match:
        op, gen = match.group(1), int(match.group(2))
        return {
            ">=": target_generation >= gen, ">": target_generation > gen,
            "<=": target_generation <= gen, "<": target_generation < gen,
            "==": target_generation == gen, "!=": target_generation != gen,
        }[op]
    # Configuration flags not described by the Gen 8 data policy default to
    # false; any such branch affecting a compact field remains detectable.
    return False


def resolve_source_conditionals(text: str, target_generation: int) -> str:
    """Select active #if branches for the declared Gen 8 compatibility target."""
    output = []
    stack = []
    active = True
    for line in text.splitlines():
        directive = re.match(r"^\s*#\s*(if|ifdef|ifndef|elif|else|endif)\b(.*)$", line)
        if not directive:
            if active:
                output.append(line)
            continue
        kind, expression = directive.group(1), directive.group(2).strip()
        if kind in ("if", "ifdef", "ifndef"):
            condition = evaluate_source_condition(expression, target_generation) if kind == "if" else False
            frame = {"parent": active, "taken": condition, "active": active and condition}
            stack.append(frame)
            active = frame["active"]
        elif kind == "elif" and stack:
            frame = stack[-1]
            condition = evaluate_source_condition(expression, target_generation)
            frame["active"] = frame["parent"] and not frame["taken"] and condition
            frame["taken"] = frame["taken"] or condition
            active = frame["active"]
        elif kind == "else" and stack:
            frame = stack[-1]
            frame["active"] = frame["parent"] and not frame["taken"]
            frame["taken"] = True
            active = frame["active"]
        elif kind == "endif" and stack:
            frame = stack.pop()
            active = frame["parent"]
    return "\n".join(output)

def extract_learnsets(text: str, generation: int) -> list[dict]:
    block_re = re.compile(
        r"static const struct LevelUpMove s([A-Za-z0-9]+)LevelUpLearnset\[\]\s*=\s*\{([\s\S]*?)\n\};"
    )
    move_re = re.compile(r"LEVEL_UP_MOVE\(\s*(\d+)\s*,\s*MOVE_([A-Z0-9_]+)\s*\)")
    result = []
    for block in block_re.finditer(text):
        moves = [{"level": int(m.group(1)), "move": m.group(2)}
                 for m in move_re.finditer(block.group(2))]
        if moves:
            result.append({"source_species": block.group(1), "generation": generation, "moves": moves})
    return result

def extract_designated_fields(body: str) -> dict:
    """Extract designated fields without truncating nested calls or ternaries."""
    fields = {}
    i = 0
    while i < len(body):
        m = re.search(r"\.([A-Za-z0-9_]+)\s*=", body[i:])
        if not m:
            break
        name = m.group(1)
        value_start = i + m.end()
        j = value_start
        depth_paren = depth_brace = depth_bracket = 0
        in_string = escaped = False
        while j < len(body):
            ch = body[j]
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
                    depth_paren += 1
                elif ch == ")":
                    depth_paren -= 1
                elif ch == "{":
                    depth_brace += 1
                elif ch == "}":
                    if depth_brace == 0 and depth_paren == 0 and depth_bracket == 0:
                        break
                    depth_brace -= 1
                elif ch == "[":
                    depth_bracket += 1
                elif ch == "]":
                    depth_bracket -= 1
                elif ch == "," and depth_paren == depth_brace == depth_bracket == 0:
                    break
            j += 1
        fields[name] = " ".join(body[value_start:j].strip().split())
        i = j + 1
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
    write(path, json.dumps(value, indent=2, ensure_ascii=False) + "\n")

def parse_species_info(source_text: str, target_info_text: str,
                       type_text: str, ability_text: str, item_text: str,
                       source_symbol_generation: dict[str, int],
                       source_ability_text: str, source_item_text: str,
                       source_pokemon_text: str,
                       source_symbol_macros: dict[str, dict]) -> dict:
    records = balanced_species_records(source_text)
    for record in records:
        generation = source_symbol_generation.get(record["symbol"])
        if generation is None:
            raise RuntimeError(
                "SpeciesInfo source generation missing for " + record["symbol"]
            )
        record["generation"] = generation
    # Source enum IDs are Expansion IDs, not Emerald IDs. Keep both domains
    # explicit so source values are never accidentally mistaken for runtime IDs.
    type_values = {x["symbol"]: x["id"] for x in symbols(source_pokemon_text, "TYPE_", enum=True)}
    egg_values = {x["symbol"]: x["id"] for x in symbols(source_pokemon_text, "EGG_GROUP_", enum=True)}
    growth_values = {x["symbol"]: x["id"] for x in symbols(source_pokemon_text, "GROWTH_", enum=True)}
    ability_values = {x["symbol"]: x["id"] for x in symbols(source_ability_text, "ABILITY_", enum=True)}
    item_values = {x["symbol"]: x["id"] for x in symbols(source_item_text, "ITEM_", enum=True)}
    if not all((type_values, egg_values, growth_values, ability_values, item_values)):
        missing_catalogs = [
            name for name, values in (
                ("types", type_values), ("egg_groups", egg_values),
                ("growth_rates", growth_values), ("abilities", ability_values),
                ("items", item_values),
            ) if not values
        ]
        raise RuntimeError("Expansion source enum catalog(s) incomplete: " + ", ".join(missing_catalogs))

    out, unresolved = [], []
    scalar_fields = (
        "baseHP", "baseAttack", "baseDefense", "baseSpeed", "baseSpAttack",
        "baseSpDefense", "catchRate", "expYield", "eggCycles",
    )
    ev_fields = (
        "evYield_HP", "evYield_Attack", "evYield_Defense", "evYield_Speed",
        "evYield_SpAttack", "evYield_SpDefense",
    )

    def resolve_generation_expression(raw, generation):
        if raw is None:
            return None
        raw = " ".join(raw.split())
        # Resolve well-understood Expansion generation switches, with the
        # source generation interpreted as the compatibility level.
        conditionals = [
            (r"\(P_UPDATED_EXP_YIELDS\s*>=\s*GEN_(\d+)\)\s*\?\s*(-?\d+)\s*:\s*(-?\d+)",
             lambda m: int(m.group(2) if generation >= int(m.group(1)) else m.group(3))),
            (r"P_UPDATED_STATS\s*>=\s*GEN_(\d+)\s*\?\s*(-?\d+)\s*:\s*(-?\d+)",
             lambda m: int(m.group(2) if generation >= int(m.group(1)) else m.group(3))),
            (r"\(P_UPDATED_FRIENDSHIP\s*>=\s*GEN_(\d+)\)\s*\?\s*(-?\d+)\s*:\s*(-?\d+)",
             lambda m: int(m.group(2) if generation >= int(m.group(1)) else m.group(3))),
        ]
        for pattern, resolver in conditionals:
            match = re.fullmatch(pattern, raw)
            if match:
                return resolver(match)
        if re.fullmatch(r"(?:0x[0-9A-Fa-f]+|\d+)", raw):
            return int(raw, 0)
        return None

    def resolve_macro_pair(raw, macro_name, prefix, domain):
        match = re.fullmatch(
            rf"{macro_name}\(\s*{prefix}([A-Z0-9_]+)(?:\s*,\s*{prefix}([A-Z0-9_]+))?\s*\)",
            raw or "",
        )
        if not match:
            return None
        first = match.group(1)
        second = match.group(2) or first
        if first not in domain or second not in domain:
            return None
        return [domain[first], domain[second]]

    def resolve_gender(raw):
        if raw == "MON_GENDERLESS":
            return 0xFF
        if raw == "MON_MALE":
            return 0x00
        if raw == "MON_FEMALE":
            return 0xFE
        match = re.fullmatch(r"PERCENT_FEMALE\(\s*(\d+(?:\.\d+)?)\s*\)", raw or "")
        if match:
            # Expansion's macro: min(254, ((percent * 255) / 100)).
            return min(254, int(float(match.group(1)) * 255 / 100))
        return resolve_generation_expression(raw, 3)

    for record in records:
        macros = source_symbol_macros.get(record["symbol"], {})
        body = expand_c_macro_text(record["body"], macros)
        body = resolve_source_conditionals(body, TARGET_GAME_GENERATION)
        fields = extract_designated_fields(body)
        problems = []
        values = {}
        for field in scalar_fields:
            raw = fields.get(field)
            if raw is None:
                problems.append(f"missing_scalar:{field}")
            else:
                resolved = resolve_generation_expression(raw, TARGET_GAME_GENERATION)
                if resolved is None:
                    problems.append(f"unresolved_scalar:{field}:{raw}")
                else:
                    values[field] = resolved

        for field in ev_fields:
            raw = fields.get(field)
            if raw is None:
                values[field] = 0
            else:
                resolved = resolve_generation_expression(raw, record["generation"])
                if resolved is None:
                    problems.append(f"unresolved_ev_yield:{field}:{raw}")
                else:
                    values[field] = resolved

        gender_raw = fields.get("genderRatio")
        gender_ratio = resolve_gender(gender_raw)
        if gender_ratio is None:
            problems.append(f"unresolved_gender_ratio:{gender_raw}")
        
        friendship_raw = fields.get("friendship")
        if friendship_raw == "STANDARD_FRIENDSHIP":
            friendship = 50 if TARGET_GAME_GENERATION >= 8 else 70
        else:
            friendship = resolve_generation_expression(friendship_raw, record["generation"])
        if friendship is None:
            problems.append(f"unresolved_friendship:{friendship_raw}")

        growth_raw = fields.get("growthRate")
        growth_match = re.fullmatch(r"GROWTH_([A-Z0-9_]+)", growth_raw or "")
        growth_rate = growth_values.get(growth_match.group(1)) if growth_match else None
        if growth_rate is None:
            problems.append(f"unresolved_growth_rate:{growth_raw}")

        type_raw = fields.get("types")
        type_pair = resolve_macro_pair(type_raw, "MON_TYPES", "TYPE_", type_values)
        if type_pair is None:
            problems.append(f"unresolved_types:{type_raw}")

        egg_raw = fields.get("eggGroups")
        egg_pair = resolve_macro_pair(egg_raw, "MON_EGG_GROUPS", "EGG_GROUP_", egg_values)
        if egg_pair is None:
            problems.append(f"unresolved_egg_groups:{egg_raw}")

        ability_raw_match = re.search(r"\.abilities\s*=\s*\{([^}]*)\}", body, re.S)
        ability_pair = None
        hidden_ability = None
        ability_names = re.findall(r"ABILITY_([A-Z0-9_]+)", ability_raw_match.group(1)) if ability_raw_match else []
        if not ability_names:
            problems.append(f"unresolved_abilities:{ability_raw_match.group(1) if ability_raw_match else None}")
        else:
            ability_names = (ability_names + ["NONE", "NONE", "NONE"])[:3]
            if any(name not in ability_values for name in ability_names):
                problems.extend(f"unknown_ability:{name}" for name in ability_names if name not in ability_values)
            else:
                ability_pair = [ability_values[name] for name in ability_names[:2]]
                hidden_ability = ability_values[ability_names[2]]

        rare_raw = fields.get("itemRare")
        common_raw = fields.get("itemCommon")
        rare_match = re.search(r"ITEM_([A-Z0-9_]+)", rare_raw or "")
        common_match = re.search(r"ITEM_([A-Z0-9_]+)", common_raw or "")
        rare_name = rare_match.group(1) if rare_match else "NONE"
        common_name = common_match.group(1) if common_match else "NONE"
        item_compatibility = {"common": "mapped", "rare": "mapped"}
        if rare_name not in item_values:
            problems.append(f"unknown_item:{rare_name}")
            item_compatibility["rare"] = "source_only"
        if common_name not in item_values:
            problems.append(f"unknown_item:{common_name}")
            item_compatibility["common"] = "source_only"

        color_match = re.search(r"\.bodyColor\s*=\s*BODY_COLOR_([A-Z0-9_]+)", body)
        color_values = {
            "RED": 0, "BLUE": 1, "YELLOW": 2, "GREEN": 3, "BLACK": 4,
            "BROWN": 5, "PURPLE": 6, "GRAY": 7, "WHITE": 8, "PINK": 9,
        }
        body_color = color_values.get(color_match.group(1)) if color_match else None
        if body_color is None:
            problems.append("unresolved_body_color")

        nat_match = re.search(r"\.natDexNum\s*=\s*NATIONAL_DEX_([A-Z0-9_]+)", body)
        dex_value = nat_match.group(1) if nat_match else None
        raw_common_item = common_raw
        raw_rare_item = rare_raw
        record_data = {
            "species_symbol": record["symbol"],
            "generation": record["generation"],
            "national_dex_symbol": dex_value,
            "source_raw": fields,
            "statistics": values,
            "gender_ratio": gender_ratio,
            "friendship": friendship,
            "growth_rate": growth_rate,
            "types": type_pair,
            "egg_groups": egg_pair,
            "abilities": ability_pair,
            "hidden_ability": hidden_ability,
            "item_common": item_values.get(common_name),
            "item_rare": item_values.get(rare_name),
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
        "source_enum_domains": {
            "types": type_values,
            "egg_groups": egg_values,
            "growth_rates": growth_values,
            "abilities": ability_values,
            "items": item_values,
        },
    }

def generate(check: bool = False) -> dict:
    source_species = symbols(read(SRC_SPECIES), "SPECIES_", enum=True)
    target_species = symbols(read(DST_SPECIES), "SPECIES_")
    source_moves = symbols(read(SRC_MOVES), "MOVE_", enum=True)
    target_moves = symbols(read(DST_MOVES), "MOVE_")
    source_info_files = [SRC_SPECIES_INFO_DIR / f"gen_{generation}_families.h" for generation in SOURCE_GENERATIONS]
    source_learnset_files = [SRC_LEARNSET_DIR / f"gen_{generation}.h" for generation in LEARNSET_GENERATIONS]
    source_info_texts = {path.name: read(path) for path in source_info_files}
    source_learnset_texts = {path.name: read(path) for path in source_learnset_files}
    source_info_text = "\n".join(source_info_texts.values())
    source_symbol_generation = {}
    source_symbol_macros = {}
    for generation, path in zip(SOURCE_GENERATIONS, source_info_files):
        family_text = source_info_texts[path.name]
        family_macros = extract_c_macros(family_text)
        for record in balanced_species_records(family_text):
            symbol = record["symbol"]
            if symbol in source_symbol_generation:
                raise RuntimeError(
                    "Duplicate SpeciesInfo designator across source generations: " + symbol
                )
            source_symbol_generation[symbol] = generation
            source_symbol_macros[symbol] = family_macros
    target_info_text = read(DST_INFO)
    learnsets = []
    for generation, path in zip(LEARNSET_GENERATIONS, source_learnset_files):
        learnsets.extend(extract_learnsets(source_learnset_texts[path.name], generation))
    type_text, ability_text, item_text = read(DST_POKEMON_CONSTANTS), read(DST_ABILITIES), read(DST_ITEMS)
    source_ability_text = read(VENDOR / "include/constants/abilities.h")
    source_item_text = read(VENDOR / "include/constants/items.h")
    source_pokemon_text = read(VENDOR / "include/constants/pokemon.h")
    info_result = parse_species_info(
        source_info_text, target_info_text, type_text, ability_text, item_text,
        source_symbol_generation, source_ability_text, source_item_text,
        source_pokemon_text, source_symbol_macros,
    )
    info_by_symbol = {}
    for record in info_result["compact_records"] + info_result["unresolved_records"]:
        if record["species_symbol"] in info_by_symbol:
            raise RuntimeError("Duplicate SpeciesInfo designator: " + record["species_symbol"])
        info_by_symbol[record["species_symbol"]] = record

    # Parse vanilla Emerald records as the authoritative source for the 386
    # existing National Dex species. These remain the existing runtime rows;
    # this does not allocate or renumber any internal species IDs.
    target_info_records = balanced_species_records(target_info_text)
    target_info_by_symbol = {row["symbol"]: row for row in target_info_records}
    target_species_by_dex = {}
    natdex_target_values = {
        row["symbol"]: row["id"]
        for row in symbols(read(DST_POKEDEX), "NATIONAL_DEX_", enum=True)
    }
    for row in target_info_records:
        fields = extract_designated_fields(row["body"])
        nat_match = re.fullmatch(r"NATIONAL_DEX_([A-Z0-9_]+)", fields.get("natDexNum", ""))
        dex_id = natdex_target_values.get(nat_match.group(1)) if nat_match else None
        if dex_id is not None and 1 <= dex_id <= 898:
            target_species_by_dex[dex_id] = {
                "species_symbol": row["symbol"],
                "generation": 3,
                "source_raw": fields,
                "status": "existing_emerald_species_info",
                "unresolved": [],
            }

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

    # Coverage uses the canonical National Dex identity. A record is accepted
    # only when its source symbol or its explicit .natDexNum identifies the Dex.
    natdex_values = {x["symbol"]: x["id"] for x in symbols(read(DST_POKEDEX), "NATIONAL_DEX_", enum=True)}
    info_candidates_by_dex = {}
    for row in info_result["compact_records"] + info_result["unresolved_records"]:
        dex_symbol = row.get("national_dex_symbol")
        dex_id = natdex_values.get(dex_symbol) if dex_symbol else None
        if dex_id is not None and 1 <= dex_id <= 898:
            info_candidates_by_dex.setdefault(dex_id, []).append(row)
    canonical_species_info = []
    missing_species_info = []
    for dex in range(1, 899):
        national_symbol = by_dex[dex]
        preferred_symbol = BASE_ALIASES.get(national_symbol, national_symbol)
        candidates = info_candidates_by_dex.get(dex, [])
        row = target_species_by_dex.get(dex)
        if row is None:
            row = next((candidate for candidate in candidates
                        if candidate["species_symbol"] == preferred_symbol), None)
        if row is None:
            row = info_by_symbol.get(preferred_symbol)
        if row is None:
            missing_species_info.append({
                "national_dex": dex,
                "national_symbol": national_symbol,
                "expected_source_alias": preferred_symbol,
                "status": "source_record_missing",
            })
        else:
            canonical_species_info.append({
                "national_dex": dex,
                "national_symbol": national_symbol,
                "source_record_symbol": row["species_symbol"],
                "source_generation": row["generation"],
                "source_fields_present": sorted(row.get("source_raw", {}).keys()),
                "compact_status": row["status"],
                "unresolved_fields": row["unresolved"],
                "same_dex_variant_symbols": sorted(
                    candidate["species_symbol"] for candidate in candidates
                    if candidate["species_symbol"] != row["species_symbol"]
                ),
            })
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
    source_field_universe = sorted(set().union(*(
        set(row.get("source_fields_present", [])) for row in canonical_species_info
    ))) if canonical_species_info else []
    field_coverage = {
        field: sum(1 for row in canonical_species_info if field in row.get("source_fields_present", []))
        for field in source_field_universe
    }
    emerald_compatibility = {
        "struct_species_info_bytes": 0x1A,
        "source_species_info_uses_three_ability_slots": True,
        "emerald_species_info_has_two_ability_slots": True,
        "ability_slot_3_runtime_compatible": False,
        "source_ability_enum_width_bits": 16,
        "emerald_ability_slot_width_bits": 8,
        "all_source_ability_ids_fit_emerald_slot": max(info_result["source_enum_domains"]["abilities"].values(), default=0) <= 255,
        "source_item_enum_width_bits": 16,
        "emerald_item_slot_width_bits": 16,
        "all_source_item_ids_fit_emerald_slot": max(info_result["source_enum_domains"]["items"].values(), default=0) <= 65535,
        "fairy_type_supported_in_emerald": "FAIRY" in {x["symbol"] for x in symbols(type_text, "TYPE_")},
        "source_only_fields_require_runtime_work": ["third_ability_slot", "new_abilities", "new_items", "fairy_type"],
    }
    counts = {
        "canonical_dex_entries": len(species_map), "existing_species": existing_count,
        "new_species": len(new_species), "source_moves_gen1_8": len({x["id"] for x in source_moves if x["id"] <= 847}),
        "learnset_blocks": len(learnsets), "learnset_move_entries": sum(len(x["moves"]) for x in learnsets),
        "learnset_generation_counts": {str(g): sum(1 for row in learnsets if row["generation"] == g) for g in LEARNSET_GENERATIONS},
        "learnset_generations": list(LEARNSET_GENERATIONS),
        "distinct_learnset_moves": len(used_moves), "missing_learnset_moves": len(missing_moves),
        "species_info_blocks": info_result["source_record_count"],
        "species_info_source_files": len(source_info_files),
        "species_info_generation_files": [path.name for path in source_info_files],
        "learnset_source_files": len(source_learnset_files),
        "species_info_compact_records": len(info_result["compact_records"]),
        "species_info_unresolved_records": len(info_result["unresolved_records"]),
        "species_info_hidden_abilities_resolved": sum(1 for row in info_result["compact_records"] + info_result["unresolved_records"] if row["hidden_ability"] is not None),
        "canonical_species_info_covered": len(canonical_species_info),
        "canonical_species_info_missing": len(missing_species_info),
        "canonical_species_info_raw_field_coverage": field_coverage,
        "missing_species_info_for_new_dex_species": len(missing_species_info),
    }
    species_info_ready = (
        len(canonical_species_info) == 898
        and not missing_species_info
        and all(row["compact_status"] == "compact_fields_resolved" for row in canonical_species_info)
        and all("baseHP" in row["source_fields_present"] for row in canonical_species_info)
        and all("natDexNum" in row["source_fields_present"] for row in canonical_species_info)
    )
    report = {
        "source": "pinned pokeemerald-expansion source snapshot (Gen 4-9 family data)",
        "scope": "National Dex 1-898 canonical species only",
        "counts": counts,
        "readiness": {
            "canonical_dex_map_complete": True, "existing_species_ids_preserved": True,
            "new_species_ids_allocated": False, "learnsets_parsed_from_expansion_syntax": True,
            "all_learnset_move_symbols_have_emerald_ids": not missing_moves,
            "species_info_compact_stage_generated": len(info_result["compact_records"]) > 0,
            "species_info_898_canonical_entries": len(canonical_species_info) == 898,
            "species_info_zero_missing_canonical_entries": not missing_species_info,
            "species_info_zero_unresolved_canonical_records": all(row["compact_status"] == "compact_fields_resolved" for row in canonical_species_info),
            "species_info_complete": species_info_ready, "save_extension_validated": False,
            "evolutions_ready": False, "pokedex_text_ready": False, "cries_ready": False,
            "graphics_ready": False, "battle_and_contest_moves_ready": False,
            "runtime_ready": False, "num_species_change_allowed": False,
        },
        "species_mapping": species_map,
        "species_info_by_national_dex": canonical_species_info,
        "species_info_complete": species_info_ready,
        "missing_species_info_by_national_dex": missing_species_info,
        "species_info_field_coverage": field_coverage,
        "emerald_compatibility": emerald_compatibility,
        "missing_learnset_move_symbols": missing_moves,
        "species_info_compact_summary": counts,
        "missing_species_info_for_new_dex_species": missing_species_info,
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
        write_json(OUT / "species_info_by_national_dex.json", canonical_species_info)
        write_json(ROOT / "data/pokemon/gen8_species_info_by_national_dex.json", canonical_species_info)
        write_json(OUT / "species_info_field_coverage.json", field_coverage)
        write_json(OUT / "emerald_species_info_compatibility.json", emerald_compatibility)
        write_json(OUT / "missing_species_info_for_new_dex_species.json", missing_species_info)
        with (OUT / "move_dependencies.csv").open("w", newline="", encoding="utf-8") as fp:
            writer = csv.DictWriter(fp, fieldnames=list(move_dependencies[0].keys()))
            writer.writeheader()
            writer.writerows(move_dependencies)
        write(ROOT / "include/gen8_species_map.h", emit_species_header())
        write(ROOT / "src/data/gen8/species_map.c", emit_species_c(species_map))
        write(ROOT / "include/gen8_conversion_status.h", emit_readiness_header(counts))
        write_json(ROOT / "data/pokemon/gen8_species_map.json", species_map)
        write_json(ROOT / "data/pokemon/gen8_level_up_learnsets.json", learnsets)
        # Compact, review-only JSON. It is deliberately not linked into
        # gSpeciesInfo until IDs, complete field coverage and runtime storage are assigned.
        write_json(ROOT / "data/pokemon/gen8_species_info_compact.json", info_result["compact_records"])
        write_json(ROOT / "data/pokemon/gen8_species_info_unresolved.json", info_result["unresolved_records"])

    return report

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    try:
        report = generate(check=args.check)
        print(json.dumps(report["counts"], indent=2))
        if args.check:
            assert report["counts"]["canonical_dex_entries"] == 898
            assert report["counts"]["canonical_species_info_covered"] == 898
            assert report["counts"]["canonical_species_info_missing"] == 0
            assert report["readiness"]["species_info_complete"] is True
        print("PASS: staging extraction completed; production IDs and save layouts untouched.")
        return 0
    except (OSError, RuntimeError, ValueError, KeyError) as e:
        print(f"GEN8 CONVERSION FAILED: {e}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
