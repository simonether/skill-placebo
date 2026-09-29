#!/bin/bash
# After the running Claude Code kill test: resume it (retries), then Codex selection and kill test.
cd "$(dirname "$0")/.." || exit 1
while pgrep -f "scripts/[p]ilot.py kill --harness claude-code" >/dev/null; do sleep 30; done
echo "$(date) CC kill process gone"
uv run python -u scripts/pilot.py kill --harness claude-code --units-budget 145e6 --usd-budget 370 \
  --window-start 2026-09-28T10:00:00Z --pace-units-5h 75e6 --pace-usd-5h 200 --claude-week-start 0.04 >> jobs/pilot-cc-kill.log 2>&1
echo "cc kill resume exit=$?"
tail -3 jobs/pilot-cc-kill.log | grep -q "STOP" && { echo "CC stopped - not starting Codex"; exit 0; }
uv run python -u scripts/pilot.py selection --harness codex --codex-weekly-start 12 > jobs/pilot-cx-selection.log 2>&1
echo "cx selection exit=$?"
tail -3 jobs/pilot-cx-selection.log | grep -q "STOP" && { echo "Codex selection stopped"; exit 0; }
uv run python -u scripts/pilot.py kill --harness codex --codex-weekly-start 12 > jobs/pilot-cx-kill.log 2>&1
echo "cx kill exit=$?"
tail -3 jobs/pilot-cx-kill.log
