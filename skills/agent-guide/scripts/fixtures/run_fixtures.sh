#!/usr/bin/env bash
# Runs every fixture case for guide_check.py and product_index.py on a temporary
# workspace: _shared/ (an invented store file and saved pages) overlaid with the
# case's own workspace/, minus the paths in its remove.txt. Each case.txt gives
# "script|expected exit|arguments"; expect.txt lists lines the output must contain.
# Exits non-zero on any miss. No network.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
misses=0
total=0
for dir in "$HERE"/*/; do
  name="$(basename "$dir")"
  [ "$name" = "_shared" ] && continue
  [ -f "$dir/case.txt" ] || continue
  IFS='|' read -r script expected args < "$dir/case.txt"
  total=$((total + 1))
  tmp="$(mktemp -d)"
  cp -R "$HERE/_shared" "$tmp/workspace"
  cp -R "$dir/workspace/." "$tmp/workspace/"
  if [ -f "$dir/remove.txt" ]; then
    while IFS= read -r gone; do
      [ -n "$gone" ] && rm -rf "$tmp/workspace/$gone"
    done < "$dir/remove.txt"
  fi
  # shellcheck disable=SC2086
  output="$(python3 -I "$HERE/../$script" "$tmp/workspace" $args 2>&1)"
  code=$?
  ok=1
  if [ "$code" != "$expected" ]; then
    echo "MISS $name: exit $code, expected $expected"
    ok=0
  fi
  while IFS= read -r want; do
    [ -z "$want" ] && continue
    if ! printf '%s\n' "$output" | grep -qF -- "$want"; then
      echo "MISS $name: output lacks: $want"
      ok=0
    fi
  done < "$dir/expect.txt"
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
