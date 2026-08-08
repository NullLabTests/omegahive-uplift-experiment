#!/usr/bin/env bash
# OmegaHive experiment entry points.
set -euo pipefail
cd "$(dirname "$0")/.."

case "${1:-run}" in
  run)
    echo "== full governed uplift loop: baseline + cycles 1..3 =="
    python3 -m loop.driver
    ;;
  baseline)
    python3 -m loop.driver --cycle 0
    ;;
  cycle)
    python3 -m loop.driver --cycle "${2:?usage: ./scripts/run.sh cycle N}"
    ;;
  resume)
    python3 -m loop.driver --resume
    ;;
  scorecard)
    cat "logs/scorecards/${2:-baseline}.md"
    ;;
  state)
    cat checkpoints/hive_state.json
    ;;
  synergy)
    python3 scripts/synergy.py
    ;;
  *)
    echo "usage: $0 {run|baseline|cycle N|resume|scorecard N|state|synergy}"
    exit 1
    ;;
esac
