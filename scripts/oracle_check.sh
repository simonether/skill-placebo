#!/bin/bash
# Oracle validation of the task pool: reference solutions, no model calls (METHOD.md section 6).
# Runs every pool task twice with Harbor's oracle agent in a clean environment.
set -u
cd "$(dirname "$0")/.."
for src in ${SOURCES:-swebench-verified terminal-bench-2-1 openthoughts-tblite}; do
  env -i PATH="$PATH" HOME="$HOME" LANG="${LANG:-en_US.UTF-8}" HARBOR_TELEMETRY=0 \
    uv run harbor run -p "tasks/pool/$src" -a oracle -k 2 -n 2 -o jobs/oracle --job-name "oracle-$src" --yes
done
