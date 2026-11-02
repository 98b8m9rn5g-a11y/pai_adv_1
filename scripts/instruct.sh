#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
if (($# == 0)); then
  echo 'Usage: bash scripts/instruct.sh "荷物を受付へ届けて"' >&2
  exit 2
fi
docker compose exec -T sim /ros_entrypoint.sh \
  python3 /work/scripts/send-instruction.py "$*"
