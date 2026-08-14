#!/usr/bin/env bash
# Render the docs/pitch HTML documents to PDF.
#
# Chromium on macOS writes the PDF and then hangs before exiting, so this polls
# for a complete file (%%EOF present) and kills the process rather than waiting
# on it. It also uses a throwaway profile — headless against the user's live
# profile blocks on the profile lock.
#
#   scripts/render-pack-pdf.sh                      # every document in the pack
#   scripts/render-pack-pdf.sh mayor-meeting-pack   # just one
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PITCH="$ROOT/docs/pitch"
BROWSER="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
[ -x "$BROWSER" ] || BROWSER="/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
[ -x "$BROWSER" ] || { echo "No Chrome or Edge found." >&2; exit 1; }

DOCS=("$@")
if [ ${#DOCS[@]} -eq 0 ]; then
  DOCS=(striops-pitch mayor-meeting-pack)
fi

complete() { # a PDF is safe to use once the trailer is written
  [ -s "$1" ] && tail -c 32 "$1" | grep -q '%%EOF'
}

for name in "${DOCS[@]}"; do
  name="${name%.html}"
  src="$PITCH/$name.html"
  out="$PITCH/$name.pdf"
  [ -f "$src" ] || { echo "missing $src" >&2; exit 1; }

  profile="$(mktemp -d)"
  rm -f "$out"
  "$BROWSER" --headless=new --disable-gpu --no-sandbox --no-first-run \
    --disable-extensions --user-data-dir="$profile" \
    --no-pdf-header-footer --virtual-time-budget=15000 \
    --print-to-pdf="$out" "file://$src" >/dev/null 2>&1 &
  pid=$!

  for _ in $(seq 1 60); do
    complete "$out" && break
    kill -0 "$pid" 2>/dev/null || break
    sleep 1
  done
  # give the trailer a moment to flush, then stop the hung browser
  sleep 1
  kill -9 "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
  rm -rf "$profile"

  if complete "$out"; then
    pages=$("$ROOT/backend/.venv/bin/python" -c "
import sys, pypdf
print(len(pypdf.PdfReader(sys.argv[1]).pages))" "$out" 2>/dev/null || echo "?")
    printf '%-24s %s pages, %s KB\n' "$name.pdf" "$pages" "$(( $(wc -c < "$out") / 1024 ))"
  else
    echo "FAILED to render $name.pdf" >&2
    exit 1
  fi
done
