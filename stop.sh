#!/usr/bin/env bash
set -Eeuo pipefail

REPOSITORY_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPOSITORY_ROOT"

printf '\033[36mStopping NorseAI...\033[0m\n'
docker compose down
printf '\033[32m[OK] NorseAI stopped\033[0m\n'
