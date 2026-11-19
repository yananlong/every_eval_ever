#!/usr/bin/env bash
# Build an untracked work root from this directory and the committed results, so the scripts' relative paths
# ("runs/...", "ext/...") and the frozen freeze.py path assumption resolve unchanged.
# Usage, from the repository root:   bash docs/research/eci-prior-fit-checks/code/setup_workdir.sh [WORK]   (default ./eci_work)
# Layout produced:  WORK/v11/{runs,plan_src,ext}   WORK/wt-pr14 -> the repository root (freeze.py reads the plan from there)
set -euo pipefail
REPO=$(git rev-parse --show-toplevel)
PACK=$REPO/docs/research/eci-prior-fit-checks
WORK=$(mkdir -p "${1:-eci_work}" && cd "${1:-eci_work}" && pwd)
ECI_COMMIT=e04929ab751531e558b1a61e86f436487c710ef8
ZIP_SHA=9d728f9f8635069812530a157aef7a6cec935fffc93f33d3031bad5c6888b1d5
ln -sfn "$REPO" "$WORK/wt-pr14"
mkdir -p "$WORK/v11/ext/epoch_zip" "$WORK/v11/runs/W/W3/rep" "$WORK/v11/runs/W/W3/truth" "$WORK/v11/runs/W/W2"
cp -rp "$PACK/code/runs/." "$WORK/v11/runs/"
cp -rp "$PACK/code/plan_src" "$WORK/v11/"
cp -p "$PACK/results/freeze.json" "$PACK/results/env.json" "$PACK/results/deviations.md" "$WORK/v11/runs/"
cp -p "$PACK/results/W/W3/calibration.json" "$PACK/results/W/W3"/pc_seed*.json "$WORK/v11/runs/W/W3/"
cp -p "$PACK/results/W/W3/rep/"* "$WORK/v11/runs/W/W3/rep/"
cp -p "$PACK/inputs/benchmark_data.zip" "$WORK/v11/ext/epoch_zip/benchmark_data.zip"
# Epoch's code at the recorded commit (not edited, not committed here)
if [ ! -d "$WORK/v11/ext/eci-public/.git" ]; then git clone https://github.com/epoch-research/eci-public.git "$WORK/v11/ext/eci-public"; fi
git -C "$WORK/v11/ext/eci-public" checkout "$ECI_COMMIT"
mkdir -p "$WORK/v11/runs/vendor"
rm -rf "$WORK/v11/runs/vendor/eci-public"
cp -r "$WORK/v11/ext/eci-public" "$WORK/v11/runs/vendor/eci-public"; rm -rf "$WORK/v11/runs/vendor/eci-public/.git"
# environment
cd "$WORK/v11/runs"
uv venv --python 3.13 .venv
uv pip install --python .venv/bin/python -r "$PACK/code/requirements.txt"
uv pip install --python .venv/bin/python --no-deps -e vendor/eci-public
# truth draws: JSON in git, .npz where w3_calibrate.py reads them
.venv/bin/python "$PACK/code/tools/truth_npz_json.py" to-npz "$PACK/results/W/W3/truth" W/W3/truth
cd "$WORK/v11"
# committed input check, then the input that is not in git
if [ -f ext/epoch_zip/benchmark_data.zip ] && [ "$(sha256sum ext/epoch_zip/benchmark_data.zip | cut -d' ' -f1)" = "$ZIP_SHA" ]; then echo "benchmark_data.zip ok"; else
  echo "MISSING: ext/epoch_zip/benchmark_data.zip with sha256 $ZIP_SHA (should come from inputs/ in this pack)"; fi
W2_SHA=88ab45bbb8118f5ef7b0efb904e496268d69a22be470be73521416b290604162
if [ ! -f runs/W/W2/seed12345.nc ]; then
  T=$(mktemp -d); git -C "$REPO" fetch -q origin claude/busy-wright-khj0ky
  git -C "$REPO" archive FETCH_HEAD eci-handoff/W2 | tar -x -C "$T"
  (cd "$T/eci-handoff/W2" && sha256sum -c --quiet <(head -n -1 SHA256SUMS) && cat seed12345.nc.part-* > seed12345.nc)
  mv "$T/eci-handoff/W2/seed12345.nc" runs/W/W2/seed12345.nc; rm -rf "$T"
fi
[ "$(sha256sum runs/W/W2/seed12345.nc | cut -d' ' -f1)" = "$W2_SHA" ] && echo "W2 seed12345.nc ok" || { echo "W2 seed12345.nc sha256 MISMATCH"; exit 1; }
echo "work root: $WORK/v11"
