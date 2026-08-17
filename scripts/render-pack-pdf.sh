#!/usr/bin/env bash
# Render the docs/pitch HTML documents to PDF, in both palettes.
#
# Each document carries a dark and a light theme in one file, selected with
# ?theme=light. This writes <name>.pdf (dark, for screen and projection) and
# <name>-light.pdf (for printing on paper).
#
# Chromium on macOS writes the PDF and then hangs before exiting, so this polls
# for a complete file (%%EOF present) and kills the process rather than waiting
# on it. It also uses a throwaway profile — headless against the user's live
# profile blocks on the profile lock.
#
#   scripts/render-pack-pdf.sh                          # everything, both themes
#   scripts/render-pack-pdf.sh mayor-meeting-pack       # one document, both themes
#   scripts/render-pack-pdf.sh --theme light            # every document, light only
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PITCH="$ROOT/docs/pitch"
BROWSER="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
[ -x "$BROWSER" ] || BROWSER="/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
[ -x "$BROWSER" ] || { echo "No Chrome or Edge found." >&2; exit 1; }

WANT_THEME="both"
NAMES=""
while [ $# -gt 0 ]; do
  case "$1" in
    --theme) WANT_THEME="${2:-}"; shift 2 ;;
    --theme=*) WANT_THEME="${1#*=}"; shift ;;
    -h|--help) sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) NAMES="$NAMES ${1%.html}"; shift ;;
  esac
done
case "$WANT_THEME" in
  both|dark|light) ;;
  *) echo "--theme must be dark, light or both" >&2; exit 1 ;;
esac
[ -n "$NAMES" ] || NAMES="striops-pitch mayor-meeting-pack"

complete() { # a PDF is safe to use once the trailer is written
  [ -s "$1" ] && tail -c 32 "$1" | grep -q '%%EOF'
}

render() { # render <html-path> <pdf-path> <url>
  local src="$1" out="$2" url="$3" profile pid i
  profile="$(mktemp -d)"
  rm -f "$out"
  "$BROWSER" --headless=new --disable-gpu --no-sandbox --no-first-run \
    --disable-extensions --user-data-dir="$profile" \
    --no-pdf-header-footer --virtual-time-budget=15000 \
    --print-to-pdf="$out" "$url" >/dev/null 2>&1 &
  pid=$!
  for i in $(seq 1 60); do
    complete "$out" && break
    kill -0 "$pid" 2>/dev/null || break
    sleep 1
  done
  sleep 1 # let the trailer flush before stopping the hung browser
  kill -9 "$pid" 2>/dev/null || true
  wait "$pid" 2>/dev/null || true
  rm -rf "$profile"
  complete "$out"
}

for name in $NAMES; do
  src="$PITCH/$name.html"
  [ -f "$src" ] || { echo "missing $src" >&2; exit 1; }

  for theme in dark light; do
    [ "$WANT_THEME" = both ] || [ "$WANT_THEME" = "$theme" ] || continue

    if [ "$theme" = light ]; then
      out="$PITCH/$name-light.pdf"; url="file://$src?theme=light"
    else
      out="$PITCH/$name.pdf"; url="file://$src"
    fi

    if render "$src" "$out" "$url"; then
      pages=$("$ROOT/backend/.venv/bin/python" -c "
import sys, pypdf
print(len(pypdf.PdfReader(sys.argv[1]).pages))" "$out" 2>/dev/null || echo "?")
      printf '%-30s %-5s %s pages, %s KB\n' "$(basename "$out")" "$theme" \
        "$pages" "$(( $(wc -c < "$out") / 1024 ))"
    else
      echo "FAILED to render $(basename "$out")" >&2
      exit 1
    fi
  done
done
