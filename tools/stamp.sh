#!/bin/sh
# Stamp a new version into index.html and version.json before publishing,
# so installed copies notice the update and reload.
# The checks in tests/check.py run first: a failure stops here, so a broken
# page never gets a version to ship. SKIP_CHECKS=1 skips them.
cd "$(dirname "$0")/.." || exit 1
if [ -z "$SKIP_CHECKS" ]; then
  if ! python3 tests/check.py > /tmp/scorecard-check.log 2>&1; then
    grep -E "FAIL|failed" /tmp/scorecard-check.log; echo "Checks failed: not stamped." >&2; exit 1
  fi
  echo "checks passed" >&2
fi
V=$(TZ=America/Chicago date +%Y.%m.%d-%H%M)
sed -i "s/<meta name=\"agate-version\" content=\"[^\"]*\">/<meta name=\"agate-version\" content=\"$V\">/" index.html
printf '{"v":"%s"}\n' "$V" > version.json
echo "$V"
