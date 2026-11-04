#!/usr/bin/env python3
"""Regression checks for bounds-checked species evolution-table access."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADER = ROOT / "include/pokemon.h"
POKEMON = ROOT / "src/pokemon.c"
EVOLUTION_SCENE = ROOT / "src/evolution_scene.c"
DAYCARE = ROOT / "src/daycare.c"
REPORT = ROOT / "reports/gen8-conversion/evolution_access_audit.json"


def main() -> int:
    header = HEADER.read_text(encoding="utf-8")
    pokemon = POKEMON.read_text(encoding="utf-8")
    scene = EVOLUTION_SCENE.read_text(encoding="utf-8")
    daycare = DAYCARE.read_text(encoding="utf-8")

    assert "const struct Evolution *GetEvolutionTableSafe(u16 species);" in header

    accessor_start = pokemon.index(
        "const struct Evolution *GetEvolutionTableSafe(u16 species)"
    )
    accessor_end = pokemon.index(
        "const struct SpeciesInfo *GetSpeciesInfoSafe(u16 species)",
        accessor_start,
    )
    accessor = pokemon[accessor_start:accessor_end]
    assert "static const struct Evolution sEmptyEvolutionTable[EVOS_PER_MON] = {0};" in accessor
    assert "if (species >= NUM_SPECIES)" in accessor
    assert "return sEmptyEvolutionTable;" in accessor
    assert "return gEvolutionTable[species];" in accessor

    evolution_start = pokemon.index(
        "u16 GetEvolutionTargetSpecies(struct Pokemon *mon, u8 mode, u16 evolutionItem)"
    )
    evolution_end = pokemon.index("u16 HoennPokedexNumToSpecies", evolution_start)
    evolution_function = pokemon[evolution_start:evolution_end]
    assert "const struct Evolution *evolutions = GetEvolutionTableSafe(species);" in evolution_function
    assert "evolutions[i].method" in evolution_function
    assert "gEvolutionTable[" not in evolution_function

    shedinja_start = scene.index(
        "static void CreateShedinja(u16 preEvoSpecies, struct Pokemon *mon)"
    )
    shedinja_end = scene.index(
        "// States for the main switch in Task_EvolutionScene", shedinja_start
    )
    shedinja_function = scene[shedinja_start:shedinja_end]
    assert "GetEvolutionTableSafe(preEvoSpecies)" in shedinja_function
    assert "targetSpecies < NUM_SPECIES" in shedinja_function
    assert "gEvolutionTable[" not in shedinja_function
    assert "extern struct Evolution gEvolutionTable" not in scene

    egg_start = daycare.index("static u16 GetEggSpecies(u16 species)")
    egg_end = daycare.index("\nstatic ", egg_start + 10)
    egg_function = daycare[egg_start:egg_end]
    assert "evolutions = GetEvolutionTableSafe(j);" in egg_function
    assert "evolutions[k].targetSpecies" in egg_function
    assert "gEvolutionTable[" not in egg_function

    direct_indexes = []
    accessor_calls = 0
    accessor_files = set()
    for path in sorted((ROOT / "src").rglob("*.c")):
        source = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT).as_posix()
        calls = source.count("GetEvolutionTableSafe(")
        if "const struct Evolution *GetEvolutionTableSafe(u16 species)" in source:
            calls -= 1  # Exclude the function definition from call-site totals.
        if calls:
            accessor_calls += calls
            accessor_files.add(relative)
        for line_number, line in enumerate(source.splitlines(), 1):
            if "gEvolutionTable[" in line:
                direct_indexes.append({
                    "path": relative,
                    "line": line_number,
                    "source": line.strip(),
                })

    expected_direct_indexes = [
        {
            "path": "src/pokemon.c",
            "line": next(
                n for n, line in enumerate(pokemon.splitlines(), 1)
                if "return gEvolutionTable[species];" in line
            ),
            "source": "return gEvolutionTable[species];",
        }
    ]
    assert direct_indexes == expected_direct_indexes, direct_indexes
    assert accessor_calls == 3, accessor_calls
    assert accessor_files == {"src/pokemon.c", "src/evolution_scene.c", "src/daycare.c"}

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "accessor_call_sites": accessor_calls,
        "files_using_accessor": len(accessor_files),
        "unguarded_direct_indexes": 0,
        "guarded_table_index_sites": len(direct_indexes),
        "bounds_guard": "species >= NUM_SPECIES",
        "invalid_species_fallback": "zeroed evolution row (method 0)",
        "runtime_species_ids_allocated": False,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("PASS: evolution-table consumers use the bounds-checked accessor.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
