#!/usr/bin/env bash
# Render.com — Striops web build (Next.js, standalone output)
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

# `output: "standalone"` emits a self-contained server at .next/standalone/,
# but static assets and public/ must be copied in alongside it.
cp -r public .next/standalone/public
mkdir -p .next/standalone/.next/static
cp -r .next/static/. .next/standalone/.next/static/
