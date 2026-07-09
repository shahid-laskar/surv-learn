#!/usr/bin/env bash
# sim/sim_manage.sh
# Management wrapper for the Sarvanetra edge NVR simulation.
#
# Usage:
#   ./sim_manage.sh up [SITE_CODE]         — bring up all sites, or one site
#   ./sim_manage.sh down [SITE_CODE]       — tear down all sites, or one site
#   ./sim_manage.sh restart [SITE_CODE]    — down then up
#   ./sim_manage.sh status                 — docker ps for all sites
#   ./sim_manage.sh logs SITE_CODE [SVC]   — tail logs (svc optional)
#   ./sim_manage.sh chaos pause SITE_CODE  — pause tailscale container (WAN-drop)
#   ./sim_manage.sh chaos unpause SITE_CODE— restore tailscale container
#   ./sim_manage.sh chaos pause-all        — pause tailscale on all sites simultaneously
#   ./sim_manage.sh chaos unpause-all      — restore all at once (reconnect storm)
#   ./sim_manage.sh headscale nodes        — list headscale nodes
#   ./sim_manage.sh inject [args...]       — run inject_motion.py with given args

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HUB_COMPOSE_DIR="/opt/surv-learn/surv"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.sim.yml"
ENV_DIR="$SCRIPT_DIR/site-envs"

SITES=(01 02 03)
SITE_CODES=(SITE01 SITE02 SITE03)

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
info()    { echo -e "${GREEN}[sim]${NC}   $*"; }
section() { echo -e "\n${CYAN}══ $* ══${NC}"; }

project_name() {
  local site_code="$1"
  echo "sim_${site_code,,}"  # lowercase
}

env_file_for() {
  local site_code="$1"
  # Accept SITE01, SITE02, SITE03 or 01 02 03
  local num="${site_code//SITE/}"
  echo "$ENV_DIR/site-${num}.env"
}

compose_up() {
  local site_code="$1"
  local env_file
  env_file=$(env_file_for "$site_code")
  if [[ ! -f "$env_file" ]]; then
    echo -e "${RED}[err]${NC}  Env file not found: $env_file"
    echo "       Run: bash $SCRIPT_DIR/setup_sim.sh"
    return 1
  fi
  info "Starting $site_code..."
  docker compose -p "$(project_name "$site_code")" \
    --env-file "$env_file" \
    -f "$COMPOSE_FILE" \
    up -d --build
}

compose_down() {
  local site_code="$1"
  local env_file
  env_file=$(env_file_for "$site_code")
  info "Stopping $site_code..."
  docker compose -p "$(project_name "$site_code")" \
    --env-file "$env_file" \
    -f "$COMPOSE_FILE" \
    down
}

# ── Command dispatch ──────────────────────────────────────────────────────────
CMD="${1:-help}"
shift || true

case "$CMD" in

  up)
    if [[ $# -ge 1 ]]; then
      compose_up "$1"
    else
      section "Bringing up all simulated sites"
      for code in "${SITE_CODES[@]}"; do
        compose_up "$code"
      done
      info "All sites up. Check status: ./sim_manage.sh status"
    fi
    ;;

  down)
    if [[ $# -ge 1 ]]; then
      compose_down "$1"
    else
      section "Tearing down all simulated sites"
      for code in "${SITE_CODES[@]}"; do
        compose_down "$code" || true
      done
    fi
    ;;

  restart)
    TARGET="${1:-all}"
    "$SCRIPT_DIR/sim_manage.sh" down "${TARGET:-}" 2>/dev/null || true
    sleep 2
    "$SCRIPT_DIR/sim_manage.sh" up "${TARGET:-}"
    ;;

  status)
    section "Simulation Status"
    for code in "${SITE_CODES[@]}"; do
      echo -e "\n${YELLOW}── ${code} ──${NC}"
      docker compose -p "$(project_name "$code")" \
        -f "$COMPOSE_FILE" \
        ps --format "table {{.Name}}\t{{.Status}}" 2>/dev/null || \
        echo "  (not running)"
    done
    echo ""
    section "Headscale nodes"
    docker compose -f "$HUB_COMPOSE_DIR/docker-compose.yml" \
      exec headscale headscale nodes list 2>/dev/null || true
    ;;

  logs)
    SITE="${1:-SITE01}"; shift || true
    SVC="${1:-}"
    ENV_FILE=$(env_file_for "$SITE")
    docker compose -p "$(project_name "$SITE")" \
      --env-file "$ENV_FILE" \
      -f "$COMPOSE_FILE" \
      logs -f --tail=100 ${SVC:-}
    ;;

  chaos)
    CHAOS_CMD="${1:-help}"; shift || true
    case "$CHAOS_CMD" in
      pause)
        SITE="$1"
        CONTAINER="sim_${SITE,,}_tailscale"
        info "Pausing tailscale on $SITE (simulating WAN outage)..."
        docker pause "$CONTAINER"
        info "Paused $CONTAINER. Local recording should continue."
        info "Hub will show stale heartbeat after ~90s."
        info "Restore with: ./sim_manage.sh chaos unpause $SITE"
        ;;
      unpause)
        SITE="$1"
        CONTAINER="sim_${SITE,,}_tailscale"
        info "Unpausing tailscale on $SITE..."
        docker unpause "$CONTAINER"
        info "Restored. Expect heartbeat to resume within 30s."
        ;;
      pause-all)
        section "Pausing ALL site tailscale containers (reconnect storm prep)"
        for code in "${SITE_CODES[@]}"; do
          docker pause "sim_${code,,}_tailscale" 2>/dev/null && \
            info "  Paused sim_${code,,}_tailscale" || \
            echo "  (not running: $code)"
        done
        info "All paused. Restore with: ./sim_manage.sh chaos unpause-all"
        ;;
      unpause-all)
        section "Unpausing ALL sites simultaneously (reconnect storm)"
        for code in "${SITE_CODES[@]}"; do
          docker unpause "sim_${code,,}_tailscale" 2>/dev/null && \
            info "  Unpaused sim_${code,,}_tailscale" || true
        done
        info "All unpaused. Watch headscale logs for reconnection burst."
        ;;
      *)
        echo "chaos commands: pause <SITE> | unpause <SITE> | pause-all | unpause-all"
        ;;
    esac
    ;;

  headscale)
    docker compose -f "$HUB_COMPOSE_DIR/docker-compose.yml" \
      exec headscale headscale "$@"
    ;;

  inject)
    cd "$SCRIPT_DIR"
    python3 inject_motion.py "$@"
    ;;

  verify)
    section "Quick verification checks"

    echo -e "\n${YELLOW}1. Headscale nodes:${NC}"
    docker compose -f "$HUB_COMPOSE_DIR/docker-compose.yml" \
      exec headscale headscale nodes list 2>/dev/null | grep -E "SITE|nvr" || echo "  (none)"

    echo -e "\n${YELLOW}2. Hub NVR heartbeats (last 5):${NC}"
    docker compose -f "$HUB_COMPOSE_DIR/docker-compose.yml" \
      exec postgres psql -U surv sarvanetra -c \
      "SELECT site_code, last_heartbeat, is_provisioned FROM nvr_node ORDER BY last_heartbeat DESC NULLS LAST LIMIT 10;" \
      2>/dev/null || echo "  (could not query DB)"

    echo -e "\n${YELLOW}3. Simulated cameras in hub DB:${NC}"
    docker compose -f "$HUB_COMPOSE_DIR/docker-compose.yml" \
      exec postgres psql -U surv sarvanetra -c \
      "SELECT cam_id, is_online, last_seen FROM survapp_camera_master WHERE cam_id LIKE 'SIMCAM%' ORDER BY cam_id;" \
      2>/dev/null || echo "  (could not query DB)"

    echo -e "\n${YELLOW}4. HLS stream test (SITE01 cam-01):${NC}"
    curl -sI "http://10.44.0.209:9888/SIMCAM-SITE01-01/index.m3u8" 2>/dev/null | \
      head -3 || echo "  (not reachable yet)"

    echo -e "\n${YELLOW}5. RTSP port check (SITE01):${NC}"
    curl -sv --max-time 3 "rtsp://10.44.0.209:9554" 2>&1 | grep -E "RTSP|Connected|refused" || \
      echo "  (not reachable)"
    ;;

  help|*)
    echo ""
    echo -e "${CYAN}Sarvanetra Edge NVR Simulation Manager${NC}"
    echo ""
    echo "  ./sim_manage.sh up [SITE_CODE]           Bring up all or one site"
    echo "  ./sim_manage.sh down [SITE_CODE]         Tear down all or one site"
    echo "  ./sim_manage.sh restart [SITE_CODE]      Restart"
    echo "  ./sim_manage.sh status                   Show running containers + headscale nodes"
    echo "  ./sim_manage.sh logs SITE_CODE [SVC]     Tail logs"
    echo "  ./sim_manage.sh chaos pause SITE_CODE    Pause tailscale (WAN-drop test)"
    echo "  ./sim_manage.sh chaos unpause SITE_CODE  Restore tailscale"
    echo "  ./sim_manage.sh chaos pause-all          Pause all (reconnect storm prep)"
    echo "  ./sim_manage.sh chaos unpause-all        Unpause all simultaneously"
    echo "  ./sim_manage.sh headscale [args...]      Pass-through to headscale CLI"
    echo "  ./sim_manage.sh inject [args...]         Run inject_motion.py"
    echo "  ./sim_manage.sh verify                   Run quick sanity checks"
    echo ""
    echo "First-time setup:"
    echo "  bash setup_sim.sh"
    echo "  bash generate_clips.sh"
    echo "  ./sim_manage.sh up"
    echo ""
    ;;
esac
