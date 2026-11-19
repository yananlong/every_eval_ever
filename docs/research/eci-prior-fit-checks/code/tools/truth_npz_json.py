"""Convert the W3 truth draws between .npz (what runs/w3_calibrate.py reads) and .json (what git stores).

    uv run python tools/truth_npz_json.py to-json  SRC_DIR DST_DIR
    uv run python tools/truth_npz_json.py to-npz   SRC_DIR DST_DIR

Values are written with repr precision, so the round trip is exact for float64 arrays.
"""
import sys, json
from pathlib import Path
import numpy as np


def to_json(src, dst):
    dst.mkdir(parents=True, exist_ok=True)
    for p in sorted(src.glob("*.npz")):
        z = np.load(p)
        (dst / (p.stem + ".json")).write_text(json.dumps({k: dict(dtype=str(z[k].dtype), shape=list(z[k].shape), data=z[k].tolist()) for k in z.files}))


def to_npz(src, dst):
    dst.mkdir(parents=True, exist_ok=True)
    for p in sorted(src.glob("*.json")):
        d = json.loads(p.read_text())
        np.savez_compressed(dst / (p.stem + ".npz"), **{k: np.array(v["data"], dtype=v["dtype"]).reshape(v["shape"]) for k, v in d.items()})


if __name__ == "__main__":
    mode, src, dst = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    {"to-json": to_json, "to-npz": to_npz}[mode](src, dst)
