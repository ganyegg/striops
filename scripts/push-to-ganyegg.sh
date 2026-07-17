#!/usr/bin/env bash
# Delegates to the IGG workspace push script (canonical owner: ganyegg).
set -euo pipefail
exec "$(cd "$(dirname "$0")/../.." && pwd)/scripts/push-to-ganyegg.sh" "$(basename "$(cd "$(dirname "$0")/.." && pwd)")"
