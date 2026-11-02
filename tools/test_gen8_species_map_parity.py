#!/usr/bin/env python3
"""Validate the generated Gen 8 species map against Emerald's legacy Dex table."""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "gen8_convert_emerald", ROOT / "tools/gen8_convert_emerald.py"
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
import sys
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)

REPORT = ROOT / "reports/gen8-conversion/species_id_mapping.json"
OUT = ROOT / "reports/gen8-conversion/species_map_parity.json"


def compile_and_execute_real_map(rows: list[dict]) -> None:
    compiler = shutil.which("cc") or shutil.which("gcc") or shutil.which("clang")
    assert compiler, "A C compiler is required for the generated species-map test"

    expected = [0] * 899
    for row in rows:
        dex = int(row["national_dex"])
        internal = row["emerald_internal_id"]
        expected[dex] = 0 if internal is None else int(internal)

    expected_values = ",\n    ".join(str(value) for value in expected)
    harness = f"""#include <stdint.h>
#include "gen8_species_map.h"
static const u16 sExpected[899] = {{
    {expected_values}
}};
int main(void)
{{
    u16 dex;
    for (dex = 0; dex <= GEN8_NATIONAL_DEX_COUNT; dex++)
    {{
        u16 internal = Gen8SpeciesMap_GetEmeraldId(dex);
        if (internal != sExpected[dex]) return 1;
        if (internal != SPECIES_NONE)
        {{
            if (!Gen8SpeciesMap_IsAssigned(dex)) return 2;
            if (!Gen8SpeciesMap_IsValidInternalId(internal)) return 3;
            if (Gen8SpeciesMap_GetNationalDex(internal) != dex) return 4;
        }}
        else if (Gen8SpeciesMap_IsAssigned(dex)) return 5;
    }}
    if (Gen8SpeciesMap_GetEmeraldId(899) != SPECIES_NONE) return 6;
    if (Gen8SpeciesMap_GetEmeraldId(65535) != SPECIES_NONE) return 7;
    if (Gen8SpeciesMap_IsValidInternalId(SPECIES_NONE)) return 8;
    if (Gen8SpeciesMap_IsValidInternalId(SPECIES_EGG)) return 9;
    if (Gen8SpeciesMap_IsValidInternalId(SPECIES_UNOWN_B)) return 10;
    if (Gen8SpeciesMap_GetNationalDex(SPECIES_EGG) != 0) return 11;
    if (Gen8SpeciesMap_GetNationalDex(SPECIES_UNOWN_B) != 0) return 12;
    return 0;
}}
"""

    with tempfile.TemporaryDirectory(prefix="gen8-real-map-") as temporary:
        temp = Path(temporary)
        (temp / "global.h").write_text(
            """#ifndef TEST_GLOBAL_H
#define TEST_GLOBAL_H
#include <stdint.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef int32_t bool32;
#include "constants/species.h"
#endif
""",
            encoding="utf-8",
        )
        generated_header = ROOT / "include/gen8_species_map.h"
        (temp / "gen8_species_map.h").write_text(
            generated_header.read_text(encoding="utf-8"), encoding="utf-8"
        )
        (temp / "test.c").write_text(harness, encoding="utf-8")
        executable = temp / "gen8-map-test"
        command = [
            compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
            "-I", str(temp), "-I", str(ROOT / "include"),
            str(ROOT / "src/data/gen8/species_map.c"),
            str(temp / "test.c"), "-o", str(executable),
        ]
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
            subprocess.run([str(executable)], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as error:
            raise AssertionError(error.stderr or error.stdout) from error


def main() -> int:
    rows = json.loads(REPORT.read_text(encoding="utf-8"))
    assert len(rows) == 898, f"Expected 898 canonical rows, got {len(rows)}"
    existing = [row for row in rows if row["emerald_internal_id"] is not None]
    new = [row for row in rows if row["emerald_internal_id"] is None]
    assert len(existing) == 386, len(existing)
    assert len(new) == 512, len(new)

    species_text = (ROOT / "include/constants/species.h").read_text(encoding="utf-8")
    pokedex_text = (ROOT / "include/constants/pokedex.h").read_text(encoding="utf-8")
    pokemon_text = (ROOT / "src/pokemon.c").read_text(encoding="utf-8")
    species_ids = {
        row["symbol"]: row["id"]
        for row in module.symbols(species_text, "SPECIES_")
    }
    dex_ids = {
        row["symbol"]: row["id"]
        for row in module.symbols(pokedex_text, "NATIONAL_DEX_", enum=True)
    }

    table_start = pokemon_text.index(
        "static const u16 sSpeciesToNationalPokedexNum"
    )
    table_end = pokemon_text.index("};", table_start)
    table_body = pokemon_text[table_start:table_end]
    legacy_entries = re.findall(
        r"SPECIES_TO_NATIONAL\(([A-Z0-9_]+)\)", table_body
    )
    assert legacy_entries, "Could not parse the legacy National Dex table"

    # The legacy lookup scans internal IDs in ascending order. For duplicate
    # Dex values (the old Unown auxiliary entries), the lowest ID wins.
    legacy_by_dex: dict[int, int] = {}
    for symbol in legacy_entries:
        if symbol not in species_ids:
            raise AssertionError(f"Legacy table species constant missing: {symbol}")
        if symbol not in dex_ids:
            raise AssertionError(f"Legacy table National Dex constant missing: {symbol}")
        dex = dex_ids[symbol]
        internal = species_ids[symbol]
        legacy_by_dex[dex] = min(internal, legacy_by_dex.get(dex, internal))

    mismatches = []
    for row in existing:
        dex = int(row["national_dex"])
        internal = int(row["emerald_internal_id"])
        if legacy_by_dex.get(dex) != internal:
            mismatches.append({
                "national_dex": dex,
                "expected_emerald_id": internal,
                "legacy_emerald_id": legacy_by_dex.get(dex),
            })
    assert not mismatches, f"Existing Emerald mappings changed: {mismatches[:10]}"

    # Emerald's legacy table assigns pseudo-Dex slots 899-920 to the old
    # Unown B-Z auxiliary IDs. Those collide with canonical Gen 4 species
    # Dex numbers beyond the canonical 1-898 range, so the legacy lookup must retain this auxiliary mapping.
    unown_collisions = []
    for dex, legacy_id in sorted(legacy_by_dex.items()):
        if dex > 898:
            unown_collisions.append({
                "national_dex": dex,
                "legacy_internal_id": legacy_id,
            })
            assert 252 <= legacy_id <= 276, (
                f"Unexpected legacy auxiliary entry at Dex {dex}: {legacy_id}"
            )
    expected_collision_dex = list(range(899, 921))
    assert [row["national_dex"] for row in unown_collisions] == expected_collision_dex, (
        unown_collisions
    )
    canonical_dexes = {int(row["national_dex"]) for row in rows}
    assert not (canonical_dexes & {dex for dex in legacy_by_dex if dex > 898}), (
        "Legacy auxiliary National Dex values overlap canonical Gen 8 Dex rows"
    )

    compile_and_execute_real_map(rows)

    result = {
        "canonical_rows": len(rows),
        "existing_emerald_mappings": len(existing),
        "unassigned_gen8_mappings": len(new),
        "legacy_mapping_mismatches": len(mismatches),
        "legacy_unown_pseudo_dex_collisions": unown_collisions,
        "generated_c_map_executed": True,
        "legacy_unown_pseudo_dex_slots": expected_collision_dex,
        "canonical_gen8_dex_conflicts_with_legacy_unown_slots": False,
        "legacy_lookup_replacement_allowed": False,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("PASS: all 386 existing mappings match Emerald; all 898 generated map entries execute.")
    print("PASS: legacy Unown pseudo-Dex collisions 387-411 are explicitly preserved.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
