#!/usr/bin/env bash
# Render.com — Helm API (FastAPI / uvicorn on $PORT)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
export HELM_DATASETS_DIR="${HELM_DATASETS_DIR:-$ROOT/datasets}"
export HELM_ENV="${HELM_ENV:-production}"
PORT="${PORT:-8000}"
cd "$ROOT/backend"
exec python -m uvicorn helm.api.main:app --host 0.0.0.0 --port "$PORT"
