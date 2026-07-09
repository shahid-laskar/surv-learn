#!/usr/bin/env bash
# edge-sim/sim_manage.sh — manage simulated edge NVR sites

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_COMPOSE_DIR="${HUB_COMPOSE_DIR:-/opt/surv-learn/surv}"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
ENV_DIR="$SCRIPT_DIR/site-envs"
SITES=(01 02 03)
SITE_CODES=(SITE01 SITE02 SITE03)

GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'
info() { echo -e "${GREEN}[edge-sim]${NC} $*"; }

project_name() { echo "edge_sim_${1,,}"; }

env_file_for() {
  local site_code="$1"
  local num="${site_code//SITE/}"
  echo "$ENV_DIR/site-${num}.env"
}

compose_up() {
  local site_code="$1"
  local env_file
  env_file=$(env_file_for "$site_code")
  [[ -f "$env_file" ]] || { echo "Missing $env_file — copy from site-01.env.example"; return 1; }
  info "Starting $site_code..."
  docker compose -p "$(project_name "$site_code")" \
    --env-file "$env_file" -f "$COMPOSE_FILE" up -d --build
}

compose_down() {
  local site_code="$1"
  docker compose -p "$(project_name "$site_code")" \
    --env-file "$(env_file_for "$site_code")" \
    -f "$COMPOSE_FILE" down
}

CMD="${1:-help}"; shift || true
case "$CMD" in
  up)
    if [[ $# -ge 1 ]]; then compose_up "$1"; else
      for c in "${SITE_CODES[@]}"; do compose_up "$c"; done
    fi ;;
  down)
    if [[ $# -ge 1 ]]; then compose_down "$1"; else
      for c in "${SITE_CODES[@]}"; do compose_down "$c" || true; done
    fi ;;
  status)
    for c in "${SITE_CODES[@]}"; do
      echo -e "\n${CYAN}── $c ──${NC}"
      docker compose -p "$(project_name "$c")" -f "$COMPOSE_FILE" ps 2>/dev/null || echo "(not running)"
    done ;;
  logs)
    SITE="${1:-SITE01}"; shift || true
    docker compose -p "$(project_name "$SITE")" \
      --env-file "$(env_file_for "$SITE")" -f "$COMPOSE_FILE" logs -f --tail=100 ${1:-}
    ;;
  verify)
    docker compose -f "$HUB_COMPOSE_DIR/docker-compose.yml" exec postgres \
      psql -U surv sarvanetra -c \
      "SELECT site_code, last_heartbeat, overlay_ip, is_provisioned FROM nvr_node ORDER BY site_code;"
    ;;
  *)
    echo "Usage: $0 {up|down|status|logs|verify} [SITE_CODE]"
    ;;
esac
