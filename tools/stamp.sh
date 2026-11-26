#!/bin/sh
# Stamp a new version into index.html and version.json before publishing,
# so installed copies notice the update and reload.
cd "$(dirname "$0")/.." || exit 1
V=$(TZ=America/Chicago date +%Y.%m.%d-%H%M)
sed -i "s/<meta name=\"agate-version\" content=\"[^\"]*\">/<meta name=\"agate-version\" content=\"$V\">/" index.html
printf '{"v":"%s"}\n' "$V" > version.json
echo "$V"
