#!/usr/bin/env bash
# Render.com — Striops API (FastAPI / uvicorn on $PORT)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="$ROOT/backend${PYTHONPATH:+:$PYTHONPATH}"
export STRIOPS_DATASETS_DIR="${STRIOPS_DATASETS_DIR:-$ROOT/datasets}"
export STRIOPS_ENV="${STRIOPS_ENV:-production}"
PORT="${PORT:-8000}"
cd "$ROOT/backend"
exec python -m uvicorn striops.api.main:app --host 0.0.0.0 --port "$PORT"
