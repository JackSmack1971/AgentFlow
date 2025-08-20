#!/usr/bin/env bash
set -euo pipefail
cp -n .env.example .env || true
docker compose up -d
echo "[OK] Infra started. Run API: uvicorn apps.api.app.main:app --reload"
