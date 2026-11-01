#!/usr/bin/env python3
"""Audit Gen 8 runtime integration blockers without changing production C."""
from __future__ import annotations
import json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "tools/vendor/pokeemerald-expansion"
OUT = ROOT / "reports/gen8-conversion"
SOURCES = {
 "species_info": VENDOR / "src/data/pokemon/species_info/gen_8_families.h",
 "learnsets": VENDOR / "src/data/pokemon/level_up_learnsets/gen_8.h",
 "moves": VENDOR / "include/constants/moves.h",
}
TARGETS = {
 "species_info": ROOT / "src/data/pokemon/species_info.h",
 "species": ROOT / "include/constants/species.h",
 "moves": ROOT / "include/constants/moves.h",
 "abilities": ROOT / "include/constants/abilities.h",
 "items": ROOT / "include/constants/items.h",
 "pokemon_constants": ROOT / "include/constants/pokemon.h",
 "pokemon_header": ROOT / "include/pokemon.h",
 "battle_moves": ROOT / "src/data/battle_moves.h",
 "contest_moves": ROOT / "src/data/contest_moves.h",
 "pokedex_entries": ROOT / "src/data/pokemon/pokedex_entries.h",
 "pokedex_text": ROOT / "src/data/pokemon/pokedex_text.h",
 "cries": ROOT / "sound/cry_tables.inc",
 "pokemon_c": ROOT / "src/pokemon.c",
}
MEMORY = {"EWRAM":(249708,262144),"IWRAM":(30416,32768),"SaveBlock1":(15752,15872),"SaveBlock2":(3884,3968),"PokemonStorage":(33744,35712)}
def read(path):
 if not path.is_file(): raise RuntimeError(f"Missing input: {path}")
 return path.read_text(encoding="utf-8")
def cap(text, pattern): return re.findall(pattern,text,re.M)
def main():
 src={k:read(v) for k,v in SOURCES.items()}
 dst={k:read(v) for k,v in TARGETS.items()}
 abilities=set(re.findall(r"\\bABILITY_([A-Z0-9_]+)\\b",src["species_info"]))
 items=set(re.findall(r"\\bITEM_([A-Z0-9_]+)\\b",src["species_info"]))
 eggs=set(re.findall(r"\\bEGG_GROUP_([A-Z0-9_]+)\\b",src["species_info"]))
 types=set(re.findall(r"\\bTYPE_([A-Z0-9_]+)\\b",src["species_info"]))
 dst_abilities=set(cap(dst["abilities"],r"^#define ABILITY_([A-Z0-9_]+)\\s+"))
 dst_items=set(cap(dst["items"],r"^\\s*ITEM_([A-Z0-9_]+)\\s*,"))
 dst_eggs=set(cap(dst["pokemon_constants"],r"^#define EGG_GROUP_([A-Z0-9_]+)\\s+"))
 dst_types=set(cap(dst["pokemon_constants"],r"^#define TYPE_([A-Z0-9_]+)\\s+"))
 src_fields=set(cap(src["species_info"],r"^\\s*\\.([A-Za-z0-9_]+)\\s*="))
 dst_fields=set(cap(dst["species_info"],r"^\\s*\\.([A-Za-z0-9_]+)\\s*="))
 info=cap(src["species_info"],r"^\\s*\\[SPECIES_([A-Z0-9_]+)\\]\\s*=\\s*\\{")
 learns=cap(src["learnsets"],r"static const struct LevelUpMove s([A-Za-z0-9]+)LevelUpLearnset\\[\\]\\s*=\\s*\\{")
 source_moves=[(n,int(i)) for n,i in re.findall(r"^\\s*MOVE_([A-Z0-9_]+)\\s*=\\s*(\\d+)\\s*,?",src["moves"],re.M) if int(i)<=847]
 battle=set(cap(dst["battle_moves"],r"^\\s*\\[MOVE_([A-Z0-9_]+)\\]\\s*="))
 contest=set(cap(dst["contest_moves"],r"^\\s*\\[MOVE_([A-Z0-9_]+)\\]\\s*="))
 miss_battle=sorted({n for n,i in source_moves if i>354 and n not in battle})
 miss_contest=sorted({n for n,i in source_moves if i>354 and n not in contest})
 evo=re.findall(r"\\.evolutions\\s*=\\s*EVOLUTION\\(([\\s\\S]*?)\\)",src["species_info"])
 evo_methods=sorted(set(re.findall(r"\\b(EVO_[A-Z0-9_]+)\\b",src["species_info"])))
 cries=set(re.findall(r"\\bCRY_([A-Z0-9_]+)\\b",src["species_info"]))
 cry_names={x.upper() for x in cap(dst["cries"],r"^\\s*cry(?:_reverse)?\\s+Cry_([A-Za-z0-9_]+)")}
 fields_extra=sorted(src_fields-dst_fields)
 counts={"species_info_blocks":len(info),"learnset_blocks":len(learns),"unique_source_moves_through_847":len({i for n,i in source_moves}),"new_moves_after_354":len({i for n,i in source_moves if i>354}),"new_moves_missing_battle_data":len(miss_battle),"new_moves_missing_contest_data":len(miss_contest),"species_evolution_initializers":len(evo),"extra_species_info_fields":len(fields_extra),"missing_abilities":len(abilities-dst_abilities),"missing_items":len(items-dst_items),"missing_types":len(types-dst_types),"missing_egg_groups":len(eggs-dst_eggs),"source_cry_ids":len(cries),"matching_cry_names":len(cries&cry_names)}
 mem={k:{"used":u,"capacity":c,"percent":round(u/c*100,2),"remaining":c-u} for k,(u,c) in MEMORY.items()}
 report={"counts":counts,"missing_identifiers":{"abilities":sorted(abilities-dst_abilities),"items":sorted(items-dst_items),"types":sorted(types-dst_types),"egg_groups":sorted(eggs-dst_eggs)},"missing_move_data":{"battle":miss_battle,"contest":miss_contest},"extra_species_info_fields":fields_extra,"evolution_methods":evo_methods,"cry_ids_without_matching_names":sorted(cries-cry_names),"memory":mem,"readiness":{"species_info_complete":False,"battle_and_contest_complete":False,"evolutions_complete":False,"pokedex_text_complete":False,"cries_complete":False,"graphics_complete":False,"save_and_ram_validated":False,"num_species_change_allowed":False}}
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/"integration_blockers.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\\n",encoding="utf-8")
 (OUT/"integration_blockers.md").write_text("# Gen 8 integration blockers\\n\\n" + "\\n".join(f"- **{k}**: {v}" for k,v in counts.items()) + "\\n\\n`NUM_SPECIES` remains unchanged until all gates are met.\\n",encoding="utf-8")
 print(json.dumps(counts,indent=2))
if __name__=="__main__": main()
