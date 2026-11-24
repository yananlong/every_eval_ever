import sys, json, glob
sys.path.insert(0, "runs")
import w3_calibrate as W, eci
print("eci from", eci.__file__)
d = W.code_dig(); print("code_dig", d)
js = [json.load(open(p)) for p in sorted(glob.glob("runs/W/W3/rep/null_*.json"))]
from collections import Counter
print(Counter((j.get("code_sha256") == d, bool(j.get("timeout"))) for j in js))
import pytensor; print("pytensor cxx:", repr(pytensor.config.cxx))
