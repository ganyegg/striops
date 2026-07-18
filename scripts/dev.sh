#!/usr/bin/env bash
# Striops local dev helper.
#   ./scripts/dev.sh up       -> docker compose up --build
#   ./scripts/dev.sh ingest   -> run the ingestion pipeline
#   ./scripts/dev.sh backend  -> run FastAPI locally (needs venv + deps)
#   ./scripts/dev.sh frontend -> run Next.js dev server
#   ./scripts/dev.sh test     -> run backend pytest
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

cmd="${1:-up}"
case "$cmd" in
  up)       docker compose up --build ;;
  ingest)   docker compose run --rm ingest ;;
  backend)  cd backend && uvicorn striops.api.main:app --reload ;;
  frontend) cd frontend && npm run dev ;;
  test)     cd backend && python -m pytest -q ;;
  *) echo "unknown command: $cmd" >&2; exit 1 ;;
esac
