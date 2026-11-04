#ifndef GUARD_GEN8_POKEDEX_DATA_H
#define GUARD_GEN8_POKEDEX_DATA_H

#include "pokedex.h"

struct Gen8PokedexData
{
    struct PokedexEntry entry;
    u8 speciesName[16];
};

extern const struct Gen8PokedexData gGen8PokedexData[GEN8_DEX_COUNT + 1];

#endif // GUARD_GEN8_POKEDEX_DATA_H
