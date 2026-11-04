#!/usr/bin/env python3
"""Regression tests for Gen 8 pending-table extraction helpers."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile

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


def test_explicit_target_move_alias_resolution():
    targets = {"VICE_GRIP", "FAINT_ATTACK"}
    assert module.resolve_target_move_symbol("VISE_GRIP", targets) == "VICE_GRIP"
    assert module.resolve_target_move_symbol("VICEGRIP", targets) == "VICE_GRIP"
    assert module.resolve_target_move_symbol("FEINT_ATTACK", targets) == "FAINT_ATTACK"
    assert module.resolve_target_move_symbol("SPECTRAL_THIEF", targets) is None
    assert module.resolve_target_move_symbol("VICEGRIP", {"VICEGRIP"}) == "VICEGRIP"


def test_numeric_define_catalog_with_comments():
    source = """
#define EVO_LEVEL 4 // level-up evolution
#define EVO_ITEM 7 /* item evolution */
#define EVO_SPIN 8
"""
    values = module.numeric_define_catalog(source, "EVO_")
    assert values == {"LEVEL": 4, "ITEM": 7, "SPIN": 8}, values


def test_move_alias_catalog_and_conflict_detection():
    target_symbols = {"VICE_GRIP", "FAINT_ATTACK"}
    source_symbols = ["VISE_GRIP", "VICEGRIP", "FEINT_ATTACK", "SPECTRAL_THIEF"]
    resolved = {
        symbol: module.resolve_target_move_symbol(symbol, target_symbols)
        for symbol in source_symbols
    }
    assert resolved == {
        "VISE_GRIP": "VICE_GRIP",
        "VICEGRIP": "VICE_GRIP",
        "FEINT_ATTACK": "FAINT_ATTACK",
        "SPECTRAL_THIEF": None,
    }

    # Alias spellings intentionally converge on an existing ID.
    assert resolved["VISE_GRIP"] == resolved["VICEGRIP"]
    assert resolved["FEINT_ATTACK"] == "FAINT_ATTACK"

    # Collision detection is by canonical source record after aliases resolve.
    source_records = [
        {"source_move_symbol": "VISE_GRIP", "emerald_move_symbol": "VICE_GRIP", "emerald_move_id": 11},
        {"source_move_symbol": "VICEGRIP", "emerald_move_symbol": "VICE_GRIP", "emerald_move_id": 11},
        {"source_move_symbol": "FEINT_ATTACK", "emerald_move_symbol": "FAINT_ATTACK", "emerald_move_id": 185},
    ]
    owners = {}
    conflicts = {}
    for row in source_records:
        key = row["emerald_move_id"]
        previous = owners.get(key)
        if previous is not None and previous != row["emerald_move_symbol"]:
            conflicts.setdefault(key, [previous]).append(row["emerald_move_symbol"])
        else:
            owners[key] = row["emerald_move_symbol"]
    assert conflicts == {}


def test_resolved_aliases_do_not_create_false_id_collisions():
    records = [
        {"emerald_move_id": 11, "emerald_move_symbol": "VICE_GRIP"},
        {"emerald_move_id": 11, "emerald_move_symbol": "VICE_GRIP"},
        {"emerald_move_id": 185, "emerald_move_symbol": "FAINT_ATTACK"},
    ]
    owners = {}
    conflicts = {}
    for row in records:
        move_id = row["emerald_move_id"]
        canonical = row["emerald_move_symbol"]
        previous = owners.get(move_id)
        if previous is not None and previous != canonical:
            conflicts.setdefault(move_id, [previous]).append(canonical)
        else:
            owners[move_id] = canonical
    assert conflicts == {}

    records.append({"emerald_move_id": 11, "emerald_move_symbol": "ANOTHER_MOVE"})
    owners = {}
    conflicts = {}
    for row in records:
        move_id = row["emerald_move_id"]
        canonical = row["emerald_move_symbol"]
        previous = owners.get(move_id)
        if previous is not None and previous != canonical:
            conflicts.setdefault(move_id, [previous]).append(canonical)
        else:
            owners[move_id] = canonical
    assert conflicts == {11: ["VICE_GRIP", "ANOTHER_MOVE"]}


def test_battle_effect_dependency_grouping():
    move_rows = [
        {"source_move_symbol": "TEST_A", "battle_fields": {"effect": "EFFECT_HIT"}, "target_battle_record_present": False},
        {"source_move_symbol": "TEST_B", "battle_fields": {"effect": "EFFECT_HIT"}, "target_battle_record_present": True},
        {"source_move_symbol": "TEST_C", "battle_fields": {"effect": "EFFECT_CUSTOM"}, "target_battle_record_present": False},
    ]
    effect_symbols = ["EFFECT_HIT", "EFFECT_CUSTOM"]
    rows = []
    for effect in effect_symbols:
        affected = [
            row for row in move_rows
            if effect in module.re.findall(
                r"\bEFFECT_[A-Z0-9_]+\b",
                row["battle_fields"].get("effect") or "",
            )
        ]
        rows.append({
            "effect_symbol": effect,
            "canonical_move_count": len(affected),
            "canonical_moves": sorted(row["source_move_symbol"] for row in affected),
            "missing_move_record_count": sum(1 for row in affected if not row["target_battle_record_present"]),
        })
    assert rows == [
        {"effect_symbol": "EFFECT_HIT", "canonical_move_count": 2,
         "canonical_moves": ["TEST_A", "TEST_B"], "missing_move_record_count": 1},
        {"effect_symbol": "EFFECT_CUSTOM", "canonical_move_count": 1,
         "canonical_moves": ["TEST_C"], "missing_move_record_count": 1},
    ]


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


def test_gen8_pokedex_runtime_tables():
    # Require every National Dex slot to match the pinned Expansion source.
    target_source = (ROOT / "include/constants/pokedex.h").read_text(encoding="utf-8")
    expansion_source = (
        ROOT / "tools/vendor/pokeemerald-expansion/include/constants/pokedex.h"
    ).read_text(encoding="utf-8")
    target_rows = module.conv.symbols(target_source, "NATIONAL_DEX_", enum=True)
    expansion_rows = module.conv.symbols(expansion_source, "NATIONAL_DEX_", enum=True)

    def national_symbols(rows):
        result = {}
        for row in rows:
            dex_id = int(row["id"])
            symbol = row["symbol"]
            if 1 <= dex_id <= 898 and not symbol.startswith("OLD_UNOWN_"):
                result.setdefault(dex_id, symbol)
        return result

    target_by_id = national_symbols(target_rows)
    expansion_by_id = national_symbols(expansion_rows)
    assert set(target_by_id) == set(range(1, 899)), sorted(set(range(1, 899)) - set(target_by_id))
    assert target_by_id == expansion_by_id, {
        dex_id: (expansion_by_id.get(dex_id), target_by_id.get(dex_id))
        for dex_id in range(1, 899)
        if expansion_by_id.get(dex_id) != target_by_id.get(dex_id)
    }
    assert target_by_id[702] == "DEDENNE"
    assert target_by_id[808] == "MELTAN"
    assert target_by_id[809] == "MELMETAL"
    assert target_by_id[898] == "CALYREX"
    assert not any(
        int(row["id"]) <= 898 and row["symbol"].startswith("OLD_UNOWN_")
        for row in target_rows
    )

    rows = [
        {
            "national_dex": dex,
            "species_symbol": f"TEST_{dex}",
            "record_provenance": "expansion_source_initializer",
            "species_name_fragments": [f"TESTMON{dex}"],
            "category_fragments": ["Test Category"],
            "description_fragments": ["First line.\n", "Second line."],
            "height_dm": "5",
            "weight_hg": "42",
        }
        for dex in range(387, 899)
    ]
    orders = {
        name: {
            "national_dex_order": list(range(1, 899)),
            "entries": 898,
            "unique_entries": 898,
            "duplicates": [],
            "missing": [],
            "complete_for_gen8": True,
        }
        for name in (
            "gPokedexOrder_Alphabetical",
            "gPokedexOrder_Weight",
            "gPokedexOrder_Height",
        )
    }
    source, order_header = module.emit_gen8_pokedex_runtime(rows, orders)
    assert "gGen8PokedexData[GEN8_DEX_COUNT + 1]" in source
    assert "[NATIONAL_DEX_TURTWIG]" in source
    assert "sGen8PokedexDescription_387" in source
    assert "First line.\\n" in source
    assert '.speciesName = _("TESTMON387")' in source
    assert "NATIONAL_DEX_CALYREX" in order_header
    assert order_header.count("NATIONAL_DEX_") == 898 * 3


def test_enum_parser_preserves_full_constant_name():
    source = '''enum {
    NATIONAL_DEX_NONE,
    NATIONAL_DEX_BULBASAUR,
    NATIONAL_DEX_IVYSAUR,
    NATIONAL_DEX_CALYREX,
};
'''
    rows = module.conv.symbols(source, 'NATIONAL_DEX_', enum=True)
    assert rows == [
        {'symbol': 'NONE', 'id': 0},
        {'symbol': 'BULBASAUR', 'id': 1},
        {'symbol': 'IVYSAUR', 'id': 2},
        {'symbol': 'CALYREX', 'id': 3},
    ]

def test_generated_text_writer_is_idempotent():
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / "generated" / "pokedex_data.c"
        module.write_text_if_changed(path, "static const int value = 1;\\n")
        original_mtime = path.stat().st_mtime_ns

        module.write_text_if_changed(path, "static const int value = 1;\\n")
        assert path.stat().st_mtime_ns == original_mtime, "Identical output changed its timestamp"

        module.write_text_if_changed(path, "static const int value = 2;\\n")
        assert path.read_text(encoding="utf-8") == "static const int value = 2;\\n"


def main():
    test_enum_parser_preserves_full_constant_name()
    test_generated_text_writer_is_idempotent()
    test_nested_initializer_scan()
    test_evolution_expressions()
    test_text_fragments()
    test_conditional_shared_pokedex_text_pointer()
    test_numeric_define_catalog_with_comments()
    test_enum_symbol_catalog_keeps_symbolic_aliases()
    test_explicit_target_move_alias_resolution()
    test_move_alias_catalog_and_conflict_detection()
    test_resolved_aliases_do_not_create_false_id_collisions()
    test_battle_effect_dependency_grouping()
    test_cry_table_labels()
    test_named_array_inventory()
    test_gen8_pokedex_runtime_tables()
    test_runtime_national_dex_count_and_hoenn_filter()
    print("PASS: nested move/evolution initializers, source strings and form-table scanning.")



def test_runtime_national_dex_count_and_hoenn_filter():
    species_header = (ROOT / "include/constants/species.h").read_text(encoding="utf-8")
    pokedex_header = (ROOT / "include/constants/pokedex.h").read_text(encoding="utf-8")
    pokedex_source = (ROOT / "src/pokedex.c").read_text(encoding="utf-8")

    assert "#define NUM_SPECIES SPECIES_EGG" in species_header
    assert "#define NATIONAL_DEX_COUNT  NATIONAL_DEX_CALYREX" in pokedex_header
    assert "return hoennNum != 0 && hoennNum <= dexCount;" in pokedex_source
    assert pokedex_source.count(
        "IsDexNumberInCurrentDex(temp_dexNum, temp_isHoennDex, temp_dexCount)"
    ) == 5


if __name__ == "__main__":
    main()
