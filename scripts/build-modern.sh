#!/usr/bin/env bash
set -euo pipefail

cd "$(git rev-parse --show-toplevel)"

for tool in make arm-none-eabi-gcc arm-none-eabi-cpp arm-none-eabi-as arm-none-eabi-objcopy; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        printf 'Missing build tool: %s\n' "$tool" >&2
        printf 'In Codespaces, rebuild the container after pulling the latest changes.\n' >&2
        printf 'Otherwise install the packages listed in INSTALL.md.\n' >&2
        exit 1
    fi
done

jobs="$(getconf _NPROCESSORS_ONLN 2>/dev/null || printf '2')"
if ! [[ "$jobs" =~ ^[1-9][0-9]*$ ]]; then
    jobs=2
fi

make -j"$jobs" modern

if [[ ! -s pokeemerald_modern.gba ]]; then
    printf 'Build finished but pokeemerald_modern.gba was not found.\n' >&2
    exit 1
fi

printf '\nBuild successful: %s/pokeemerald_modern.gba\n' "$PWD"
printf 'The ROM has not yet been tested in an emulator.\n'
