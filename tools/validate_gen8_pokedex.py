#!/usr/bin/env python3
"""Validate Emerald Gen 8 manifest coverage and required per-species assets.

The script is intentionally a preflight validator, not a placeholder asset
generator. It fails until each new species has real source metadata and all
required graphics; it never aliases a missing sprite to another Pokémon.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EXPECTED = 898
REQUIRED_ASSETS = (
    "front.png",
    "anim_front.png",
    "back.png",
    "icon.png",
    "footprint.png",
    "normal.pal",
    "shiny.pal",
)
ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    manifest_path = ROOT / "data/pokemon/gen8_species_manifest.json"
    if not manifest_path.exists():
        print("FAIL: manifest missing; run tools/gen8_pokedex_manifest.py first")
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    species = manifest.get("species", [])
    numbers = [entry.get("national_dex") for entry in species]
    slugs = [entry.get("slug") for entry in species]
    if manifest.get("species_count") != EXPECTED or len(species) != EXPECTED:
        print(f"FAIL: manifest must contain exactly {EXPECTED} species")
        return 1
    if numbers != list(range(1, EXPECTED + 1)):
        print("FAIL: National Dex numbering is incomplete or unordered")
        return 1
    if len(set(slugs)) != EXPECTED:
        print("FAIL: duplicate species slugs in manifest")
        return 1

    missing = []
    for entry in species:
        folder = ROOT / "graphics/pokemon" / entry["slug"]
        for asset in REQUIRED_ASSETS:
            if not (folder / asset).is_file():
                missing.append(f"{entry['national_dex']:03d} {entry['slug']}: {asset}")

    if missing:
        print(f"FAIL: {len(missing)} required graphics files missing")
        for item in missing[:100]:
            print("  " + item)
        if len(missing) > 100:
            print(f"  ... and {len(missing) - 100} more")
        return 1

    source_files = {
        "species_info": ROOT / "src/data/pokemon/species_info.h",
        "evolution": ROOT / "src/data/pokemon/evolution.h",
        "learnset_pointers": ROOT / "src/data/pokemon/level_up_learnset_pointers.h",
        "pokedex_entries": ROOT / "src/data/pokemon/pokedex_entries.h",
    }
    for label, path in source_files.items():
        if not path.is_file():
            print(f"FAIL: required C data source missing: {path}")
            return 1

    print(f"PASS: {EXPECTED} manifest records and all required assets found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
