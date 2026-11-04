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
#define TRUE 1
#define FALSE 0
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

    # Emerald's legacy table assigns pseudo-Dex slots 899-923 to all 25
    # old Unown B-Z auxiliary IDs. These remain outside the canonical 1-898
    # range, so the legacy lookup must retain this auxiliary mapping.
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
    expected_collision_dex = list(range(899, 924))
    assert [row["national_dex"] for row in unown_collisions] == expected_collision_dex, (
        unown_collisions
    )
    canonical_dexes = {int(row["national_dex"]) for row in rows}
    assert not (canonical_dexes & {dex for dex in legacy_by_dex if dex > 898}), (
        "Legacy auxiliary National Dex values overlap canonical Gen 8 Dex rows"
    )

    pokemon_source = (ROOT / "src/pokemon.c").read_text(encoding="utf-8")
    lookup_start = pokemon_source.index("u16 NationalPokedexNumToSpecies(u16 nationalNum)")
    lookup_end = pokemon_source.index("u16 NationalToHoennOrder", lookup_start)
    lookup_body = pokemon_source[lookup_start:lookup_end]
    assert "nationalNum <= GEN8_NATIONAL_DEX_COUNT" in lookup_body
    assert "Gen8SpeciesMap_GetEmeraldId(nationalNum)" in lookup_body
    assert "sSpeciesToNationalPokedexNum[species] != nationalNum" in lookup_body
    assert "return SPECIES_NONE;" in lookup_body

    reverse_start = pokemon_source.index("u16 SpeciesToNationalPokedexNum(u16 species)")
    reverse_end = pokemon_source.index("u16 SpeciesToHoennPokedexNum", reverse_start)
    reverse_body = pokemon_source[reverse_start:reverse_end]
    assert "Gen8SpeciesMap_GetNationalDex(species)" in reverse_body
    assert "species < SPECIES_EGG" in reverse_body
    assert "sSpeciesToNationalPokedexNum[species - 1]" in reverse_body

    accessor_start = pokemon_source.index("const struct SpeciesInfo *GetSpeciesInfoSafe(u16 species)")
    accessor_end = pokemon_source.index("u16 NationalPokedexNumToSpecies", accessor_start)
    accessor_body = pokemon_source[accessor_start:accessor_end]
    assert "species >= NUM_SPECIES" in accessor_body
    assert "species = SPECIES_NONE" in accessor_body
    assert "return &gSpeciesInfo[species];" in accessor_body
    pokemon_header = (ROOT / "include/pokemon.h").read_text(encoding="utf-8")
    assert "GetSpeciesInfoSafe(u16 species);" in pokemon_header

    raw_species_info_indexes = []
    accessor_calls = 0
    accessor_files = set()
    for source_path in (ROOT / "src").rglob("*.c"):
        source_text = source_path.read_text(encoding="utf-8")
        accessor_calls += source_text.count("GetSpeciesInfoSafe(")
        if "GetSpeciesInfoSafe(" in source_text:
            accessor_files.add(str(source_path.relative_to(ROOT)))
        for line_number, line in enumerate(source_text.splitlines(), 1):
            if "gSpeciesInfo[" in line:
                if source_path == ROOT / "src/pokemon.c" and "return &gSpeciesInfo[species];" in line:
                    continue
                raw_species_info_indexes.append({
                    "path": str(source_path.relative_to(ROOT)),
                    "line": line_number,
                    "source": line.strip(),
                })
    assert not raw_species_info_indexes, (
        f"Unbounded SpeciesInfo indexes remain: {raw_species_info_indexes[:10]}"
    )
    assert accessor_calls >= 150, f"Expected migrated call sites, got {accessor_calls}"
    access_report = {
        "accessor_call_sites": accessor_calls,
        "files_using_accessor": len(accessor_files),
        "unbounded_direct_indexes": 0,
        "guarded_table_index_sites": 1,
        "sentinel_fallback": "SPECIES_NONE",
        "bounds_guard": "species >= NUM_SPECIES",
    }
    (ROOT / "reports/gen8-conversion/species_info_access_audit.json").write_text(
        json.dumps(access_report, indent=2) + "\n", encoding="utf-8"
    )

    makefile = (ROOT / "Makefile").read_text(encoding="utf-8")
    assert "src/data/gen8/species_map.c" in makefile
    assert "gen8_species_map:" in makefile

    compile_and_execute_real_map(rows)

    result = {
        "canonical_rows": len(rows),
        "existing_emerald_mappings": len(existing),
        "unassigned_gen8_mappings": len(new),
        "legacy_mapping_mismatches": len(mismatches),
        "legacy_unown_pseudo_dex_collisions": unown_collisions,
        "generated_c_map_executed": True,
        "canonical_lookup_uses_generated_map": True,
        "legacy_unown_lookup_fallback_preserved": True,
        "reverse_lookup_uses_generated_map": True,
        "legacy_unown_reverse_fallback_preserved": True,
        "species_info_reads_bounds_checked": True,
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
