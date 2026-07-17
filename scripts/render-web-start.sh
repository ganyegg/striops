#!/usr/bin/env bash
# Render.com — Helm web (Next.js on $PORT)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"
export NODE_ENV=production
export NEXT_TELEMETRY_DISABLED=1
exec npx next start -H 0.0.0.0 -p "${PORT:-3000}"
