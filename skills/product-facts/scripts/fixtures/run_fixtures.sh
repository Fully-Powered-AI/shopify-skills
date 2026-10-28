#!/usr/bin/env bash
# Runs every fixture case for the product-facts scripts on a temporary copy of
# its workspace. A case misses when the exit code differs, a line of
# expect.txt is absent from the output, a line of reject.txt is present in the
# output or a written file, a "path|text" line of expect-files.txt is absent
# from that written file, a written import file differs from
# expected-import.csv, or a refused import wrote a file. Exits non-zero on any
# miss. No case touches the network; every store in the cases is invented.
# The fact-slots-self-test case runs the shared module's own cases
# (references/schemas.md section 12); its workspace is an empty folder.
set -u
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
S="$HERE/.."
misses=0
total=0
IMP="products/facts-2026-10-01.md --export exports/products-2026-10-01.csv"

# case | script | expected exit | arguments after the workspace (REF = the case's reference.md)
CASES=(
  "gaps-green|product_gaps.py|0|--date 2026-10-01"
  "gaps-no-pages|product_gaps.py|2|--date 2026-10-01"
  "gaps-no-store|product_gaps.py|1|--date 2026-10-01"
  "gaps-product-lines|product_gaps.py|0|--date 2026-10-01"
  "gaps-slot-on-field-line|product_gaps.py|0|--date 2026-10-01"
  "review-skeleton|review_file.py|0|--date 2026-10-01"
  "review-check-flagged|review_file.py|2|--date 2026-10-01 --check"
  "review-out-of-line|review_file.py|2|--date 2026-10-01"
  "review-check-sources|review_file.py|0|--date 2026-10-01 --check"
  "import-green|product_import.py|2|$IMP"
  "import-verified|product_import.py|0|$IMP --reference REF"
  "import-one-product|product_import.py|2|$IMP --handles ember-bowl"
  "import-no-approved|product_import.py|1|$IMP"
  "import-no-export|product_import.py|1|products/facts-2026-10-01.md"
  "import-unknown-handle|product_import.py|1|$IMP"
  "import-unknown-image|product_import.py|1|$IMP"
  "import-column-missing|product_import.py|1|$IMP"
  "gaps-unit-rule|product_gaps.py|0|--date 2026-10-01"
  "gaps-line-kinds|product_gaps.py|0|--date 2026-10-01"
  "fine-zero|review_file.py|0|--date 2026-10-01"
  "review-fine-accounted|review_file.py|2|--date 2026-10-01"
  "import-description-only|product_import.py|0|$IMP"
  "import-with-alt|product_import.py|2|$IMP"
  "fact-slots-self-test|fact_slots.py|0|--self-test"
)

for spec in "${CASES[@]}"; do
  IFS='|' read -r name script expected args <<< "$spec"
  total=$((total + 1))
  tmp="$(mktemp -d)"
  cp -R "$HERE/$name/workspace" "$tmp/workspace"
  args="${args//REF/$HERE/$name/reference.md}"
  # shellcheck disable=SC2086
  output="$(python3 -I "$S/$script" "$tmp/workspace" $args 2>&1)"
  code=$?
  ok=1
  if [ "$code" != "$expected" ]; then
    echo "MISS $name: exit $code, expected $expected"; ok=0
  fi
  if [ -f "$HERE/$name/expect.txt" ]; then
    while IFS= read -r want; do
      [ -z "$want" ] && continue
      printf '%s\n' "$output" | grep -qF -- "$want" || { echo "MISS $name: output lacks: $want"; ok=0; }
    done < "$HERE/$name/expect.txt"
  fi
  if [ -f "$HERE/$name/reject.txt" ]; then
    while IFS= read -r unwanted; do
      [ -z "$unwanted" ] && continue
      if printf '%s\n' "$output" | grep -qF -- "$unwanted"; then echo "MISS $name: output should not contain: $unwanted"; ok=0; fi
      for f in "$tmp"/workspace/products/*; do
        [ -f "$f" ] || continue
        # the review file is an input to the import and check cases, so it is not searched there
        case "$name:$f" in import-*:*facts-*|review-check-*:*facts-*) continue ;; esac
        if grep -qF -- "$unwanted" "$f"; then echo "MISS $name: $(basename "$f") should not contain: $unwanted"; ok=0; fi
      done
    done < "$HERE/$name/reject.txt"
  fi
  if [ -f "$HERE/$name/expect-files.txt" ]; then
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      path="${line%%|*}"; want="${line#*|}"
      if [ ! -f "$tmp/workspace/$path" ]; then echo "MISS $name: $path not written"; ok=0; continue; fi
      grep -qF -- "$want" "$tmp/workspace/$path" || { echo "MISS $name: $path lacks: $want"; ok=0; }
    done < "$HERE/$name/expect-files.txt"
  fi
  if [ -f "$HERE/$name/expected-import.csv" ]; then
    if ! diff -q "$tmp/workspace/products/product-import-2026-10-01.csv" "$HERE/$name/expected-import.csv" > /dev/null 2>&1; then
      echo "MISS $name: the import file differs from expected-import.csv"; ok=0
    fi
  fi
  if [ "$code" = 1 ] && [ -f "$tmp/workspace/products/product-import-2026-10-01.csv" ]; then
    echo "MISS $name: a refused run wrote an import file"; ok=0
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
