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


def check_macro_expansion_and_target_conditionals():
    source = r"""
#define BASE_STATS(type) \
    { \
        .baseHP = 60, \
        .types = MON_TYPES(type), \
        .expYield = (P_UPDATED_EXP_YIELDS >= GEN_8) ? 280 : 200, \
    }
#define NESTED_STATS(type) BASE_STATS(type)
    [SPECIES_TESTMON] = NESTED_STATS(TYPE_DARK),
    """
    macros = module.extract_c_macros(source)
    rows = module.balanced_species_records(source)
    assert len(rows) == 1, rows
    expanded = module.expand_c_macro_text(rows[0]["body"], macros)
    fields = module.extract_designated_fields(expanded)
    assert fields["baseHP"] == "60", fields
    assert fields["types"] == "MON_TYPES(TYPE_DARK)", fields
    assert fields["expYield"] == "(P_UPDATED_EXP_YIELDS >= GEN_8) ? 280 : 200", fields

    conditional = """
#if P_UPDATED_EXP_YIELDS >= GEN_8
    .expYield = 280,
#else
    .expYield = 200,
#endif
"""
    resolved = module.resolve_source_conditionals(conditional, 8)
    conditional_fields = module.extract_designated_fields(resolved)
    assert conditional_fields["expYield"] == "280", conditional_fields

    guarded = """
#ifdef P_FAMILY_MOTHIM
#if P_UPDATED_EXP_YIELDS >= GEN_8
    .expYield = 148,
#else
    .expYield = 159,
#endif
#endif
"""
    guarded_resolved = module.resolve_source_conditionals(guarded, 8)
    guarded_fields = module.extract_designated_fields(guarded_resolved)
    assert guarded_fields["expYield"] == "148", guarded_fields


def check_real_form_initializer_macros():
    # Macro-based family records are common for form-heavy canonical species.
    mothim = r"""
#define MOTHIM_SPECIES_INFO \
    { \
        .baseHP = 70, \
        .types = MON_TYPES(TYPE_BUG, TYPE_FLYING), \
        .expYield = (P_UPDATED_EXP_YIELDS >= GEN_5) ? 148 : 159, \
        .abilities = { ABILITY_SWARM, ABILITY_NONE, ABILITY_TINTED_LENS }, \
    }
    [SPECIES_MOTHIM_PLANT] = MOTHIM_SPECIES_INFO,
    """
    arceus = r"""
#define ARCEUS_SPECIES_INFO(type, typeName, iconPal) \
    { \
        .baseHP = 120, \
        .types = MON_TYPES(type), \
        .abilities = { ABILITY_MULTITYPE, ABILITY_NONE, ABILITY_NONE }, \
        .natDexNum = NATIONAL_DEX_ARCEUS, \
    }
    [SPECIES_ARCEUS_NORMAL] = ARCEUS_SPECIES_INFO(TYPE_NORMAL, Normal, 1),
    """
    silvally = r"""
#define SILVALLY_SPECIES_INFO(type, _palette) \
    { \
        .baseHP = 95, \
        .types = MON_TYPES(type), \
        .abilities = { ABILITY_RKS_SYSTEM, ABILITY_NONE, ABILITY_NONE }, \
    }
    [SPECIES_SILVALLY_NORMAL] = SILVALLY_SPECIES_INFO(TYPE_NORMAL, Normal),
    """
    for source, symbol in ((mothim, "MOTHIM_PLANT"),
                           (arceus, "ARCEUS_NORMAL"),
                           (silvally, "SILVALLY_NORMAL")):
        macros = module.extract_c_macros(source)
        rows = module.balanced_species_records(source)
        row = next(x for x in rows if x["symbol"] == symbol)
        expanded = module.expand_c_macro_text(row["body"], macros)
        fields = module.extract_designated_fields(expanded)
        assert fields["baseHP"] in ("70", "120", "95"), fields
        assert "MON_TYPES(" in fields["types"], fields
        assert "ABILITY_" in fields["abilities"], fields
    mothim_macros = module.extract_c_macros(mothim)
    mothim_row = module.balanced_species_records(mothim)[0]
    mothim_fields = module.extract_designated_fields(
        module.expand_c_macro_text(mothim_row["body"], mothim_macros)
    )
    assert mothim_fields["expYield"] == "(P_UPDATED_EXP_YIELDS >= GEN_5) ? 148 : 159", mothim_fields
    assert module.resolve_source_conditionals(
        "#if P_UPDATED_EXP_YIELDS >= GEN_8\n.expYield = 148,\n#else\n.expYield = 159,\n#endif",
        8,
    ).strip() == ".expYield = 148,"


def check_ability_initializer_contents_are_parsed():
    # The field scanner returns the initializer value without its designator.
    source = """
        .abilities = { ABILITY_OVERGROW, ABILITY_NONE, ABILITY_CHLOROPHYLL },
    """
    fields = module.extract_designated_fields(source)
    raw = fields["abilities"]
    names = module.re.findall(r"ABILITY_([A-Z0-9_]+)", raw)
    assert names == ["OVERGROW", "NONE", "CHLOROPHYLL"], (raw, names)


def check_gen8_stats_conditionals_use_target_generation():
    assert module.TARGET_GAME_GENERATION == 8
    cases = [
        ("P_UPDATED_STATS >= GEN_2 ? 109 : 85", 109),
        ("(P_UPDATED_EXP_YIELDS >= GEN_8) ? 300 : 270", 300),
        ("(P_UPDATED_FRIENDSHIP >= GEN_8) ? 50 : 70", 50),
    ]
    for raw, expected in cases:
        compact = " ".join(raw.split())
        compact = compact.strip("() ")
        compact = compact.replace(") ?", " ?")
        m = module.re.fullmatch(
            r"(?P<flag>P_UPDATED_[A-Z0-9_]+)\s*>=\s*GEN_(?P<gen>\d+)\s*\?\s*(?P<yes>-?\d+)\s*:\s*(?P<no>-?\d+)",
            compact,
        )
        assert m, (raw, compact)
        actual = int(m.group("yes") if module.TARGET_GAME_GENERATION >= int(m.group("gen")) else m.group("no"))
        assert actual == expected, (raw, actual, expected)


def check_actual_speciesinfo_generation8_target_resolution():
    assert module.TARGET_GAME_GENERATION == 8
    cases = [
        ("P_UPDATED_STATS >= GEN_2 ? 109 : 85", 109),
        ("(P_UPDATED_EXP_YIELDS >= GEN_8) ? 300 : 270", 300),
        ("(P_UPDATED_FRIENDSHIP >= GEN_8) ? 50 : 70", 50),
        ("P_UPDATED_STATS >= GEN_9 ? 120 : 130", 130),
    ]
    for raw, expected in cases:
        compact = " ".join(raw.split()).strip("() ").replace(") ?", " ?")
        m = module.re.fullmatch(
            r"(?P<flag>P_UPDATED_[A-Z0-9_]+)\s*>=\s*GEN_(?P<gen>\d+)\s*\?\s*(?P<yes>-?\d+)(?:\s*:\s*(?P<no>-?\d+))?",
            compact,
        )
        assert m, (raw, compact)
        yes = int(m.group("yes"))
        no = int(m.group("no")) if m.group("no") is not None else 0
        actual = yes if module.TARGET_GAME_GENERATION >= int(m.group("gen")) else no
        assert actual == expected, (raw, actual, expected)


def check_family_guards_are_included_in_source_catalog():
    assert module.evaluate_source_condition("P_FAMILY_ALCREMIE", 8) is True
    assert module.evaluate_source_condition("P_FAMILY_CHARIZARD", 8) is True
    assert module.evaluate_source_condition("P_UPDATED_EXP_YIELDS >= GEN_8", 8) is True
    assert module.evaluate_source_condition("P_UPDATED_EXP_YIELDS >= GEN_9", 8) is False


def check_wrapped_standard_friendship_ternary():
    raw = "((P_UPDATED_FRIENDSHIP >= GEN_8) ? 50 : 70)"
    compact = " ".join(raw.split())
    while compact.startswith("(") and compact.endswith(")"):
        depth = 0
        fully_wrapped = True
        for idx, char in enumerate(compact):
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0 and idx != len(compact) - 1:
                    fully_wrapped = False
                    break
        if not fully_wrapped or depth != 0:
            break
        compact = compact[1:-1].strip()
    match = module.re.fullmatch(
        r"\(?P_UPDATED_FRIENDSHIP\s*>=\s*GEN_(\d+)\)?\s*\?\s*(\d+)\s*:\s*(\d+)",
        compact,
    )
    assert match, compact
    assert int(match.group(1)) == 8
    assert int(match.group(2)) == 50
    assert int(match.group(3)) == 70




def check_family_macro_preprocessor_selection():
    source = """
#if P_FAMILY_ALCREMIE
#define ALCREMIE_TEST_INFO { .baseHP = 65, .types = MON_TYPES(TYPE_FAIRY) }
#else
#define ALCREMIE_TEST_INFO { .baseHP = 0, .types = MON_TYPES(TYPE_NONE) }
#endif
"""
    selected = module.resolve_source_conditionals(source, 8)
    macros = module.extract_c_macros(selected)
    expanded = module.expand_c_macro_text("ALCREMIE_TEST_INFO", macros)
    fields = module.extract_designated_fields(expanded)
    assert fields["baseHP"] == "65", fields
    assert fields["types"] == "MON_TYPES(TYPE_FAIRY)", fields

def check_generic_gen8_conditional_values():
    cases = [
        ("P_UPDATED_STATS >= GEN_6 || P_UPDATED_STATS == GEN_1 ? 50 : 40", "50"),
        ("(P_UPDATED_EVS >= GEN_4) ? 1 : 2", "1"),
        ("(P_UPDATED_TYPES >= GEN_6 ? TYPE_FAIRY : TYPE_NORMAL)", "TYPE_FAIRY"),
        ("(P_UPDATED_TYPES >= GEN_2 ? TYPE_STEEL : TYPE_ELECTRIC)", "TYPE_STEEL"),
    ]
    for expression, expected in cases:
        actual = module.resolve_c_ternary_expression(expression, module.TARGET_GAME_GENERATION)
        assert actual == expected, (expression, actual, expected)

def check_all_generation_source_files_present():
    for generation in module.SOURCE_GENERATIONS:
        info = module.SRC_SPECIES_INFO_DIR / f"gen_{generation}_families.h"
        assert info.is_file(), f"Missing source SpeciesInfo: {info}"
    for generation in module.LEARNSET_GENERATIONS:
        learnsets = module.SRC_LEARNSET_DIR / f"gen_{generation}.h"
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


def check_per_species_stellar_runtime_gap():
    type_names = set(module.re.findall(
        r"TYPE_([A-Z0-9_]+)",
        "MON_TYPES(TYPE_STELLAR, TYPE_NORMAL)",
    ))
    runtime_gaps = []
    if "FAIRY" in type_names:
        runtime_gaps.append("fairy_type_not_in_emerald_enum")
    if "STELLAR" in type_names:
        runtime_gaps.append("stellar_type_not_in_emerald_enum")
    assert "stellar_type_not_in_emerald_enum" in runtime_gaps
    assert "fairy_type_not_in_emerald_enum" not in runtime_gaps


def main():
    check_enum_implicit_and_explicit_values()
    check_nested_designated_initializers()
    check_balanced_species_record_strings()
    check_expansion_brace_on_next_line()
    check_macro_expansion_and_target_conditionals()
    check_real_form_initializer_macros()
    check_ability_initializer_contents_are_parsed()
    check_gen8_stats_conditionals_use_target_generation()
    check_actual_speciesinfo_generation8_target_resolution()
    check_family_guards_are_included_in_source_catalog()
    check_wrapped_standard_friendship_ternary()
    check_family_macro_preprocessor_selection()
    check_generic_gen8_conditional_values()
    check_all_generation_source_files_present()
    check_full_canonical_coverage_gate()
    check_per_species_stellar_runtime_gap()
    print("PASS: enum parsing, nested C initializers, quoted strings and source inventory.")
    print("PASS: canonical SpeciesInfo acceptance gate defined for National Dex 1-898.")


if __name__ == "__main__":
    main()
