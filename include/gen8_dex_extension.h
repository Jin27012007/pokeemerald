#ifndef GUARD_GEN8_DEX_EXTENSION_H
#define GUARD_GEN8_DEX_EXTENSION_H

#include "global.h"

#define GEN8_DEX_EXT_BYTES GEN8_DEX_EXT_FLAG_BYTES
#define GEN8_DEX_EXT_MAGIC GEN8_DEX_EXT_MAGIC_VALUE
#define GEN8_DEX_EXT_VERSION GEN8_DEX_EXT_FORMAT_VERSION

enum Gen8DexExtensionCopy
{
    GEN8_DEX_COPY_SEEN = 0,
    GEN8_DEX_COPY_OWNED,
    GEN8_DEX_COPY_SEEN_BACKUP,
    GEN8_DEX_COPY_OWNED_BACKUP,
};

enum Gen8DexExtensionResult
{
    GEN8_DEX_EXTENSION_OK = 0,
    GEN8_DEX_EXTENSION_BAD_ARGUMENT,
    GEN8_DEX_EXTENSION_BAD_HEADER,
    GEN8_DEX_EXTENSION_BAD_VERSION,
    GEN8_DEX_EXTENSION_BAD_CHECKSUM,
    GEN8_DEX_EXTENSION_BAD_GENERATION,
};

u32 Gen8DexExtensionChecksum(const struct Gen8DexExtension *extension);
void Gen8DexExtensionInit(struct Gen8DexExtension *extension);
bool32 Gen8DexExtensionValidate(const struct Gen8DexExtension *extension);
bool32 Gen8DexExtensionReadFlag(const struct Gen8DexExtension *extension, u16 nationalDex, bool32 owned);
enum Gen8DexExtensionResult Gen8DexExtensionWriteFlag(
    struct Gen8DexExtension *extension, u16 nationalDex, bool32 owned, bool32 value);

#endif // GUARD_GEN8_DEX_EXTENSION_H
