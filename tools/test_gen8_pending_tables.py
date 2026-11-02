#!/usr/bin/env python3
"""Regression tests for Gen 8 pending-table extraction helpers."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "gen8_build_pending_tables", ROOT / "tools/gen8_build_pending_tables.py"
)
assert SPEC and SPEC.loader
module = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = module
SPEC.loader.exec_module(module)


def test_nested_initializer_scan():
    source = '''
    [MOVE_TEST] = {
        .name = COMPOUND_STRING("Comma, in text"),
        .effect = EFFECT_HIT,
        .value = WRAP(1, NESTED(2, 3)),
        .nested = { 4, 5, 6 },
    },
    [MOVE_TEST_TWO] = { .value = 9 },
    '''
    records = module.indexed_records(source, "MOVE_")
    assert set(records) == {"MOVE_TEST", "MOVE_TEST_TWO"}, records
    fields = module.conv.extract_designated_fields(records["MOVE_TEST"])
    assert fields["name"] == 'COMPOUND_STRING("Comma, in text")', fields
    assert fields["value"] == "WRAP(1, NESTED(2, 3))", fields
    assert fields["nested"] == "{ 4, 5, 6 }", fields


def test_evolution_expressions():
    single = module.parse_evolution_expression(
        "EVOLUTION({EVO_LEVEL, 16, SPECIES_IVYSAUR})"
    )
    assert single == [{
        "slot": 0,
        "method_symbol": "EVO_LEVEL",
        "parameter_expression": "16",
        "target_species_symbol": "SPECIES_IVYSAUR",
        "condition_expression": None,
        "additional_expressions": [],
    }], single

    branches = module.parse_evolution_expression(
        "EVOLUTION({EVO_TRADE, 0, SPECIES_ALAKAZAM}, "
        "{EVO_ITEM, ITEM_LINKING_CORD, SPECIES_ALAKAZAM, "
        "CONDITIONS({IF_NOT_REGION, REGION_PALDEA})})"
    )
    assert branches and len(branches) == 2, branches
    assert branches[0]["method_symbol"] == "EVO_TRADE"
    assert branches[1]["parameter_expression"] == "ITEM_LINKING_CORD"
    assert "CONDITIONS" in branches[1]["condition_expression"]


def test_text_fragments():
    fragments = module.string_fragments(
        'COMPOUND_STRING("Line one\\n" "Line two, with comma")'
    )
    assert fragments == ["Line one\n", "Line two, with comma"], fragments



def test_conditional_shared_pokedex_text_pointer():
    shared = {
        "gSilvallyNormalPokedexText": ["Normal form description."],
        "gSilvallyMemoryPokedexText": ["Memory form description."],
    }
    expression = (
        "(TYPE_NORMAL == TYPE_NORMAL ? "
        "gSilvallyNormalPokedexText : gSilvallyMemoryPokedexText)"
    )
    assert module.resolve_shared_text_pointer(expression, shared) == "gSilvallyNormalPokedexText"
    ambiguous = (
        "(TYPE_FIRE == TYPE_WATER ? "
        "gSilvallyNormalPokedexText : gSilvallyMemoryPokedexText)"
    )
    assert module.resolve_shared_text_pointer(ambiguous, shared) is None



def test_enum_symbol_catalog_keeps_symbolic_aliases():
    source = """
enum Type {
    TYPE_NONE = 0,
    TYPE_NORMAL = 1,
    TYPE_FAIRY = 19,
    TYPE_STELLAR = TYPE_FAIRY + 1,
    NUMBER_OF_MON_TYPES
};
"""
    values = module.enum_symbol_catalog(source, "TYPE_")
    assert values["NORMAL"] == 1
    assert values["FAIRY"] == 19
    assert "STELLAR" in values
    assert values["STELLAR"] is None


def test_numeric_define_catalog_with_comments():
    source = """
#define EVO_LEVEL 4 // level-up evolution
#define EVO_ITEM 7 /* item evolution */
#define EVO_SPIN 8
"""
    values = module.numeric_define_catalog(source, "EVO_")
    assert values == {"LEVEL": 4, "ITEM": 7, "SPIN": 8}, values


def test_cry_table_labels():
    source = """gCryTable::
    cry Cry_Bulbasaur
    cry Cry_MrMime
gCryTable_Reverse::
    cry_reverse Cry_Bulbasaur
"""
    labels = module.parse_cry_table_labels(source)
    assert labels == {"bulbasaur", "mrmime"}, labels


def test_named_array_inventory():
    source = '''
    static const u16 sExampleFormSpeciesIdTable[] = {
        SPECIES_EXAMPLE,
#if P_MEGA_EVOLUTIONS
        SPECIES_EXAMPLE_MEGA,
#endif
        FORM_SPECIES_END,
    };
    '''
    tables = module.named_arrays(
        source,
        r"^\s*static\s+const\s+u16\s+(s[A-Za-z0-9_]+FormSpeciesIdTable)\s*\[\]\s*=\s*\{",
    )
    assert "sExampleFormSpeciesIdTable" in tables
    assert "SPECIES_EXAMPLE_MEGA" in tables["sExampleFormSpeciesIdTable"]


def main():
    test_nested_initializer_scan()
    test_evolution_expressions()
    test_text_fragments()
    test_conditional_shared_pokedex_text_pointer()
    test_numeric_define_catalog_with_comments()
    test_enum_symbol_catalog_keeps_symbolic_aliases()
    test_cry_table_labels()
    test_named_array_inventory()
    print("PASS: nested move/evolution initializers, source strings and form-table scanning.")


if __name__ == "__main__":
    main()
