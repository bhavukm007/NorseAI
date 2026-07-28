#!/usr/bin/env bash
set -Eeuo pipefail

REPOSITORY_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPOSITORY_ROOT"

step() {
  printf '\n\033[36m%s\033[0m\n' "$1"
}

success() {
  printf '\033[32m[OK] %s\033[0m\n' "$1"
}

config_value() {
  local name="$1"
  local default="$2"
  local value
  value="$(printenv "$name" 2>/dev/null || true)"
  if [[ -n "$value" ]]; then
    printf '%s' "$value"
    return
  fi
  if [[ -f .env ]]; then
    value="$(sed -n -E "s/^[[:space:]]*${name}[[:space:]]*=[[:space:]]*(.*)$/\1/p" .env | tail -n 1)"
    value="${value%$'\r'}"
    value="${value%\"}"
    value="${value#\"}"
    value="${value%\'}"
    value="${value#\'}"
  fi
  printf '%s' "${value:-$default}"
}

port_is_open() {
  local port="$1"
  if command -v nc >/dev/null 2>&1; then
    nc -z 127.0.0.1 "$port" >/dev/null 2>&1
  elif command -v lsof >/dev/null 2>&1; then
    lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1
  else
    (echo >/dev/tcp/127.0.0.1/"$port") >/dev/null 2>&1
  fi
}

compose_owns_port() {
  local service="$1"
  local container_port="$2"
  local host_port="$3"
  local published
  published="$(docker compose port "$service" "$container_port" 2>/dev/null || true)"
  [[ "$published" =~ :${host_port}$ ]]
}

wait_service() {
  local service="$1"
  local label="$2"
  local timeout="${3:-240}"
  local deadline=$((SECONDS + timeout))
  local container_id state

  while ((SECONDS < deadline)); do
    container_id="$(docker compose ps -q "$service" 2>/dev/null || true)"
    if [[ -n "$container_id" ]]; then
      state="$(docker inspect --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container_id" 2>/dev/null || true)"
      if [[ "$state" == "healthy" || "$state" == "running" ]]; then
        success "$label"
        return
      fi
      if [[ "$state" == "unhealthy" || "$state" == "exited" || "$state" == "dead" ]]; then
        docker compose logs --tail 50 "$service"
        printf 'ERROR: %s failed to become healthy (state: %s).\n' "$label" "$state" >&2
        exit 1
      fi
    fi
    sleep 2
  done
  docker compose logs --tail 50 "$service"
  printf 'ERROR: Timed out waiting for %s.\n' "$label" >&2
  exit 1
}

printf '\033[36m=====================================\n'
printf 'Starting NorseAI...\n'
printf '=====================================\033[0m\n'

step "Checking Docker..."
if ! command -v docker >/dev/null 2>&1; then
  printf 'ERROR: Docker is not installed or is not available on PATH.\n' >&2
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  printf 'ERROR: Docker is not running. Start Docker Desktop or the Docker daemon and try again.\n' >&2
  exit 1
fi
success "Docker running"

if ! docker compose version >/dev/null 2>&1; then
  printf 'ERROR: Docker Compose v2 is not available. Install or update Docker Desktop.\n' >&2
  exit 1
fi
success "Docker Compose available"

if [[ ! -f .env ]]; then
  cp .env.example .env
  success "Created .env from .env.example"
fi

FRONTEND_PORT="$(config_value FRONTEND_PORT 3000)"
BACKEND_PORT="$(config_value BACKEND_PORT 8000)"
FRONTEND_ORIGIN="$(config_value FRONTEND_ORIGIN "http://localhost:${FRONTEND_PORT}")"
PUBLIC_API_BASE_URL="$(config_value PUBLIC_API_BASE_URL "http://localhost:${BACKEND_PORT}/api/v1")"
export FRONTEND_ORIGIN PUBLIC_API_BASE_URL

step "Checking ports..."
if port_is_open "$FRONTEND_PORT" && ! compose_owns_port frontend 80 "$FRONTEND_PORT"; then
  printf 'ERROR: Frontend port %s is already occupied. Set FRONTEND_PORT in .env to a free port.\n' "$FRONTEND_PORT" >&2
  exit 1
fi
if port_is_open "$BACKEND_PORT" && ! compose_owns_port backend 8000 "$BACKEND_PORT"; then
  printf 'ERROR: Backend port %s is already occupied. Set BACKEND_PORT in .env to a free port.\n' "$BACKEND_PORT" >&2
  exit 1
fi
success "Required ports available"

step "Building and starting containers..."
docker compose up --build --detach

step "Waiting for services..."
wait_service postgres "PostgreSQL"
wait_service redis "Redis"
wait_service opa "OPA"
wait_service backend "Backend"
wait_service frontend "Frontend"

FRONTEND_URL="http://localhost:${FRONTEND_PORT}"
BACKEND_URL="http://localhost:${BACKEND_PORT}"

printf '\n\033[36m=====================================\033[0m\n'
printf '\033[32mNorseAI is ready!\033[0m\n\n'
printf 'Frontend:\n\033[36m%s\033[0m\n\n' "$FRONTEND_URL"
printf 'Backend:\n\033[36m%s\033[0m\n\n' "$BACKEND_URL"
printf 'Swagger:\n\033[36m%s/docs\033[0m\n' "$BACKEND_URL"
printf '\033[36m=====================================\033[0m\n'
