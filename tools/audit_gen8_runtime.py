#!/usr/bin/env python3
"""Quantify Gen 8 RAM/save and data compatibility gates without modifying runtime C."""
from __future__ import annotations
import json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"reports/gen8-conversion"
def read(p): 
    if not p.is_file(): raise RuntimeError(f"Missing audit input: {p}")
    return p.read_text(encoding="utf-8")
def block(text, name):
    at=text.find(name)
    if at<0: return ""
    start=text.find("{",at); depth=1; i=start+1
    while i<len(text) and depth:
        if text[i]=="{": depth+=1
        elif text[i]=="}": depth-=1
        i+=1
    return text[at:i]
def main():
    global_h=read(ROOT/"include/global.h")
    save_h=read(ROOT/"include/save.h")
    save_c=read(ROOT/"src/save.c")
    pokemon_h=read(ROOT/"include/pokemon.h")
    pokemon_constants=read(ROOT/"include/constants/pokemon.h")
    species_h=read(ROOT/"include/constants/species.h")
    source_info=read(ROOT/"tools/vendor/pokeemerald-expansion/src/data/pokemon/species_info/gen_8_families.h")
    target_info=read(ROOT/"src/data/pokemon/species_info.h")
    source_species=read(ROOT/"tools/vendor/pokeemerald-expansion/include/constants/species.h")
    source_moves=read(ROOT/"tools/vendor/pokeemerald-expansion/include/constants/moves.h")
    source_learn=read(ROOT/"tools/vendor/pokeemerald-expansion/src/data/pokemon/level_up_learnsets/gen_8.h")
    # Reconstruct the fixed save layout; the struct comments and flash sector table are authoritative.
    sb1=block(global_h,"struct SaveBlock1")
    sb2=block(global_h,"struct SaveBlock2")
    pdb=block(global_h,"struct Pokedex")
    storage_text=read(ROOT/"include/pokemon_storage_system.h")
    storage=block(storage_text,"struct PokemonStorage")
    def parse_size(label,txt,pattern,default):
        m=re.search(pattern,txt)
        return int(m.group(1),0) if m else default
    save1_size=parse_size("SaveBlock1",sb1,r"sizeof:s*(0x[0-9A-Fa-f]+)",0x3D88)
    save2_size=parse_size("SaveBlock2",sb2,r"sizeof:s*(0x[0-9A-Fa-f]+)",0x6A0)
    storage_size=parse_size("PokemonStorage",storage,r"sizeof:s*(0x[0-9A-Fa-f]+)",0x83C3)
    sector=int(re.search(r"#define SECTOR_DATA_SIZEs+(d+)",save_h).group(1))
    sb1_capacity=4*sector
    sb2_capacity=1*sector
    storage_capacity=9*sector
    num_dex=898
    dex_flag_bytes=(num_dex+7)//8
    two_flag_arrays=2*dex_flag_bytes
    old_flag_bytes=(412+7)//8
    current_pokedex_flags=2*old_flag_bytes
    unused_match=re.search(r"unused_3598[(0x[0-9A-Fa-f]+)]",sb1)
    reserved_in_sb1=int(unused_match.group(1),0) if unused_match else 0
    source_record_count=len(re.findall(r"^s*[SPECIES_[A-Z0-9_]+]s*=",source_info,re.M))
    target_fields=set(re.findall(r"^s*.([A-Za-z0-9_]+)s*=",target_info,re.M))
    source_fields=set(re.findall(r"^s*.([A-Za-z0-9_]+)s*=",source_info,re.M))
    extra_fields=sorted(source_fields-target_fields)
    src_species_ids=[int(x) for x in re.findall(r"^s*SPECIES_[A-Z0-9_]+s*=s*(d+)",source_species,re.M)]
    src_move_ids=[int(x) for x in re.findall(r"^s*MOVE_[A-Z0-9_]+s*=s*(d+)",source_moves,re.M)]
    learn_blocks=len(re.findall(r"static const struct LevelUpMove s[A-Za-z0-9]+LevelUpLearnset[]s*=",source_learn))
    src_beyond_gen3=len({i for i in src_move_ids if 354<i<=847})
    source_abilities=set(re.findall(r"ABILITY_([A-Z0-9_]+)",source_info))
    target_abilities=set(re.findall(r"^#define ABILITY_([A-Z0-9_]+)s+",read(ROOT/"include/constants/abilities.h"),re.M))
    source_items=set(re.findall(r"ITEM_([A-Z0-9_]+)",source_info))
    target_items=set(re.findall(r"^s*ITEM_([A-Z0-9_]+)s*,",read(ROOT/"include/constants/items.h"),re.M))
    source_types=set(re.findall(r"TYPE_([A-Z0-9_]+)",source_info))
    target_types=set(re.findall(r"^#define TYPE_([A-Z0-9_]+)s+",pokemon_constants,re.M))
    cry_ids=set(re.findall(r"CRY_([A-Z0-9_]+)",source_info))
    cry_table=read(ROOT/"sound/cry_tables.inc")
    cry_names={x.upper() for x in re.findall(r"^s*cry(?:_reverse)?s+Cry_([A-Za-z0-9_]+)",cry_table,re.M)}
    count_missing={
      "abilities":sorted(source_abilities-target_abilities),
      "items":sorted(source_items-target_items),
      "types":sorted(source_types-target_types)
    }
    report={
      "save_layout":{
        "sector_data_bytes":sector,"saveblock1_bytes":save1_size,"saveblock1_capacity_bytes":sb1_capacity,
        "saveblock1_headroom_bytes":sb1_capacity-save1_size,"saveblock1_unused_internal_bytes":reserved_in_sb1,
        "saveblock2_bytes":save2_size,"saveblock2_capacity_bytes":sb2_capacity,"saveblock2_headroom_bytes":sb2_capacity-save2_size,
        "pokemon_storage_bytes":storage_size,"pokemon_storage_capacity_bytes":storage_capacity,
        "national_dex_count":num_dex,"required_pokedex_flag_bytes_per_set":dex_flag_bytes,
        "required_seen_owned_flag_bytes":two_flag_arrays,"current_species_flag_bytes":2*old_flag_bytes,
        "additional_flag_bytes_needed":two_flag_arrays-2*old_flag_bytes,
        "estimated_one_sector_extension_capacity_bytes":sector-16,
        "two_copy_journaled_extension_bytes":2*(two_flag_arrays+16),
        "note":"SaveBlock1/2 have hard sector capacities; do not grow them in-place. Special sectors 30/31 are currently assigned to Trainer Hill/Recorded Battle."
      },
      "data":{
        "gen8_species_info_records":source_record_count,"species_info_fields_not_in_vanilla":extra_fields,
        "new_moves_after_gen3_through_gen8":src_beyond_gen3,"learnset_blocks":learn_blocks,
        "missing_abilities":count_missing["abilities"],"missing_items":count_missing["items"],
        "missing_types":count_missing["types"],"source_cry_ids":len(cry_ids),
        "matching_cry_names":len(cry_ids&cry_names),"unmatched_cry_ids":sorted(cry_ids-cry_names)
      },
      "readiness":{
        "save_extension_sector_plan_validated":False,"save_extension_read_write_tests":False,
        "species_info_complete":False,"abilities_complete":not count_missing["abilities"],
        "held_items_complete":not count_missing["items"],"types_complete":not count_missing["types"],
        "battle_and_contest_moves_complete":False,"evolutions_complete":False,
        "pokedex_text_complete":False,"cries_complete":False,"graphics_complete":False,
        "runtime_ready":False,"num_species_change_allowed":False
      }
    }
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"storage_architecture_audit.json").write_text(json.dumps(report,indent=2,ensure_ascii=False)+"
",encoding="utf-8")
    print(json.dumps({"save_layout":report["save_layout"],"data":{k:v for k,v in report["data"].items() if not isinstance(v,list)},"readiness":report["readiness"]},indent=2))
if __name__=="__main__":main()
