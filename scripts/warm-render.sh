#!/usr/bin/env bash
# Wake the Render free-tier services and wait until both actually answer.
#
# Free instances sleep after ~15 minutes idle and take ~50-70s to come back.
# The site now waits that out on its own, but a cold first click still costs a
# minute — run this before a demo so the first page load is instant.
#
#   scripts/warm-render.sh            # wake and report
#   scripts/warm-render.sh --watch 25 # keep warm for 25 minutes
set -euo pipefail

API="${STRIOPS_API_URL:-https://striops-api.onrender.com}"
WEB="${STRIOPS_WEB_URL:-https://striops-web.onrender.com}"
WATCH_MINUTES=0

while [ $# -gt 0 ]; do
  case "$1" in
    --watch) WATCH_MINUTES="${2:-20}"; shift 2 ;;
    --watch=*) WATCH_MINUTES="${1#*=}"; shift ;;
    -h|--help) sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 1 ;;
  esac
done

# Health endpoints only — no SSR, so waking costs one cheap request each.
probe() { # probe <label> <url>
  local label="$1" url="$2" start now code elapsed
  start=$(date +%s)
  for _ in $(seq 1 30); do
    code=$(curl -s -o /dev/null -w '%{http_code}' --max-time 30 "$url" || echo 000)
    now=$(date +%s); elapsed=$((now - start))
    if [ "$code" = "200" ]; then
      printf '%-8s awake in %2ds  %s\n' "$label" "$elapsed" "$url"
      return 0
    fi
    sleep 3
  done
  printf '%-8s FAILED after %ds (last status %s)  %s\n' "$label" "$elapsed" "$code" "$url"
  return 1
}

warm() {
  probe "api" "$API/health"
  probe "web" "$WEB/icon.svg"
}

warm

if [ "$WATCH_MINUTES" -gt 0 ]; then
  # Render sleeps at ~15 minutes idle, so a ping every 10 keeps both up.
  deadline=$(( $(date +%s) + WATCH_MINUTES * 60 ))
  echo "keeping warm for ${WATCH_MINUTES}m — ctrl-c to stop"
  while [ "$(date +%s)" -lt "$deadline" ]; do
    sleep 600
    [ "$(date +%s)" -lt "$deadline" ] || break
    printf '[%s] ' "$(date +%H:%M:%S)"
    warm
  done
  echo "done"
fi
