# CFRU source snapshot for Lilycove Adoption data migration

Upstream: https://github.com/Skeli789/Complete-Fire-Red-Upgrade
Upstream branch: master
Source snapshot commit audited: b637a27898b14e25dd24d0f69a3e302f0069deb8

Only the following source files are vendored for data extraction:
- include/constants/species.h
- include/constants/pokedex.h
- include/constants/moves.h
- src/Tables/level_up_learnsets.c

This snapshot is used only as a source of species identity and learnset data.
Do not import its battle engine hooks, assembly patches, binary assets, or save
layout. Review the upstream license and attribution requirements before any
redistribution of extracted assets or data.
