#include "global.h"
#include "gen8_dex_extension.h"

#include <stddef.h>

#define GEN8_DEX_EXT_LOCAL_COPY_COUNT 4


STATIC_ASSERT(sizeof(struct Gen8DexExtension) == 256, Gen8DexExtension_must_fit_reserved_window);
STATIC_ASSERT(GEN8_DEX_EXT_BYTES * GEN8_DEX_EXT_LOCAL_COPY_COUNT == 244, Gen8DexExtension_flag_payload_must_be_244_bytes);
STATIC_ASSERT(GEN8_DEX_EXT_BYTES == 61, Gen8DexExtension_requires_486_dex_bits_per_copy);

static const u8 *GetGen8DexExtensionFlagArrayConst(const struct Gen8DexExtension *extension, u8 copy)
{
    switch (copy)
    {
    case GEN8_DEX_COPY_SEEN:
        return extension->seen;
    case GEN8_DEX_COPY_OWNED:
        return extension->owned;
    case GEN8_DEX_COPY_SEEN_BACKUP:
        return extension->seenBackup;
    case GEN8_DEX_COPY_OWNED_BACKUP:
        return extension->ownedBackup;
    default:
        return NULL;
    }
}

// FNV-1a over the versioned header and all four payload copies, excluding the
// checksum field itself. This is an integrity check, not cryptographic auth.
u32 Gen8DexExtensionChecksum(const struct Gen8DexExtension *extension)
{
    const u8 *bytes;
    u32 hash = 2166136261u;
    u32 i;

    if (extension == NULL)
        return 0;

    bytes = (const u8 *)extension;
    for (i = 0; i < sizeof(*extension); i++)
    {
        if (i >= offsetof(struct Gen8DexExtension, checksum)
         && i < offsetof(struct Gen8DexExtension, checksum) + sizeof(extension->checksum))
            continue;
        hash ^= bytes[i];
        hash *= 16777619u;
    }
    return hash;
}

void Gen8DexExtensionInit(struct Gen8DexExtension *extension)
{
    if (extension == NULL)
        return;

    CpuFill32(0, extension, sizeof(*extension));
    extension->magic = GEN8_DEX_EXT_MAGIC;
    extension->version = GEN8_DEX_EXT_VERSION;
    extension->generation = 1;
    extension->checksum = Gen8DexExtensionChecksum(extension);
}

bool32 Gen8DexExtensionValidate(const struct Gen8DexExtension *extension)
{
    if (extension == NULL
     || extension->magic != GEN8_DEX_EXT_MAGIC
     || extension->version != GEN8_DEX_EXT_VERSION
     || extension->generation == 0)
        return FALSE;

    if (extension->checksum != Gen8DexExtensionChecksum(extension))
        return FALSE;

    return TRUE;
}

static bool32 IsGen8DexExtensionBlank(const struct Gen8DexExtension *extension)
{
    const u8 *bytes = (const u8 *)extension;
    u32 i;

    for (i = 0; i < sizeof(*extension); i++)
    {
        if (bytes[i] != 0)
            return FALSE;
    }
    return TRUE;
}

// Older Emerald saves used this fixed SaveBlock1 region as unused padding.
// Initialize only a blank legacy region. A nonblank invalid envelope is
// treated as corruption or an unknown format and is never overwritten.
bool32 Gen8DexExtensionPrepareForWrite(struct Gen8DexExtension *extension)
{
    if (extension == NULL)
        return FALSE;

    if (IsGen8DexExtensionBlank(extension))
        Gen8DexExtensionInit(extension);

    return Gen8DexExtensionValidate(extension);
}

static bool32 ReadFlagFromCopy(const struct Gen8DexExtension *extension, u16 nationalDex, u8 copy)
{
    const u8 *array = GetGen8DexExtensionFlagArrayConst(extension, copy);
    u16 index;

    if (array == NULL || nationalDex < 413 || nationalDex > GEN8_DEX_COUNT)
        return FALSE;

    index = nationalDex - 413;
    return (array[index / 8] >> (index % 8)) & 1;
}

bool32 Gen8DexExtensionReadFlag(const struct Gen8DexExtension *extension, u16 nationalDex, bool32 owned)
{
    bool32 primary;
    bool32 backup;

    if (!Gen8DexExtensionValidate(extension) || nationalDex < 1 || nationalDex > GEN8_DEX_COUNT)
        return FALSE;

    // Original 1..412 National Dex flags remain in legacy Pokedex arrays.
    if (nationalDex <= 412)
        return FALSE;

    if (owned)
    {
        primary = ReadFlagFromCopy(extension, nationalDex, GEN8_DEX_COPY_OWNED);
        backup = ReadFlagFromCopy(extension, nationalDex, GEN8_DEX_COPY_OWNED_BACKUP);
    }
    else
    {
        primary = ReadFlagFromCopy(extension, nationalDex, GEN8_DEX_COPY_SEEN);
        backup = ReadFlagFromCopy(extension, nationalDex, GEN8_DEX_COPY_SEEN_BACKUP);
    }

    // A disagreement is not silently resolved. The caller gets false
    // unless both copies agree that the bit is set. Save recovery remains
    // outside this staging-only helper.
    return primary && backup;
}

enum Gen8DexExtensionResult Gen8DexExtensionWriteFlag(
    struct Gen8DexExtension *extension, u16 nationalDex, bool32 owned, bool32 value)
{
    u16 index;
    u8 mask;
    u8 *primary;
    u8 *backup;

    if (extension == NULL)
        return GEN8_DEX_EXTENSION_BAD_ARGUMENT;
    if (extension->magic != GEN8_DEX_EXT_MAGIC
     || extension->generation == 0)
        return GEN8_DEX_EXTENSION_BAD_HEADER;
    if (extension->version != GEN8_DEX_EXT_VERSION)
        return GEN8_DEX_EXTENSION_BAD_VERSION;
    if (!Gen8DexExtensionValidate(extension))
        return GEN8_DEX_EXTENSION_BAD_CHECKSUM;
    if (nationalDex < 413 || nationalDex > GEN8_DEX_COUNT)
        return GEN8_DEX_EXTENSION_BAD_ARGUMENT;
    if (extension->generation == 0xFFFFu)
        return GEN8_DEX_EXTENSION_BAD_GENERATION;

    index = nationalDex - 413;
    mask = 1u << (index % 8);
    if (owned)
    {
        primary = extension->owned;
        backup = extension->ownedBackup;
    }
    else
    {
        primary = extension->seen;
        backup = extension->seenBackup;
    }

    if (value)
    {
        primary[index / 8] |= mask;
        backup[index / 8] |= mask;
    }
    else
    {
        primary[index / 8] &= ~mask;
        backup[index / 8] &= ~mask;
    }

    extension->generation++;
    extension->checksum = Gen8DexExtensionChecksum(extension);
    return GEN8_DEX_EXTENSION_OK;
}
