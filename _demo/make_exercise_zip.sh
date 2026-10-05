#!/usr/bin/env bash
# Pack the files students need for the afternoon exercises into one zip.
# Used by .github/workflows/exercise-zip.yml; also works locally:
#     bash _demo/make_exercise_zip.sh        → dist/gis-modelling-exercises.zip
#
# Not included (repository only): python/ (scripts that made the slide figures)
# and outputs/qgis/ (raw screenshots for the slides).
set -euo pipefail

NAME="gis-modelling-exercises"
REPO="$(cd "$(dirname "$0")/.." && pwd)"
DIST="$REPO/dist"
STAGE="$(mktemp -d)/$NAME"

FILES=(
  README.md
  dem
  outputs/dem
  outputs/abm
  qgis
)

mkdir -p "$STAGE" "$DIST"
for path in "${FILES[@]}"; do
  mkdir -p "$STAGE/$(dirname "$path")"
  cp -R "$REPO/_demo/$path" "$STAGE/$path"
done
find "$STAGE" \( -name ".DS_Store" -o -name "*.aux.xml" -o -name "__pycache__" \) -prune -exec rm -rf {} +

rm -f "$DIST/$NAME.zip"
(cd "$(dirname "$STAGE")" && zip -qrX "$DIST/$NAME.zip" "$NAME")
echo "wrote $DIST/$NAME.zip"
unzip -l "$DIST/$NAME.zip" | tail -n +4 | sed '$d' | sed '$d' | awk '{print "  " $4}'
