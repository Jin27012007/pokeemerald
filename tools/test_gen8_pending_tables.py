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
    test_named_array_inventory()
    print("PASS: nested move/evolution initializers, source strings and form-table scanning.")


if __name__ == "__main__":
    main()
