#!/bin/bash
# Oracle check for a list of pool tasks (one path per line relative to tasks/pool), 2 attempts each.
set -u
cd "$(dirname "$0")/.."
while read -r t; do
  [ -z "$t" ] && continue
  env -i PATH="$PATH" HOME="$HOME" LANG="${LANG:-en_US.UTF-8}" HARBOR_TELEMETRY=0 \
    uv run harbor run -p "tasks/pool/$t" -a oracle -k 2 -n "${N:-2}" -o jobs/oracle --job-name "oracle-$(echo "$t" | sed "s#\.\./##; s#/#-#g")" --yes
done < "${1:?task list}"
