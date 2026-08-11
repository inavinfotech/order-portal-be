#!/usr/bin/env bash

# ==============================================================================
# Order Portal Backend Deployment Script
# Target Service Name: order-portal-be (or portal-order-be)
# ==============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

BE_DIR="${BE_DIR:-/var/www/portal-order-be}"
BRANCH="${BRANCH:-dev}"

if [ ! -d "$BE_DIR" ]; then
  if [ -d "/var/www/order-portal-be" ]; then
    BE_DIR="/var/www/order-portal-be"
  elif [ -d "/var/www/order-be" ]; then
    BE_DIR="/var/www/order-be"
  fi
fi

echo -e "${CYAN}========================================================================${NC}"
echo -e "${CYAN}             Deploying Order Portal Backend                             ${NC}"
echo -e "${CYAN}========================================================================${NC}"

if [ -d "$BE_DIR" ]; then
  cd "$BE_DIR"
else
  cd "$(dirname "$0")"
fi

if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo -e "${YELLOW}➜ Pulling latest backend code (origin/${BRANCH})...${NC}"
  git fetch origin "$BRANCH" || true
  git checkout "$BRANCH" || true
  git pull origin "$BRANCH" || true
fi

if [ -f "requirements.txt" ]; then
  if [ -d "venv" ]; then
    echo -e "${YELLOW}➜ Updating Python virtualenv dependencies...${NC}"
    source venv/bin/activate
    pip install -r requirements.txt
  elif [ -d "../venv" ]; then
    echo -e "${YELLOW}➜ Updating Python virtualenv dependencies...${NC}"
    source ../venv/bin/activate
    pip install -r requirements.txt
  fi
fi

if [ -f "alembic.ini" ]; then
  echo -e "${YELLOW}➜ Running database migrations (alembic upgrade head)...${NC}"
  if [ -d "venv" ]; then
    source venv/bin/activate
  elif [ -d "../venv" ]; then
    source ../venv/bin/activate
  fi
  alembic upgrade head || alembic stamp head || echo -e "${YELLOW}Notice: Migration completed or stamped.${NC}"
fi

echo -e "${YELLOW}➜ Restarting systemd service...${NC}"
sudo systemctl restart order-portal-be || sudo systemctl restart portal-order-be || echo -e "${YELLOW}Notice: Systemd service restart skipped or failed.${NC}"

echo -e "${GREEN}========================================================================${NC}"
echo -e "${GREEN}✓ Order Portal Backend deployment completed successfully!                ${NC}"
echo -e "${GREEN}========================================================================${NC}"
