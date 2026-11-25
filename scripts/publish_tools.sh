#!/bin/bash
# Uploads the jars listed in anadroid/resources/tools.json as assets of the GitHub release "tools-v1".
# `pyanadroid --setup` downloads the jars from this release.
# Run this script one time from the root of the repository, with a `gh` login that can create releases.
# After it succeeds, remove the jars from git:
#   git rm anadroid/resources/jars/*.jar anadroid/resources/jars/libs/*.jar
#   (keep gradle-wrapper.jar: git reset HEAD anadroid/resources/jars/gradle-wrapper.jar && git checkout anadroid/resources/jars/gradle-wrapper.jar)
set -euo pipefail

TAG="tools-v1"
JARS_DIR="anadroid/resources/jars"
FILES=$(python3 -c "
import json
tools = json.load(open('anadroid/resources/tools.json'))
print(' '.join('$JARS_DIR/' + t['file'] for t in tools.values() if not t.get('archive')))
")

gh release view "$TAG" > /dev/null 2>&1 || gh release create "$TAG" --title "External tools v1" \
    --notes "Jars that PyAnaDroid runs. Downloaded by \`pyanadroid --setup\`. Checksums are in anadroid/resources/tools.json."
# shellcheck disable=SC2086
gh release upload "$TAG" $FILES --clobber
