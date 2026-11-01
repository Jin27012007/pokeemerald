#!/usr/bin/env python3
"""Validate Gen 8 source-data coverage and the complete Emerald graphics contract.

A manifest passing alone is not enough to raise NUM_SPECIES. This validator
checks that the actual C sources declare every new National Dex species and
that all species graphics needed by the Emerald loader exist. It reports
missing assets and missing C entries without generating fake records.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EXPECTED = 898
ROOT = Path(__file__).resolve().parents[1]
REQUIRED_ASSETS = (
    "front.png", "anim_front.png", "back.png", "icon.png",
    "footprint.png", "normal.pal", "shiny.pal",
)
C_SOURCE_CONTRACT = {
    "src/data/pokemon/species_info.h": (r"\[SPECIES_([A-Z0-9_]+)\]\s*=", "species metadata"),
    "src/data/pokemon/evolution.h": (r"\[SPECIES_([A-Z0-9_]+)\]\s*=", "evolution rows"),
    "src/data/pokemon/level_up_learnset_pointers.h": (r"\[SPECIES_([A-Z0-9_]+)\]\s*=", "learnset pointers"),
    "src/data/pokemon/pokedex_entries.h": (r"\[NATIONAL_DEX_([A-Z0-9_]+)\]\s*=", "National Dex entries"),
    "src/data/pokemon_graphics/front_pic_table.h": (r"SPECIES_SPRITE\(([A-Z0-9_]+),", "front sprite table"),
    "src/data/pokemon_graphics/back_pic_table.h": (r"SPECIES_SPRITE\(([A-Z0-9_]+),", "back sprite table"),
    "src/data/pokemon_graphics/footprint_table.h": (r"\[SPECIES_([A-Z0-9_]+)\]\s*=", "footprint table"),
    "src/data/pokemon_graphics/palette_table.h": (r"SPECIES_PAL\(([A-Z0-9_]+),", "palette table"),
    "src/data/pokemon_graphics/shiny_palette_table.h": (r"SPECIES_SHINY_PAL\(([A-Z0-9_]+),", "shiny palette table"),
}


def normalize(name: str) -> str:
    return name.upper().replace("-", "_").replace(".", "")


def main() -> int:
    manifest_path = ROOT / "data/pokemon/gen8_species_manifest.json"
    if not manifest_path.is_file():
        print("FAIL: manifest missing; run tools/gen8_pokedex_manifest.py")
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    species = manifest.get("species", [])
    if manifest.get("species_count") != EXPECTED or len(species) != EXPECTED:
        print(f"FAIL: expected exactly {EXPECTED} species")
        return 1
    if [s.get("national_dex") for s in species] != list(range(1, EXPECTED + 1)):
        print("FAIL: National Dex numbering is not continuous 1..898")
        return 1
    if len({s.get("slug") for s in species}) != EXPECTED:
        print("FAIL: duplicate species slugs")
        return 1

    failures = []
    # Include all 898 species in the asset contract. Existing Emerald species
    # may have special filenames/forms, so only report paths absent on disk.
    for s in species:
        folder = ROOT / "graphics/pokemon" / s["slug"]
        for asset in REQUIRED_ASSETS:
            if not (folder / asset).is_file():
                failures.append(f"asset: #{s['national_dex']} {s['slug']}/{asset}")

    # For each Gen 4-8 addition, require matching C table records. Existing
    # Gen 1-3 sources use legacy IDs/order and are separately preserved.
    additions = species[386:]
    for rel, (pattern, label) in C_SOURCE_CONTRACT.items():
        path = ROOT / rel
        if not path.is_file():
            failures.append(f"source missing: {rel}")
            continue
        text = path.read_text(encoding="utf-8")
        declared = set(re.findall(pattern, text))
        for s in additions:
            ident = normalize(s["slug"])
            if ident not in declared:
                failures.append(f"{label}: missing {s['species_id']} ({s['slug']})")

    if failures:
        print(f"FAIL: {len(failures)} Gen 8 coverage errors")
        for item in failures[:200]:
            print("  " + item)
        if len(failures) > 200:
            print(f"  ... and {len(failures) - 200} more")
        return 1

    print("PASS: 898 species have the required graphics and C data coverage")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
