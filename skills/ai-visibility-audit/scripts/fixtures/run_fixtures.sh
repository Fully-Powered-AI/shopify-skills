#!/usr/bin/env bash
# Runs every fixture under scripts/fixtures/ and exits non-zero on any miss. No network: the fetch fixtures use
# --dry-run, the plan-only path, or inputs refused before any request.
#
# A fixture folder holds:
#   cmd          one line: a script name and its arguments, with WS standing for the fixture's workspace copy
#   expect.txt   "exit N", then any of: "contains: TEXT", "absent: TEXT" (script output), "file: PATH" / "nofile: PATH"
#                (in the workspace), "filehas: PATH TEXT" (TEXT in that workspace file), "json: VNN OUTCOME" and
#                "priority: VNN P" (in the audit JSON), "md: TEXT" / "mdabsent: TEXT" (in the audit Markdown)
#   workspace/   the files the fixture adds or replaces
#   base         optional: the name of another fixture whose workspace is copied first
#   remove.txt   optional: workspace paths removed after the copy, to make a file missing on purpose
#   pre          optional: lines in the cmd form, run in order before cmd; each must exit 0
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCRIPTS="$(dirname "$HERE")"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
fail=0; count=0

build() {  # build <fixture> <dest>
  local fx="$HERE/${1}" dest="${2}"
  if [ -f "$fx/base" ]; then build "$(tr -d '[:space:]' < "$fx/base")" "$dest"; fi
  if [ -d "$fx/workspace" ]; then cp -R "$fx/workspace/." "$dest/"; fi
  if [ -f "$fx/remove.txt" ]; then
    while IFS= read -r p; do [ -n "$p" ] && rm -rf "$dest/$p"; done < "$fx/remove.txt"
  fi
}

for fx in "$HERE"/*/; do
  name="$(basename "$fx")"
  [ -f "$fx/cmd" ] || continue
  count=$((count + 1))
  ws="$TMP/$name"; mkdir -p "$ws"
  build "$name" "$ws"
  premiss=""
  if [ -f "$fx/pre" ]; then
    while read -r pscript pargs; do
      [ -z "$pscript" ] && continue
      pargs="${pargs//WS/$ws}"
      # shellcheck disable=SC2086
      (cd "$TMP" && python3 -I "$SCRIPTS/$pscript" "$ws" ${pargs#"$ws"} >/dev/null 2>&1) || premiss="$premiss; pre step $pscript failed"
    done < "$fx/pre"
  fi
  read -r script args < "$fx/cmd"
  args="${args//WS/$ws}"
  # shellcheck disable=SC2086
  out="$(cd "$TMP" && python3 -I "$SCRIPTS/$script" "$ws" ${args#"$ws"} 2>&1)"; code=$?
  miss="$premiss"
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    kind="${line%%:*}"; val="${line#*: }"
    case "$line" in
      exit\ *) want="${line#exit }"; [ "$code" = "$want" ] || miss="$miss; exit $code, wanted $want" ;;
      contains:*) grep -qF -- "$val" <<<"$out" || miss="$miss; output lacks '$val'" ;;
      absent:*) grep -qF -- "$val" <<<"$out" && miss="$miss; output has '$val'" ;;
      file:*) [ -e "$ws/$val" ] || miss="$miss; missing file $val" ;;
      nofile:*) [ -e "$ws/$val" ] && miss="$miss; unexpected file $val" ;;
      filehas:*) fp="${val%% *}"; txt="${val#* }"; { [ -f "$ws/$fp" ] && grep -qF -- "$txt" "$ws/$fp"; } || miss="$miss; $fp lacks '$txt'" ;;
      mdabsent:*) f="$(ls "$ws"/visibility/audit-*.md 2>/dev/null | head -1)"; { [ -n "$f" ] && ! grep -qF -- "$val" "$f"; } || miss="$miss; audit Markdown has '$val' or is missing" ;;
      md:*) f="$(ls "$ws"/visibility/audit-*.md 2>/dev/null | head -1)"; { [ -n "$f" ] && grep -qF -- "$val" "$f"; } || miss="$miss; audit Markdown lacks '$val'" ;;
      json:*|priority:*)
        f="$(ls "$ws"/visibility/audit-*.json 2>/dev/null | head -1)"
        read -r id want <<<"$val"
        key=outcome; [ "$kind" = "priority" ] && key=priority
        got="$( [ -n "$f" ] && python3 -I -c 'import json,sys; d=json.load(open(sys.argv[1])); print(next((c[sys.argv[3]] for c in d["checks"] if c["id"]==sys.argv[2]), "absent"))' "$f" "$id" "$key" 2>/dev/null)"
        [ "$got" = "$want" ] || miss="$miss; $id $key is '$got', wanted '$want'" ;;
    esac
  done < "$fx/expect.txt"
  if [ -n "$miss" ]; then
    echo "FAIL $name${miss}"
    echo "$out" | head -20 | sed 's/^/    /'
    fail=$((fail + 1))
  else
    echo "ok   $name"
  fi
done
echo "$count fixture(s), $fail failed"
[ "$fail" -eq 0 ] && [ "$count" -gt 0 ]
