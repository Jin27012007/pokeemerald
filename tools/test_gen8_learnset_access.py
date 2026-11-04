#!/usr/bin/env python3
"""Regression checks for bounds-checked level-up and TM/HM learnset access."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEADER = ROOT / "include/pokemon.h"
POKEMON = ROOT / "src/pokemon.c"
APPRENTICE = ROOT / "src/apprentice.c"
REPORT = ROOT / "reports/gen8-conversion/learnset_access_audit.json"


def section(source: str, start: str, end: str) -> str:
    start_at = source.index(start)
    end_at = source.index(end, start_at)
    return source[start_at:end_at]


def main() -> int:
    header = HEADER.read_text(encoding="utf-8")
    pokemon = POKEMON.read_text(encoding="utf-8")
    apprentice = APPRENTICE.read_text(encoding="utf-8")

    assert "const u16 *GetLevelUpLearnsetSafe(u16 species);" in header

    level_accessor = section(
        pokemon,
        "const u16 *GetLevelUpLearnsetSafe(u16 species)",
        "static const u32 *GetTMHMLearnsetWordsSafe(u16 species)",
    )
    assert "static const u16 sEmptyLearnset[] = {LEVEL_UP_END};" in level_accessor
    assert "if (species >= NUM_SPECIES)" in level_accessor
    assert "return sEmptyLearnset;" in level_accessor
    assert "return gLevelUpLearnsets[species];" in level_accessor

    tmhm_accessor = section(
        pokemon,
        "static const u32 *GetTMHMLearnsetWordsSafe(u16 species)",
        "const struct SpeciesInfo *GetSpeciesInfoSafe(u16 species)",
    )
    assert "struct TMHMLearnset learnset;" in tmhm_accessor
    assert "u32 as_u32s[sizeof(struct TMHMLearnset) / sizeof(u32)];" in tmhm_accessor
    assert "sEmptyTMHMLearnset = {0};" in tmhm_accessor
    assert "if (species >= NUM_SPECIES)" in tmhm_accessor
    assert "return sEmptyTMHMLearnset.as_u32s;" in tmhm_accessor
    assert "return gTMHMLearnsets[species].as_u32s;" in tmhm_accessor

    give_initial = section(
        pokemon,
        "void GiveBoxMonInitialMoveset(struct BoxPokemon *boxMon)",
        "u16 MonTryLearningNewMove(struct Pokemon *mon, bool8 firstMove)",
    )
    assert "GetLevelUpLearnsetSafe(species)" in give_initial
    assert "learnset[i] != LEVEL_UP_END" in give_initial
    assert "gLevelUpLearnsets[" not in give_initial

    learn_move = section(
        pokemon,
        "u16 MonTryLearningNewMove(struct Pokemon *mon, bool8 firstMove)",
        "void DeleteFirstMoveAndGiveMoveToMon",
    )
    assert "GetLevelUpLearnsetSafe(species)" in learn_move
    assert "if (learnset[0] == LEVEL_UP_END)" in learn_move
    assert "learnset[sLearningMoveTableID] != LEVEL_UP_END" in learn_move
    assert "if (learnset[sLearningMoveTableID] == LEVEL_UP_END)" in learn_move
    assert "gLevelUpLearnsets[" not in learn_move

    can_mon_tmhm = section(
        pokemon,
        "u32 CanMonLearnTMHM(struct Pokemon *mon, u8 tm)",
        "u32 CanSpeciesLearnTMHM(u16 species, u8 tm)",
    )
    can_species_tmhm = section(
        pokemon,
        "u32 CanSpeciesLearnTMHM(u16 species, u8 tm)",
        "u8 GetMoveRelearnerMoves(struct Pokemon *mon, u16 *moves)",
    )
    for function in (can_mon_tmhm, can_species_tmhm):
        assert "GetTMHMLearnsetWordsSafe(species)" in function
        assert "learnset[" in function
        assert "gTMHMLearnsets[" not in function
        assert "index >= sizeof(struct TMHMLearnset) / sizeof(u32)" in function

    move_relearner = section(
        pokemon,
        "u8 GetMoveRelearnerMoves(struct Pokemon *mon, u16 *moves)",
        "u8 GetLevelUpMovesBySpecies(u16 species, u16 *moves)",
    )
    level_by_species = section(
        pokemon,
        "u8 GetLevelUpMovesBySpecies(u16 species, u16 *moves)",
        "u8 GetNumberOfRelearnableMoves(struct Pokemon *mon)",
    )
    number_relearnable = section(
        pokemon,
        "u8 GetNumberOfRelearnableMoves(struct Pokemon *mon)",
        "u16 SpeciesToPokedexNum(u16 species)",
    )
    for function in (move_relearner, level_by_species, number_relearnable):
        assert "GetLevelUpLearnsetSafe(species)" in function
        assert "learnset[" in function
        assert "gLevelUpLearnsets[" not in function

    random_alternate = section(
        apprentice,
        "static u16 GetRandomAlternateMove(u8 monId)\n{",
        "static bool8 TrySetMove(u8 monId, u16 move)\n{",
    )
    assert "GetLevelUpLearnsetSafe(species)" in random_alternate
    assert "if (species >= NUM_SPECIES)" in random_alternate
    assert "return MOVE_NONE;" in random_alternate
    assert "gLevelUpLearnsets[" not in random_alternate

    latest_learned = section(
        apprentice,
        "static void GetLatestLearnedMoves(u16 species, u16 *moves)",
        "static u16 GetDefaultMove(u8 monId, u8 speciesArrayId, u8 moveSlot)",
    )
    assert "GetLevelUpLearnsetSafe(species)" in latest_learned
    assert "if (learnset[0] == LEVEL_UP_END)" in latest_learned
    assert "moves[j] = MOVE_NONE;" in latest_learned
    assert "gLevelUpLearnsets[" not in latest_learned

    direct_indexes = []
    level_calls = 0
    tmhm_calls = 0
    level_files = set()
    tmhm_files = set()
    for path in sorted((ROOT / "src").rglob("*.c")):
        source = path.read_text(encoding="utf-8")
        relative = path.relative_to(ROOT).as_posix()

        calls = source.count("GetLevelUpLearnsetSafe(")
        if "const u16 *GetLevelUpLearnsetSafe(u16 species)" in source:
            calls -= 1
        if calls:
            level_calls += calls
            level_files.add(relative)

        calls = source.count("GetTMHMLearnsetWordsSafe(")
        if "static const u32 *GetTMHMLearnsetWordsSafe(u16 species)" in source:
            calls -= 1
        if calls:
            tmhm_calls += calls
            tmhm_files.add(relative)

        for line_number, line in enumerate(source.splitlines(), 1):
            if "gLevelUpLearnsets[" in line:
                direct_indexes.append({
                    "path": relative,
                    "line": line_number,
                    "source": line.strip(),
                    "table": "level_up",
                })
            if "gTMHMLearnsets[" in line:
                direct_indexes.append({
                    "path": relative,
                    "line": line_number,
                    "source": line.strip(),
                    "table": "tmhm",
                })

    expected_direct_indexes = [
        {
            "path": "src/pokemon.c",
            "line": next(
                n for n, line in enumerate(pokemon.splitlines(), 1)
                if "return gLevelUpLearnsets[species];" in line
            ),
            "source": "return gLevelUpLearnsets[species];",
            "table": "level_up",
        },
        {
            "path": "src/pokemon.c",
            "line": next(
                n for n, line in enumerate(pokemon.splitlines(), 1)
                if "return gTMHMLearnsets[species].as_u32s;" in line
            ),
            "source": "return gTMHMLearnsets[species].as_u32s;",
            "table": "tmhm",
        },
    ]
    assert direct_indexes == expected_direct_indexes, direct_indexes
    assert level_calls == 7, level_calls
    assert tmhm_calls == 2, tmhm_calls
    assert level_files == {"src/pokemon.c", "src/apprentice.c"}
    assert tmhm_files == {"src/pokemon.c"}

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "level_up_accessor_call_sites": level_calls,
        "level_up_files_using_accessor": len(level_files),
        "tmhm_accessor_call_sites": tmhm_calls,
        "tmhm_files_using_accessor": len(tmhm_files),
        "unguarded_direct_indexes": 0,
        "guarded_table_index_sites": len(direct_indexes),
        "invalid_level_up_fallback": "LEVEL_UP_END sentinel",
        "invalid_tmhm_fallback": "zeroed TMHM words",
        "runtime_gen8_moves_imported": False,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("PASS: level-up and TM/HM learnset consumers use bounded accessors.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
