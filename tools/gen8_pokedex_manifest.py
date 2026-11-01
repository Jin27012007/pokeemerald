#!/usr/bin/env python3
"""Generate the canonical National Dex manifest for all 898 Gen 1-8 species.

This records species identity and ordering. It does not create Emerald-ready
C structs or graphics; those are handled by the import pipeline in separate,
validated steps.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

SPECIES_COUNT = 898
API = "https://pokeapi.co/api/v2/pokemon-species?limit=1000"


def fetch_species() -> list[dict]:
    request = urllib.request.Request(
        API,
        headers={"User-Agent": "LilycoveAdoption-Gen8-Importer/1.0"},
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        payload = json.load(response)

    records = []
    for entry in payload.get("results", []):
        dex_id = int(entry["url"].rstrip("/").split("/")[-1])
        if 1 <= dex_id <= SPECIES_COUNT:
            name = entry["name"]
            records.append({
                "national_dex": dex_id,
                "slug": name,
                "species_id": "SPECIES_" + name.upper().replace("-", "_").replace(".", ""),
            })

    records.sort(key=lambda item: item["national_dex"])
    ids = [item["national_dex"] for item in records]
    if ids != list(range(1, SPECIES_COUNT + 1)):
        raise RuntimeError(f"Expected continuous National Dex 1-{SPECIES_COUNT}; got {len(records)} records")
    if len({item["slug"] for item in records}) != SPECIES_COUNT:
        raise RuntimeError("Duplicate species slug in source data")
    return records


def render() -> str:
    records = fetch_species()
    data = {
        "scope": "National Dex generations 1-8",
        "species_count": SPECIES_COUNT,
        "first": records[0],
        "last": records[-1],
        "species": records,
    }
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/pokemon/gen8_species_manifest.json")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    output = Path(args.output)

    try:
        result = render()
    except Exception as exc:
        print(f"ERROR: unable to retrieve complete species source: {exc}", file=sys.stderr)
        return 2

    if args.check:
        if not output.is_file() or output.read_text(encoding="utf-8") != result:
            print(f"FAIL: {output} is missing or differs from canonical species data")
            return 1
        print(f"PASS: manifest contains {SPECIES_COUNT} ordered species")
        return 0

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result, encoding="utf-8")
    print(f"Wrote {SPECIES_COUNT} species to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
