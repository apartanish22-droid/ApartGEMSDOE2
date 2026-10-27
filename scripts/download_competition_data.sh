#!/usr/bin/env bash
# scripts/download_competition_data.sh
#
# GEMS Prize Challenge data placement script.
#
# STATUS: BLOCKED IN THIS SANDBOX (verified).
#   * DrivenData data tab (https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
#     requires login; the page redirects to a login wall. Files training_features.tif,
#     labels.tif, sample_submission.tif, 1m_DEM_links.csv cannot be auto-downloaded here.
#   * Public Dropbox mirrors found in competition materials are hosted on www.dropbox.com,
#     which is NOT in this sandbox's outbound allowlist (only github.com/*,
#     codeload.github.com, api.github.com, registry.npmjs.org, pypi.org,
#     files.pythonhosted.org are reachable). Verified: TLS connection closed on both
#     buffedlizard55-lab.github.io and www.dropbox.com.
#
# ACTION REQUIRED (manual, on any machine with DrivenData access):
#   1. Log in to https://www.drivendata.org/competitions/306/competition-doe-gems/data/
#   2. Download: numeric_features.tif (or training_features.tif), labels.tif, and the
#      sample_submission.tif / example_submission.tif format reference.
#   3. Place them in this repo's data/ directory:
#        data/numeric_features.tif
#        data/labels.tif
#        data/example_submission.tif   # format reference (grid = CRS/shape/transform target)
#   4. Re-run: python scripts/prepare_data.py  -> python src/generate_submission.py
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="$REPO_ROOT/data"

echo "=== GEMS Prize Challenge data placement ==="
echo "Repo root: $REPO_ROOT"
echo "Data dir:  $DATA_DIR"

mkdir -p "$DATA_DIR"

if [ -f "$DATA_DIR/numeric_features.tif" ] && [ -f "$DATA_DIR/labels.tif" ]; then
  echo "OK: data/numeric_features.tif and data/labels.tif already present."
  ls -lh "$DATA_DIR"
  exit 0
fi

echo ""
echo "BLOCKER: competition data not found in data/."
echo "This sandbox cannot reach DrivenData (login wall) or Dropbox (not in allowlist)."
echo "Please download manually on an authenticated machine and place files in $DATA_DIR:"
echo "  - numeric_features.tif   (multi-band feature stack, EPSG:32611, 100 m)"
echo "  - labels.tif             (fault labels, same grid)"
echo "  - example_submission.tif (optional format reference)"
echo ""
echo "Official data page: https://www.drivendata.org/competitions/306/competition-doe-gems/data/"
echo "DOE data package:   https://gdr.openei.org/submissions/1391"
echo "Reference solution: https://github.com/drivendataorg/gems-prize-reference-solution"
echo ""
echo "After placement, run: python scripts/prepare_data.py"
exit 1
