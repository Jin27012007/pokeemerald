#!/usr/bin/env python3
"""Generate a National Dex manifest for the 898 Gen 1-8 species.

This deliberately does NOT rewrite C headers or change NUM_SPECIES. The
Emerald source tree must receive species data, learnsets, evolution data,
dex text, cry IDs and every graphics table before the enum limit is raised.
The manifest makes the source list deterministic and provides a completeness
gate for a later import pipeline.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

SPECIES_COUNT = 898
API = "https://pokeapi.co/api/v2/pokemon-species?limit=1000"


def load_species() -> list[dict]:
    request = urllib.request.Request(API, headers={"User-Agent": "LilycoveAdoption-Gen8-Importer/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    records = sorted(payload["results"], key=lambda item: int(item["url"].rstrip("/").split("/")[-1]))
    records = [item for item in records if int(item["url"].rstrip("/").split("/")[-1]) <= SPECIES_COUNT]
    if len(records) != SPECIES_COUNT:
        raise RuntimeError(f"Expected {SPECIES_COUNT} National Dex species, got {len(records)}")
    return [
        {
            "national_dex": index,
            "slug": item["name"],
            "species_id": f"SPECIES_{item['name'].upper().replace('-', '_').replace('.', '')}",
        }
        for index, item in enumerate(records, start=1)
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/pokemon/gen8_species_manifest.json")
    args = parser.parse_args()
    try:
        records = load_species()
    except Exception as exc:
        print(f"ERROR: cannot fetch complete National Dex manifest: {exc}", file=sys.stderr)
        return 2

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "scope": "National Dex generations 1-8",
        "species_count": SPECIES_COUNT,
        "first": records[0],
        "last": records[-1],
        "species": records,
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(records)} species to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
