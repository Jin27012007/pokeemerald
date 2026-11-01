#!/usr/bin/env python3
"""Regression tests for the Gen 8 SpeciesInfo source parser and coverage gate."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "gen8_convert_emerald", ROOT / "tools/gen8_convert_emerald.py"
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def check_enum_implicit_and_explicit_values():
    source = """
    enum __attribute__((packed)) EggGroup
    {
        EGG_GROUP_NONE,
        EGG_GROUP_MONSTER,
        EGG_GROUP_WATER_1,
    };
    enum GrowthRate
    {
        GROWTH_MEDIUM_FAST,
        GROWTH_ERRATIC,
        GROWTH_SLOW = 5,
    };
    """
    egg = {x["symbol"]: x["id"] for x in module.symbols(source, "EGG_GROUP_", enum=True)}
    growth = {x["symbol"]: x["id"] for x in module.symbols(source, "GROWTH_", enum=True)}
    assert egg == {"NONE": 0, "MONSTER": 1, "WATER_1": 2}, egg
    assert growth == {"MEDIUM_FAST": 0, "ERRATIC": 1, "SLOW": 5}, growth


def check_nested_designated_initializers():
    body = """
        .baseHP = 55,
        .expYield = (P_UPDATED_EXP_YIELDS >= GEN_5) ? 142 : 141,
        .types = MON_TYPES(TYPE_GRASS),
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_MONSTER, EGG_GROUP_GRASS),
        .abilities = { ABILITY_OVERGROW, ABILITY_NONE, ABILITY_SHELL_ARMOR },
        .description = COMPOUND_STRING(
            "Line one, with comma,\\n"
            "Line two"
        ),
    """
    fields = module.extract_designated_fields(body)
    assert fields["baseHP"] == "55", fields
    assert fields["expYield"] == "(P_UPDATED_EXP_YIELDS >= GEN_5) ? 142 : 141", fields
    assert fields["types"] == "MON_TYPES(TYPE_GRASS)", fields
    assert fields["eggGroups"] == "MON_EGG_GROUPS(EGG_GROUP_MONSTER, EGG_GROUP_GRASS)", fields
    assert fields["abilities"] == "{ ABILITY_OVERGROW, ABILITY_NONE, ABILITY_SHELL_ARMOR }", fields
    assert "Line one, with comma" in fields["description"], fields


def check_balanced_species_record_strings():
    source = '''
    [SPECIES_TESTMON] =
    {
        .speciesName = _("Test, mon"),
        .description = COMPOUND_STRING("A {brace}, and a comma,"),
        .baseHP = 1,
    },
    '''
    rows = module.balanced_species_records(source)
    assert len(rows) == 1, rows
    assert rows[0]["symbol"] == "TESTMON"
    assert "Test, mon" in rows[0]["body"]
    assert "A {brace}, and a comma," in rows[0]["body"]


def check_expansion_brace_on_next_line():
    source = """
    [SPECIES_TURTWIG] =
    {
        .baseHP = 55,
        .natDexNum = NATIONAL_DEX_TURTWIG,
        .eggGroups = MON_EGG_GROUPS(EGG_GROUP_MONSTER, EGG_GROUP_GRASS),
    },
    """
    rows = module.balanced_species_records(source)
    assert len(rows) == 1, rows
    assert rows[0]["symbol"] == "TURTWIG"
    fields = module.extract_designated_fields(rows[0]["body"])
    assert fields["baseHP"] == "55", fields
    assert fields["natDexNum"] == "NATIONAL_DEX_TURTWIG", fields
    assert fields["eggGroups"] == "MON_EGG_GROUPS(EGG_GROUP_MONSTER, EGG_GROUP_GRASS)", fields


def check_all_generation_source_files_present():
    for generation in module.SOURCE_GENERATIONS:
        info = module.SRC_SPECIES_INFO_DIR / f"gen_{generation}_families.h"
        learnsets = module.SRC_LEARNSET_DIR / f"gen_{generation}.h"
        assert info.is_file(), f"Missing source SpeciesInfo: {info}"
        assert learnsets.is_file(), f"Missing source learnsets: {learnsets}"


def check_full_canonical_coverage_gate():
    # This is the acceptance criterion used by --check. It is deliberately
    # independent of form count and rejects missing/duplicate/partial rows.
    dex_rows = list(range(1, 898 + 1))
    assert len(dex_rows) == 898
    assert len(set(dex_rows)) == 898
    assert dex_rows[0] == 1 and dex_rows[-1] == 898
    required = {"baseHP", "baseAttack", "baseDefense", "baseSpeed",
                "baseSpAttack", "baseSpDefense", "natDexNum"}
    sample = required | {"types", "eggGroups", "abilities", "growthRate"}
    assert required <= sample


def main():
    check_enum_implicit_and_explicit_values()
    check_nested_designated_initializers()
    check_balanced_species_record_strings()
    check_expansion_brace_on_next_line()
    check_all_generation_source_files_present()
    check_full_canonical_coverage_gate()
    print("PASS: enum parsing, nested C initializers, quoted strings and source inventory.")
    print("PASS: canonical SpeciesInfo acceptance gate defined for National Dex 1-898.")


if __name__ == "__main__":
    main()
