#!/usr/bin/env python3
"""Preflight validator for Gen 8 expansion prerequisites.

Checks canonical National Dex coverage and reports which new species still
lack Emerald-compatible graphics. It deliberately does not treat aliases,
forms, or the legacy Nidoran/Unown names as simple lowercase folder slugs.
It is a data readiness gate, not proof that the full Gen 8 expansion exists.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = 898
REQUIRED_ASSETS = ("front.png", "anim_front.png", "back.png", "icon.png",
                   "footprint.png", "normal.pal", "shiny.pal")
SPECIAL_SLUGS = {
    "nidoran-f": "nidoran_f",
    "nidoran-m": "nidoran_m",
    "mr-mime": "mr_mime",
    "ho-oh": "ho_oh",
    "mime-jr": "mime_jr",
    "porygon-z": "porygon_z",
    "type-null": "type_null",
    "jangmo-o": "jangmo_o",
    "hakamo-o": "hakamo_o",
    "kommo-o": "kommo_o",
    "tapu-koko": "tapu_koko",
    "tapu-lele": "tapu_lele",
    "tapu-bulu": "tapu_bulu",
    "tapu-fini": "tapu_fini",
    "mr-rime": "mr_rime",
    "sirfetchd": "sirfetchd",
    "flabebe": "flabebe",
}


def main() -> int:
    path = ROOT / "data/pokemon/gen8_species_manifest.json"
    if not path.is_file():
        print("FAIL: National Dex manifest is missing")
        return 2
    manifest = json.loads(path.read_text(encoding="utf-8"))
    species = manifest.get("species", [])
    if manifest.get("species_count") != EXPECTED or len(species) != EXPECTED:
        print(f"FAIL: expected {EXPECTED} species records")
        return 1
    if [s.get("national_dex") for s in species] != list(range(1, EXPECTED + 1)):
        print("FAIL: National Dex numbers must be continuous from 1 to 898")
        return 1
    slugs = [s.get("slug") for s in species]
    if len(set(slugs)) != EXPECTED:
        print("FAIL: duplicated species slug")
        return 1

    missing: list[str] = []
    for s in species[386:]:
        slug = s["slug"]
        folder_name = SPECIAL_SLUGS.get(slug, slug.replace("-", "_"))
        folder = ROOT / "graphics/pokemon" / folder_name
        absent = [name for name in REQUIRED_ASSETS if not (folder / name).is_file()]
        if absent:
            missing.append(f"#{s['national_dex']} {slug}: {', '.join(absent)}")

    if missing:
        print(f"BLOCKED: {len(missing)} new species still lack one or more required Emerald graphics.")
        print("No placeholder sprites or cross-species aliases are generated.")
        for line in missing[:120]:
            print("  " + line)
        if len(missing) > 120:
            print(f"  ... and {len(missing) - 120} more species")
        return 1

    print("PASS: all 512 Gen 2-8 species graphics are present")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
