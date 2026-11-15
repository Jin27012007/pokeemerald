#!/usr/bin/env python3
"""Static contract tests for expanded Emerald SpeciesInfo and ability slots."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HEADER = (ROOT / "include/pokemon.h").read_text(encoding="utf-8")
POKEMON = (ROOT / "src/pokemon.c").read_text(encoding="utf-8")
ABILITIES = (ROOT / "include/constants/abilities.h").read_text(encoding="utf-8")
ABILITY_TEXT = (ROOT / "src/data/text/abilities.h").read_text(encoding="utf-8")


def struct_body(name: str) -> str:
    match = re.search(r"struct\s+" + re.escape(name) + r"\s*\{(.*?)\n\};", HEADER, re.S)
    assert match, f"missing struct {name}"
    return match.group(1)


def test_box_and_battle_pokemon_can_store_three_ability_slots():
    substruct = struct_body("PokemonSubstruct3")
    battle = struct_body("BattlePokemon")
    assert re.search(r"u32\s+abilityNum\s*:\s*2\s*;", substruct)
    assert re.search(r"u32\s+unusedRibbons\s*:\s*2\s*;", substruct)
    assert re.search(r"u32\s+unusedAbilityPadding\s*:\s*1\s*;", substruct)
    assert re.search(r"u8\s+abilityNum\s*;", battle)
    assert re.search(r"u32\s+unusedAbilityPadding\s*:\s*1\s*;", battle)


def test_species_info_has_wide_exp_yield_and_three_abilities():
    info = struct_body("SpeciesInfo")
    assert re.search(r"u16\s+expYield\s*;", info)
    assert re.search(r"u8\s+abilities\s*\[\s*3\s*\]\s*;", info)
    assert "u8 safariZoneFleeRate" in info


def test_ability_access_is_bounded_and_falls_back_safely():
    start = POKEMON.index("u8 GetAbilityBySpecies(")
    end = POKEMON.index("\n}\n", start) + 3
    getter = POKEMON[start:end]
    assert "abilityNum >= ARRAY_COUNT(speciesInfo->abilities)" in getter
    assert "speciesInfo->abilities[abilityNum] == ABILITY_NONE" in getter
    assert "abilityNum = 0" in getter


def test_boxed_and_party_mon_hidden_ability_selection():
    assert "bool8 SetBoxMonAbilityNum(struct BoxPokemon *boxMon, u8 abilityNum)" in POKEMON
    assert "bool8 SetMonAbilityNum(struct Pokemon *mon, u8 abilityNum)" in POKEMON
    assert "return SetBoxMonAbilityNum(&mon->box, abilityNum);" in POKEMON
    assert "SetBoxMonData(boxMon, MON_DATA_ABILITY_NUM, &abilityNum);" in POKEMON


def test_gen8_ability_registry_has_unique_u8_ids_and_text():
    rows = re.findall(r"#define ABILITY_([A-Z0-9_]+) ([0-9]+)", ABILITIES)
    values = [int(value) for _, value in rows]
    assert len(values) == len(set(values))
    assert max(values) <= 255
    assert len([value for value in values if value >= 78]) == 165
    assert "#define ABILITIES_COUNT 243" in ABILITIES
    for symbol, value in rows:
        if int(value) < 78:
            continue
        assert f"[ABILITY_{symbol}] = " in ABILITY_TEXT
        assert f"[ABILITY_{symbol}] = sGen8" in ABILITY_TEXT


def main():
    test_box_and_battle_pokemon_can_store_three_ability_slots()
    test_species_info_has_wide_exp_yield_and_three_abilities()
    test_ability_access_is_bounded_and_falls_back_safely()
    test_boxed_and_party_mon_hidden_ability_selection()
    test_gen8_ability_registry_has_unique_u8_ids_and_text()
    print("PASS: three ability slots, u16 experience yield, hidden ability selection and Gen 8 ability registry.")


if __name__ == "__main__":
    main()
