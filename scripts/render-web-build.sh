#!/usr/bin/env bash
# Render.com — Striops web build (Next.js)
# Keep install able to see devDependencies even when NODE_ENV=production.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/frontend"

export NPM_CONFIG_PRODUCTION=false
export NODE_ENV="${NODE_ENV:-production}"
export NEXT_TELEMETRY_DISABLED=1
# Free-tier instances are memory-tight during `next build`
export NODE_OPTIONS="${NODE_OPTIONS:---max-old-space-size=460}"

if [[ -f package-lock.json ]]; then
  npm ci
else
  npm install
fi

npm run build
