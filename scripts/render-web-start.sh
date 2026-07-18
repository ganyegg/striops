#!/usr/bin/env bash
# Render.com — Striops web (Next.js standalone server on $PORT)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"
export NODE_ENV=production
export NEXT_TELEMETRY_DISABLED=1
export HOSTNAME=0.0.0.0
export PORT="${PORT:-3000}"
exec node .next/standalone/server.js
