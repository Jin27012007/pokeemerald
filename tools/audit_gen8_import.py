#!/usr/bin/env python3
"""Audit CFRU's Gen 8 source data against Emerald before importing.

This audit intentionally preserves Emerald species IDs and never rewrites
species or move IDs. It reports source compatibility blockers before C-table
generation is permitted.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "tools/vendor/cfru"
SOURCE_FILES = {
    "species": SOURCE_DIR / "include/constants/species.h",
    "pokedex": SOURCE_DIR / "include/constants/pokedex.h",
    "moves": SOURCE_DIR / "include/constants/moves.h",
    "learnsets": SOURCE_DIR / "src/Tables/level_up_learnsets.c",
}
TARGET_FILES = {
    "species": ROOT / "include/constants/species.h",
    "moves": ROOT / "include/constants/moves.h",
    "learnsets": ROOT / "src/data/pokemon/level_up_learnsets.h",
}
MANIFEST = ROOT / "data/pokemon/gen8_species_manifest.json"

ALIASES = {
    "BASCULIN": ("BASCULIN_RED", "BASCULIN_BLUE"),
    "MINIOR": ("MINIOR_SHIELD", "MINIOR_RED"),
    "ALCREMIE": ("ALCREMIE_STRAWBERRY", "ALCREMIE_BERRY"),
    "URSHIFU": ("URSHIFU_SINGLE",),
}


def read(path: Path) -> str:
    if not path.is_file():
        raise RuntimeError(f"Missing source file: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def parse_defines(text: str, prefix: str) -> dict[str, int]:
    result: dict[str, int] = {}
    pattern = re.compile(
        rf"^#define {re.escape(prefix)}([A-Z0-9_]+) (0x([0-9A-Fa-f]+)|(\d+))$",
        re.MULTILINE,
    )
    for match in pattern.finditer(text):
        name = match.group(1)
        if name in result:
            raise RuntimeError(f"Duplicate {prefix}{name} definition")
        result[name] = int(match.group(3), 16) if match.group(3) else int(match.group(4))
    return result


def camel_species(name: str) -> str:
    return "".join(part.title() for part in name.lower().split("_"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", default="reports/gen8_import_compatibility.json")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    try:
        manifest = json.loads(read(MANIFEST))
        species = manifest.get("species", [])
        if manifest.get("species_count") != 898 or len(species) != 898:
            raise RuntimeError("Manifest is not exactly the canonical 898-species list")

        target_species = parse_defines(read(TARGET_FILES["species"]), "SPECIES_")
        target_moves = parse_defines(read(TARGET_FILES["moves"]), "MOVE_")
        source_species = parse_defines(read(SOURCE_FILES["species"]), "SPECIES_")
        source_dex = parse_defines(read(SOURCE_FILES["pokedex"]), "NATIONAL_DEX_")
        source_moves = parse_defines(read(SOURCE_FILES["moves"]), "MOVE_")
        source_learnsets = read(SOURCE_FILES["learnsets"])
        read(TARGET_FILES["learnsets"])  # Confirm expected target structure exists.

        missing = [
            item for item in species
            if item["national_dex"] >= 387
            and item["species_id"].removeprefix("SPECIES_") not in target_species
        ]

        source_names: dict[str, str] = {}
        unresolved_dex: list[dict[str, object]] = []
        for item in missing:
            name = item["species_id"].removeprefix("SPECIES_")
            dex = item["national_dex"]
            if source_dex.get(name) == dex and name in source_species:
                source_names[name] = name
                continue
            candidates = [candidate for candidate in ALIASES.get(name, ()) if candidate in source_species]
            if candidates:
                source_names[name] = candidates[0]
            else:
                unresolved_dex.append({"dex": dex, "name": name})

        missing_learnsets: list[dict[str, object]] = []
        used_moves: set[str] = set()
        blocks_found = 0
        for item in missing:
            name = item["species_id"].removeprefix("SPECIES_")
            source_name = source_names.get(name)
            if not source_name:
                continue
            symbol = camel_species(source_name)
            pattern = re.compile(
                rf"static const struct LevelUpMove s{re.escape(symbol)}"
                rf"LevelUpLearnset\[\] = \{{([\s\S]*?)\n\}};"
            )
            match = pattern.search(source_learnsets)
            if not match and name == "URSHIFU":
                match = re.search(
                    r"static const struct LevelUpMove sUrshifuLevelUpLearnset"
                    r"\[\] = \{([\s\S]*?)\n\};",
                    source_learnsets,
                )
            if not match:
                missing_learnsets.append({"dex": item["national_dex"], "name": name})
                continue
            blocks_found += 1
            used_moves.update(re.findall(
                r"LEVEL_UP_MOVE\(\s*\d+\s*,\s*MOVE_([A-Z0-9_]+)\s*\)",
                match.group(1),
            ))

        missing_moves = sorted(used_moves - set(target_moves))
        report = {
            "scope": "National Dex 387-898; canonical species only",
            "existing_emerald_species_ids_preserved": True,
            "existing_species_definitions": len(target_species),
            "new_species_to_map": len(missing),
            "source_species_aliases": source_names,
            "unresolved_source_dex": unresolved_dex,
            "learnset_blocks_found": blocks_found,
            "unresolved_learnsets": missing_learnsets,
            "unique_new_species_moves": len(used_moves),
            "missing_move_identifiers": missing_moves,
            "source_move_definitions": len(source_moves),
            "target_move_definitions": len(target_moves),
            "ready_for_import": not unresolved_dex and not missing_learnsets and not missing_moves,
        }
        output = ROOT / args.json
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"New species to map: {len(missing)}")
        print(f"Learnset blocks resolved: {blocks_found}/{len(missing)}")
        print(f"Unique new move identifiers: {len(used_moves)}")
        print(f"Move identifiers missing in Emerald: {len(missing_moves)}")
        print(f"Report written: {output.relative_to(ROOT)}")
        if missing_moves:
            print("Missing move IDs: " + ", ".join(missing_moves[:30]))
        if unresolved_dex:
            print(f"Unresolved source species identities: {len(unresolved_dex)}")
        if missing_learnsets:
            print(f"Unresolved learnsets: {len(missing_learnsets)}")
        return 1 if args.strict and not report["ready_for_import"] else 0
    except (OSError, json.JSONDecodeError, RuntimeError, KeyError, TypeError) as exc:
        print(f"GEN 8 IMPORT AUDIT FAILED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
