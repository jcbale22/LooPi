#!/usr/bin/env bash
# ============================================================
#  LooPi — single-command startup script
#  Usage: ./start.sh
# ============================================================

set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
RESET='\033[0m'

info()    { echo -e "${CYAN}[loopi]${RESET} $*"; }
success() { echo -e "${GREEN}[loopi]${RESET} $*"; }
warn()    { echo -e "${YELLOW}[loopi]${RESET} $*"; }
error()   { echo -e "${RED}[loopi]${RESET} $*"; exit 1; }

echo ""
echo -e "${CYAN}  ██╗      ██████╗  ██████╗ ██████╗ ██╗${RESET}"
echo -e "${CYAN}  ██║     ██╔═══██╗██╔═══██╗██╔══██╗██║${RESET}"
echo -e "${CYAN}  ██║     ██║   ██║██║   ██║██████╔╝██║${RESET}"
echo -e "${CYAN}  ██║     ██║   ██║██║   ██║██╔═══╝ ██║${RESET}"
echo -e "${CYAN}  ███████╗╚██████╔╝╚██████╔╝██║     ██║${RESET}"
echo -e "${CYAN}  ╚══════╝ ╚═════╝  ╚═════╝ ╚═╝     ╚═╝${RESET}"
echo ""

# ── 1. Check Docker is installed ────────────────────────────
if ! command -v docker &>/dev/null; then
  error "Docker is not installed. Install Docker Desktop from https://www.docker.com/products/docker-desktop and re-run."
fi

# ── 2. Check Docker daemon is running ───────────────────────
if ! docker info &>/dev/null; then
  error "Docker daemon is not running. Start Docker Desktop and re-run."
fi

# ── 3. Ensure .env exists ────────────────────────────────────
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    warn ".env not found — copying from .env.example"
    warn "Edit .env and fill in your R2 credentials before continuing."
    cp .env.example .env
    echo ""
    read -rp "  Press Enter once you've updated .env, or Ctrl+C to exit..."
    echo ""
  else
    error ".env file is missing and no .env.example found. Create a .env file with your R2 credentials."
  fi
fi

# ── 4. Ensure data dirs / files exist for volume mounts ─────
mkdir -p app/static/uploads app/data
touch playlists.json metadata.json

# Seed playlists.json if empty
if [ ! -s playlists.json ]; then
  echo '{}' > playlists.json
fi

# Seed metadata.json if empty
if [ ! -s metadata.json ]; then
  echo '{}' > metadata.json
fi

# Seed devices.json if missing
if [ ! -f app/data/devices.json ]; then
  echo '{}' > app/data/devices.json
fi

# ── 5. Stop any existing container ──────────────────────────
if docker compose ps --quiet 2>/dev/null | grep -q .; then
  info "Stopping existing containers..."
  docker compose down
fi

# ── 6. Build & start ────────────────────────────────────────
info "Building and starting LooPi..."
docker compose up --build -d

# ── 7. Wait for the app to respond ──────────────────────────
info "Waiting for app to be ready..."
for i in {1..20}; do
  if curl -sf http://localhost:8000 -o /dev/null 2>/dev/null; then
    break
  fi
  sleep 1
done

echo ""
success "LooPi is running!"
echo ""
echo -e "  ${GREEN}→${RESET} Local:   http://localhost:8000"
echo -e "  ${GREEN}→${RESET} Network: http://$(ipconfig getifaddr en0 2>/dev/null || hostname):8000"
echo ""
echo -e "  Logs:    docker compose logs -f"
echo -e "  Stop:    docker compose down"
echo ""
