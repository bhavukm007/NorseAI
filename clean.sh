#!/usr/bin/env bash
set -Eeuo pipefail

REPOSITORY_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPOSITORY_ROOT"

printf 'WARNING: This removes NorseAI containers and database/Redis volumes, then prunes unused Docker data.\n'
read -r -p 'Type CLEAN to continue: ' confirmation
if [[ "$confirmation" != "CLEAN" ]]; then
  printf 'Clean cancelled.\n'
  exit 0
fi

docker compose down -v
docker system prune -f
printf '\033[32m[OK] NorseAI Docker data cleaned\033[0m\n'
