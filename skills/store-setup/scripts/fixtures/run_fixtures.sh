#!/usr/bin/env bash
# Runs every fixture case for store_file.py, observe_store.py and the shared
# module fact_slots.py (its --self-test) on a temporary
# copy of its workspace. Exits non-zero if any exit code or expected line is
# missed, or if a line in the case's reject.txt appears. No network.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS="$HERE/.."
misses=0
total=0

# case | script | expected exit | arguments after the workspace
CASES=(
  "green|store_file.py|0|"
  "missing-section|store_file.py|1|"
  "value-without-mark|store_file.py|1|"
  "blank-required|store_file.py|1|"
  "open-items|store_file.py|2|"
  "mark-inside|store_file.py|1|"
  "person-not-role|store_file.py|1|"
  "role-name-with-role|store_file.py|1|"
  "entrance-stray|store_file.py|1|"
  "connection-no-tool|store_file.py|1|"
  "connection-unconfirmed|store_file.py|2|"
  "connection-to-confirm|store_file.py|0|"
  "line-no-colon|store_file.py|1|"
  "line-no-category|store_file.py|2|"
  "init|store_file.py|0|--init"
  "init-exists|store_file.py|1|--init"
  "observe-green|observe_store.py|0|--date 2026-10-21"
  "observe-missing|observe_store.py|2|--date 2026-10-21"
  "observe-nofolder|observe_store.py|1|--date 2026-10-21"
  "observe-connection|observe_store.py|2|--date 2026-10-21 --connection store/connection-2026-10-21.json"
  "observe-coffee-eligible|observe_store.py|0|--date 2026-10-21"
  "observe-catalog-mixed|observe_store.py|0|--date 2026-10-21"
  "fact-slots-self-test|fact_slots.py|0|--self-test"
)

for spec in "${CASES[@]}"; do
  IFS='|' read -r name script expected args <<< "$spec"
  total=$((total + 1))
  tmp="$(mktemp -d)"
  cp -R "$HERE/$name/workspace" "$tmp/workspace"
  # shellcheck disable=SC2086
  output="$(python3 -I "$SCRIPTS/$script" "$tmp/workspace" $args 2>&1)"
  code=$?
  ok=1
  if [ "$code" != "$expected" ]; then
    echo "MISS $name: exit $code, expected $expected"
    ok=0
  fi
  # expect.txt lines are looked for in the script's output and, for the
  # observe cases, in the observation file it wrote.
  written=""
  if [ -f "$tmp/workspace/store/observed-2026-10-21.md" ]; then
    written="$(cat "$tmp/workspace/store/observed-2026-10-21.md")"
  fi
  if [ "$name" = "init" ] && [ -f "$tmp/workspace/store/store.md" ]; then
    written="$(cat "$tmp/workspace/store/store.md")"
  fi
  while IFS= read -r want; do
    [ -z "$want" ] && continue
    if ! printf '%s\n%s\n' "$output" "$written" | grep -qF -- "$want"; then
      echo "MISS $name: lacks: $want"
      ok=0
    fi
  done < "$HERE/$name/expect.txt"
  if [ -f "$HERE/$name/reject.txt" ]; then
    while IFS= read -r unwanted; do
      [ -z "$unwanted" ] && continue
      if printf '%s\n%s\n' "$output" "$written" | grep -qF -- "$unwanted"; then
        echo "MISS $name: should not contain: $unwanted"
        ok=0
      fi
    done < "$HERE/$name/reject.txt"
  fi
  if [ "$ok" = 1 ]; then
    echo "ok   $name (exit $code)"
  else
    misses=$((misses + 1))
    printf '%s\n' "$output" | sed 's/^/     | /'
  fi
  rm -rf "$tmp"
done

echo "fixtures: $((total - misses)) of $total passed"
[ "$misses" = 0 ]
