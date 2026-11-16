#!/usr/bin/env python3
"""Regression tests for the Gen 8 Fairy type integration."""
from pathlib import Path
import re
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
POKEMON_CONSTANTS = (ROOT / "include/constants/pokemon.h").read_text(encoding="utf-8")
BATTLE_MAIN = (ROOT / "src/battle_main.c").read_text(encoding="utf-8")
BATTLE_MAIN_HEADER = (ROOT / "include/battle_main.h").read_text(encoding="utf-8")
SUMMARY = (ROOT / "src/pokemon_summary_screen.c").read_text(encoding="utf-8")
BATTLE_SCRIPTS = (ROOT / "src/battle_script_commands.c").read_text(encoding="utf-8")
GRAPHICS_RULES = (ROOT / "graphics_file_rules.mk").read_text(encoding="utf-8")


def test_fairy_moves_are_registered_and_battle_ready():
    constants = (ROOT / "include/constants/moves.h").read_text(encoding="utf-8")
    moves = (ROOT / "src/data/battle_moves.h").read_text(encoding="utf-8")
    names = (ROOT / "src/data/text/move_names.h").read_text(encoding="utf-8")
    descriptions = (ROOT / "src/data/text/move_descriptions.h").read_text(encoding="utf-8")
    animations = (ROOT / "data/battle_anim_scripts.s").read_text(encoding="utf-8")
    expected = {
        "DISARMING_VOICE": (355, "EFFECT_ALWAYS_HIT", 40, 0, 15),
        "DRAINING_KISS": (356, "EFFECT_ABSORB", 50, 100, 10),
        "FAIRY_WIND": (357, "EFFECT_HIT", 40, 100, 30),
        "PLAY_ROUGH": (358, "EFFECT_ATTACK_DOWN_HIT", 90, 90, 10),
        "MOONBLAST": (359, "EFFECT_SPECIAL_ATTACK_DOWN_HIT", 95, 100, 15),
        "DAZZLING_GLEAM": (360, "EFFECT_HIT", 80, 100, 10),
        "BABY_DOLL_EYES": (361, "EFFECT_ATTACK_DOWN", 0, 100, 30),
    }
    for name, (move_id, effect, power, accuracy, pp) in expected.items():
        assert f"#define MOVE_{name} {move_id}" in constants
        start = moves.index(f"[MOVE_{name}] =")
        entry = moves[start:moves.index("\n    },", start) + 7]
        assert f".effect = {effect}" in entry
        assert f".power = {power}" in entry
        assert ".type = TYPE_FAIRY" in entry
        assert f".accuracy = {accuracy}" in entry
        assert f".pp = {pp}" in entry
        assert f"[MOVE_{name}] = " in names
        assert f"[MOVE_{name} - 1] =" in descriptions
        assert f"@ " + {"DISARMING_VOICE": "Disarming Voice", "DRAINING_KISS": "Draining Kiss", "FAIRY_WIND": "Fairy Wind", "PLAY_ROUGH": "Play Rough", "MOONBLAST": "Moonblast", "DAZZLING_GLEAM": "Dazzling Gleam", "BABY_DOLL_EYES": "Baby-Doll Eyes"}[name] in animations
    assert ".priority = 1" in moves[moves.index("[MOVE_BABY_DOLL_EYES] ="):]
    assert ".target = MOVE_TARGET_BOTH" in moves[moves.index("[MOVE_DAZZLING_GLEAM] ="):]


def test_existing_fairy_species_can_learn_fairy_moves():
    learnsets = (ROOT / "src/data/pokemon/level_up_learnsets.h").read_text(encoding="utf-8")
    expected = {
        "sClefairyLevelUpLearnset": "MOVE_MOONBLAST",
        "sJigglypuffLevelUpLearnset": "MOVE_DISARMING_VOICE",
        "sMarillLevelUpLearnset": "MOVE_PLAY_ROUGH",
        "sRaltsLevelUpLearnset": "MOVE_MOONBLAST",
        "sTogepiLevelUpLearnset": "MOVE_DRAINING_KISS",
        "sSnubbullLevelUpLearnset": "MOVE_PLAY_ROUGH",
    }
    for symbol, move in expected.items():
        start = learnsets.index(f"static const u16 {symbol}[]")
        end = learnsets.index("\n};", start)
        assert move in learnsets[start:end], f"{symbol} is missing {move}"


def test_fairy_abilities_are_applied_in_battle_calculation():
    battle_header = (ROOT / "include/battle.h").read_text(encoding="utf-8")
    pokemon = (ROOT / "src/pokemon.c").read_text(encoding="utf-8")
    assert "ABILITY_PIXILATE" in battle_header
    assert "move != MOVE_STRUGGLE" in battle_header
    assert "attacker->ability == ABILITY_PIXILATE" in pokemon
    assert "isPhysical = GetMoveCategory(move) == DAMAGE_CATEGORY_PHYSICAL" in pokemon
    assert "if (type == TYPE_NORMAL && attacker->ability == ABILITY_PIXILATE && move != MOVE_STRUGGLE)" in pokemon
    assert "ABILITY_FAIRY_AURA" in pokemon
    assert "ABILITY_AURA_BREAK" in pokemon
    assert "gBattleMovePower = (gBattleMovePower * 6) / 5" in pokemon
    assert "gBattleMovePower = (gBattleMovePower * 4) / 3" in pokemon
    assert "gBattleMovePower = (gBattleMovePower * 3) / 4" in pokemon


def test_fairy_has_a_unique_emerald_type_id():
    assert "#define TYPE_FAIRY            18" in POKEMON_CONSTANTS
    assert "#define NUMBER_OF_MON_TYPES   19" in POKEMON_CONSTANTS
    assert '[TYPE_FAIRY] = _("FAIRY")' in BATTLE_MAIN
    assert "extern const u8 gTypeEffectiveness[366];" in BATTLE_MAIN_HEADER


def test_fairy_chart_contains_all_gen6_matchups():
    start = BATTLE_MAIN.index("const u8 gTypeEffectiveness[366]")
    end = BATTLE_MAIN.index("\n};", start)
    chart = BATTLE_MAIN[start:end]
    triples = re.findall(
        r"(TYPE_[A-Z0-9_]+)\s*,\s*(TYPE_[A-Z0-9_]+)\s*,\s*(TYPE_MUL_[A-Z_]+)",
        chart,
    )
    assert len(triples) == 122
    expected = {
        ("TYPE_FAIRY", "TYPE_FIGHTING", "TYPE_MUL_SUPER_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_DRAGON", "TYPE_MUL_SUPER_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_DARK", "TYPE_MUL_SUPER_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_FIRE", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_POISON", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_FAIRY", "TYPE_STEEL", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_FIGHTING", "TYPE_FAIRY", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_POISON", "TYPE_FAIRY", "TYPE_MUL_SUPER_EFFECTIVE"),
        ("TYPE_BUG", "TYPE_FAIRY", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_DRAGON", "TYPE_FAIRY", "TYPE_MUL_NO_EFFECT"),
        ("TYPE_DARK", "TYPE_FAIRY", "TYPE_MUL_NOT_EFFECTIVE"),
        ("TYPE_STEEL", "TYPE_FAIRY", "TYPE_MUL_SUPER_EFFECTIVE"),
    }
    assert expected.issubset(set(triples))
    assert ("TYPE_ENDTABLE", "TYPE_ENDTABLE", "TYPE_MUL_NO_EFFECT") in triples
    # Steel no longer resists Ghost and Dark from Generation VI onward.
    assert ("TYPE_GHOST", "TYPE_STEEL", "TYPE_MUL_NOT_EFFECTIVE") not in triples
    assert ("TYPE_DARK", "TYPE_STEEL", "TYPE_MUL_NOT_EFFECTIVE") not in triples


def test_fairy_png_is_a_valid_4bpp_32x16_asset():
    data = (ROOT / "graphics/types/fairy.png").read_bytes()
    assert data.startswith(b"\x89PNG\r\n\x1a\n")
    offset = 8
    chunks = {}
    while offset < len(data):
        length = struct.unpack(">I", data[offset : offset + 4])[0]
        kind = data[offset + 4 : offset + 8]
        payload = data[offset + 8 : offset + 8 + length]
        stored_crc = struct.unpack(">I", data[offset + 8 + length : offset + 12 + length])[0]
        assert zlib.crc32(kind + payload) & 0xFFFFFFFF == stored_crc
        chunks[kind] = payload
        offset += length + 12
    assert offset == len(data)
    assert chunks[b"IHDR"] == struct.pack(">IIBBBBB", 32, 16, 4, 3, 0, 0, 0)
    assert len(chunks[b"PLTE"]) == 16 * 3
    assert chunks[b"tRNS"] == b"\x00"
    assert chunks[b"IEND"] == b""


def test_fairy_summary_icon_and_palette_are_registered():
    assert "ANIMCMD_FRAME(TYPE_FAIRY * 8, 0, FALSE, FALSE)" in SUMMARY
    assert "sSpriteAnim_TypeFairy,\n    sSpriteAnim_CategoryCool" in SUMMARY
    assert "[TYPE_FAIRY] = 14" in SUMMARY
    assert "fairy" in GRAPHICS_RULES.split("types ?=", 1)[1].split("\n", 1)[0]
    assert (ROOT / "graphics/types/fairy.png").is_file()
    type_assignments = [
        line.strip()
        for line in GRAPHICS_RULES.splitlines()
        if re.match(r"^types\s*(?::=|\?=|=)", line.strip())
    ]
    assert type_assignments == [
        "types ?= normal fight flying poison ground rock bug ghost steel mystery fire water grass electric psychic ice dragon dark fairy",
        "types := $(filter-out fairy,$(types)) fairy",
    ]
    assert "$(types:%=$(TYPESGFXDIR)/%.4bpp)" in GRAPHICS_RULES


def test_type_chart_random_probe_cannot_read_past_the_table():
    assert ">= sizeof(gTypeEffectiveness) / 3" in BATTLE_SCRIPTS
    assert "> sizeof(gTypeEffectiveness) / 3" not in BATTLE_SCRIPTS


def test_hidden_power_keeps_the_original_gen3_type_pool():
    assert "NUMBER_OF_MON_TYPES - 4" in BATTLE_SCRIPTS
    assert "NUMBER_OF_MON_TYPES - 3) * typeBits" not in BATTLE_SCRIPTS
    assert "Fairy type are excluded" in BATTLE_SCRIPTS
    # All 16 Gen 3 Hidden Power types remain reachable; Fairy stays excluded.
    legacy_pool = set((15 * bits) // 63 + 1 for bits in range(64))
    legacy_pool = {value + 1 if value >= 9 else value for value in legacy_pool}
    assert len(legacy_pool) == 16
    assert min(legacy_pool) == 1 and max(legacy_pool) == 17
    assert 18 not in legacy_pool


def test_fairy_battle_text_and_pokedex_filter():
    battle_messages = (ROOT / "src/battle_message.c").read_text(encoding="utf-8")
    assert '[TYPE_FAIRY]    = _("a FAIRY move")' in battle_messages
    pokedex = (ROOT / "src/pokedex.c").read_text(encoding="utf-8")
    assert "gTypeNames[TYPE_FAIRY]" in pokedex
    start = pokedex.index("static const u8 sDexSearchTypeIds[NUMBER_OF_MON_TYPES]")
    end = pokedex.index("\n};", start)
    assert "TYPE_FAIRY," in pokedex[start:end]


def test_species_that_gained_fairy_keep_modern_types():
    source = (ROOT / "src/data/pokemon/species_info.h").read_text(encoding="utf-8")
    expected = {
        "CLEFAIRY": ("TYPE_FAIRY", "TYPE_FAIRY"),
        "CLEFABLE": ("TYPE_FAIRY", "TYPE_FAIRY"),
        "JIGGLYPUFF": ("TYPE_NORMAL", "TYPE_FAIRY"),
        "WIGGLYTUFF": ("TYPE_NORMAL", "TYPE_FAIRY"),
        "MR_MIME": ("TYPE_PSYCHIC", "TYPE_FAIRY"),
        "CLEFFA": ("TYPE_FAIRY", "TYPE_FAIRY"),
        "IGGLYBUFF": ("TYPE_NORMAL", "TYPE_FAIRY"),
        "TOGEPI": ("TYPE_FAIRY", "TYPE_FAIRY"),
        "TOGETIC": ("TYPE_FAIRY", "TYPE_FLYING"),
        "SNUBBULL": ("TYPE_FAIRY", "TYPE_FAIRY"),
        "GRANBULL": ("TYPE_FAIRY", "TYPE_FAIRY"),
        "MARILL": ("TYPE_WATER", "TYPE_FAIRY"),
        "AZUMARILL": ("TYPE_WATER", "TYPE_FAIRY"),
        "AZURILL": ("TYPE_NORMAL", "TYPE_FAIRY"),
        "MAWILE": ("TYPE_STEEL", "TYPE_FAIRY"),
        "RALTS": ("TYPE_PSYCHIC", "TYPE_FAIRY"),
        "KIRLIA": ("TYPE_PSYCHIC", "TYPE_FAIRY"),
        "GARDEVOIR": ("TYPE_PSYCHIC", "TYPE_FAIRY"),
    }
    for species, pair in expected.items():
        start = source.index(f"[SPECIES_{species}] =")
        end = source.index("\n    },", start)
        block = source[start:end]
        expected_field = f".types = {{ {pair[0]}, {pair[1]} }}"
        assert expected_field in block, f"{species}: expected {expected_field}"


def test_gen8_converter_no_longer_treats_fairy_as_a_gap():
    converter = (ROOT / "tools/gen8_convert_emerald.py").read_text(encoding="utf-8")
    assert "fairy_type_not_in_emerald_enum" not in converter
    source_only_line = next(
        line for line in converter.splitlines()
        if '"source_only_fields_require_runtime_work"' in line
    )
    assert '"fairy_type"' not in source_only_line


def main():
    test_fairy_moves_are_registered_and_battle_ready()
    test_existing_fairy_species_can_learn_fairy_moves()
    test_fairy_abilities_are_applied_in_battle_calculation()
    test_fairy_has_a_unique_emerald_type_id()
    test_fairy_chart_contains_all_gen6_matchups()
    test_fairy_png_is_a_valid_4bpp_32x16_asset()
    test_fairy_summary_icon_and_palette_are_registered()
    test_type_chart_random_probe_cannot_read_past_the_table()
    test_hidden_power_keeps_the_original_gen3_type_pool()
    test_fairy_battle_text_and_pokedex_filter()
    test_species_that_gained_fairy_keep_modern_types()
    test_gen8_converter_no_longer_treats_fairy_as_a_gap()
    print("PASS: Fairy chart, 4bpp icon integrity, summary UI, Pokédex, species and legacy Hidden Power.")


if __name__ == "__main__":
    main()
