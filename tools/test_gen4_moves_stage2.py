from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED = [
    ("AQUA_TAIL", 394, "EFFECT_HIT", 90, "WATER", "PHYSICAL", 90, 10, 0, "MOVE_TARGET_SELECTED", true, "Aqua Tail"),
    ("FORCE_PALM", 395, "EFFECT_PARALYZE_HIT", 60, "FIGHTING", "PHYSICAL", 100, 10, 30, "MOVE_TARGET_SELECTED", true, "Force Palm"),
    ("AIR_SLASH", 396, "EFFECT_FLINCH_HIT", 75, "FLYING", "SPECIAL", 95, 20, 30, "MOVE_TARGET_SELECTED", false, "Air Slash"),
    ("DRAGON_RUSH", 397, "EFFECT_FLINCH_HIT", 100, "DRAGON", "PHYSICAL", 75, 10, 20, "MOVE_TARGET_SELECTED", true, "Dragon Rush"),
    ("FLASH_CANNON", 398, "EFFECT_SPECIAL_DEFENSE_DOWN_HIT", 80, "STEEL", "SPECIAL", 100, 10, 10, "MOVE_TARGET_SELECTED", false, "Flash Cannon"),
    ("DISCHARGE", 399, "EFFECT_PARALYZE_HIT", 80, "ELECTRIC", "SPECIAL", 100, 15, 30, "MOVE_TARGET_FOES_AND_ALLY", false, "Discharge"),
    ("LAVA_PLUME", 400, "EFFECT_BURN_HIT", 80, "FIRE", "SPECIAL", 100, 15, 30, "MOVE_TARGET_FOES_AND_ALLY", false, "Lava Plume"),
    ("ATTACK_ORDER", 401, "EFFECT_HIGH_CRITICAL", 90, "BUG", "PHYSICAL", 100, 15, 0, "MOVE_TARGET_SELECTED", false, "Attack Order"),
    ("DOUBLE_HIT", 402, "EFFECT_DOUBLE_HIT", 35, "NORMAL", "PHYSICAL", 90, 10, 0, "MOVE_TARGET_SELECTED", true, "Double Hit"),
    ("INFERNO", 403, "EFFECT_BURN_HIT", 100, "FIRE", "SPECIAL", 50, 5, 100, "MOVE_TARGET_SELECTED", false, "Inferno"),
    ("STRUGGLE_BUG", 404, "EFFECT_SPECIAL_ATTACK_DOWN_HIT", 30, "BUG", "SPECIAL", 100, 20, 100, "MOVE_TARGET_BOTH", false, "Struggle Bug"),
    ("LEAF_TORNADO", 405, "EFFECT_ACCURACY_DOWN_HIT", 65, "GRASS", "SPECIAL", 90, 10, 50, "MOVE_TARGET_SELECTED", false, "Leaf Tornado"),
    ("SEARING_SHOT", 406, "EFFECT_BURN_HIT", 100, "FIRE", "SPECIAL", 100, 5, 30, "MOVE_TARGET_FOES_AND_ALLY", false, "Searing Shot"),
    ("PETAL_BLIZZARD", 407, "EFFECT_HIT", 90, "GRASS", "PHYSICAL", 100, 15, 0, "MOVE_TARGET_FOES_AND_ALLY", false, "Petal Blizzard"),
    ("NUZZLE", 408, "EFFECT_PARALYZE_HIT", 20, "ELECTRIC", "PHYSICAL", 100, 20, 100, "MOVE_TARGET_SELECTED", true, "Nuzzle"),
    ("POWER_UP_PUNCH", 409, "EFFECT_ATTACK_UP_HIT", 40, "FIGHTING", "PHYSICAL", 100, 20, 100, "MOVE_TARGET_SELECTED", true, "Power-up Punch"),
    ("LEAFAGE", 410, "EFFECT_HIT", 40, "GRASS", "PHYSICAL", 100, 40, 0, "MOVE_TARGET_SELECTED", false, "Leafage"),
    ("LUNGE", 411, "EFFECT_ATTACK_DOWN_HIT", 80, "BUG", "PHYSICAL", 100, 15, 100, "MOVE_TARGET_SELECTED", true, "Lunge"),
]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def test_gen4_move_stage2_records_are_specific():
    constants = read("include/constants/moves.h")
    records = read("src/data/battle_moves.h")
    names = read("src/data/text/move_names.h")
    descriptions = read("src/data/text/move_descriptions.h")
    animations = read("data/battle_anim_scripts.s")
    effects = read("include/constants/battle_move_effects.h")
    scripts = read("data/battle_scripts_1.s")

    assert "#define MOVES_COUNT 412" in constants
    assert len(EXPECTED) == 18
    for symbol, move_id, effect, power, move_type, category, accuracy, pp, chance, target, contact, anim_name in EXPECTED:
        assert f"#define MOVE_{symbol} {move_id}" in constants
        entry = records.split(f"[MOVE_{symbol}] =", 1)[1].split("\n    },", 1)[0]
        assert f".effect = {effect}" in entry, symbol
        assert f".power = {power}" in entry, symbol
        assert f".type = TYPE_{move_type}" in entry, symbol
        assert f".category = DAMAGE_CATEGORY_{category}" in entry, symbol
        assert f".accuracy = {accuracy}" in entry, symbol
        assert f".pp = {pp}" in entry, symbol
        assert f".secondaryEffectChance = {chance}" in entry, symbol
        assert f".target = {target}" in entry, symbol
        assert ".priority = 0" in entry, symbol
        assert ("FLAG_MAKES_CONTACT" in entry) == contact, symbol
        assert f"#define {effect} " in effects
        assert f"@ {effect}" in scripts
        assert f"[MOVE_{symbol}] = " in names
        assert f"[MOVE_{symbol} - 1] =" in descriptions
        assert f"@ {anim_name}" in animations


if __name__ == "__main__":
    test_gen4_move_stage2_records_are_specific()
    print("PASS: 18 additional Gen 4 learnset moves have matching Emerald battle effects.")
