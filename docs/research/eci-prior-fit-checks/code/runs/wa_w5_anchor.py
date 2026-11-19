"""WA A3 (plan M11a): the W5 grid scored under alternative anchor pairs.  Run after W5 from v11/:
    nice -n 19 runs/.venv/bin/python runs/wa_w5_anchor.py                      # reads runs/W/W5/*.npz, writes runs/W/WA/A3/
    nice -n 19 runs/.venv/bin/python runs/wa_w5_anchor.py --standin            # stand-in test on W2 draws only (no W5 needed)
For each resolved W5 entry k and each pair of anchor_pairs.json: entry k and the baseline P0 are both re-anchored on the pair
(targets: P0 posterior-mean ECI of the pair's models; 130/150 for the original pair) and S1-S4 are scored with the frozen
sens_metrics through wa_anchor.score_vs_base. Reports whether any pass/fail flag differs from the original anchoring.
Post-processing only; no sampling. The C1 verdict stays on the original anchoring."""
import sys, json, argparse, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from lib import anchors as A, sens_metrics as sm
import wa_anchor as W

log = lambda *a: print(time.strftime("%H:%M:%S"), *a, flush=True)
PASS_KEYS = ("S1_pass", "S2_pass", "S3_pass")
CORE = ("all", "frontier", "sparse")


def load_w5(d):
    """name -> eci draws (n, M) float64 for P0 and every resolved entry with an .npz, names in the W2 model order."""
    d = Path(d); out = {}
    for npz in sorted(d.glob("*.npz")):
        nm = npz.stem
        js = d / f"{nm}.json"
        if js.exists() and not json.loads(js.read_text()).get("resolved", True): continue
        out[nm] = np.load(npz)["eci"].astype("float64")
    return out


def load_standin():
    """Stand-in for a grid: baseline = W2 seed 12345, entries = W2 seeds 22345 and 32345 (names 'P0', 'S22345', 'S32345')."""
    out = {}
    for s, nm in zip(A.SEEDS, ("P0", "S22345", "S32345")):
        e, _, names = A.load_seed(s); out[nm] = e
    return out


def flags(sc):
    f = {s: {k: bool(sc[s][k]) for k in PASS_KEYS} for s in CORE}
    f["S4"] = bool(sc["S4"]["pass_"])
    return f


def failing(f):
    return sorted([f"{s}:{k[:2]}" for s in CORE for k in PASS_KEYS if not f[s][k]] + ([] if f["S4"] else ["S4"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--w5dir", default="runs/W/W5"); ap.add_argument("--out", default=None)
    ap.add_argument("--standin", action="store_true"); ap.add_argument("--pairs", default="runs/W/WA/anchor_pairs.json")
    ap.add_argument("--no-pij", action="store_true", help="skip the all-pairs P(i>j) invariance check (rank and P(top 10) checks stay)")
    a = ap.parse_args()
    out = Path(a.out or ("runs/W/WA/A3_standin" if a.standin else "runs/W/WA/A3")); out.mkdir(parents=True, exist_ok=True)
    draws = load_standin() if a.standin else load_w5(a.w5dir)
    assert "P0" in draws, "baseline P0 missing"
    _, _, names = A.load_seed(A.SEEDS[0])
    masks = W.strata_masks(names)
    s2_shift = sm.S2_SHIFT
    sj = Path(a.w5dir) / "sensitivity.json"
    if not a.standin and sj.exists():
        s2_shift = float(json.loads(sj.read_text()).get("s2_shift", s2_shift))
    pairs = A.jload(a.pairs)["pairs"]
    io = [names.index(n) for n in A.ORIG]
    P0 = draws["P0"]; p0_mean = P0.mean(0)
    # the baseline must be anchored as Epoch anchors it
    anchor_check = [[float(P0[:, i].min()), float(P0[:, i].max())] for i in io]
    res = dict(source="W2 stand-in (test only)" if a.standin else str(a.w5dir), s2_shift=s2_shift, p0_anchor_ranges=anchor_check, entries=sorted(k for k in draws if k != "P0"), pairs={})
    for p in pairs:
        i_lo, i_hi = p["low_idx"], p["high_idx"]
        tl, th = (130.0, 150.0) if p["id"] == "orig" else (float(p0_mean[i_lo]), float(p0_mean[i_hi]))
        excl = sorted(set(io) | {i_lo, i_hi}); new = [i_lo, i_hi]
        base, _, bad0 = A.reanchor(P0, i_lo, i_hi, tl, th)
        rec = dict(low=p["low"], high=p["high"], target_low=tl, target_high=th, entries={})
        for nm, Dk in draws.items():
            if nm == "P0": continue
            dk, _, badk = A.reanchor(Dk, i_lo, i_hi, tl, th)
            r = dict(n_nonpositive_spread_draws=badk, baseline_nonpositive=bad0)
            n = min(len(dk), len(base))   # the entries and P0 may differ in draw count only if W5 doubled draws for some
            r["scores"] = W.score_vs_base(dk[:n], base[:n], names, masks, excl, new, s2_shift)
            ok = ~np.isnan(dk).any(axis=1)
            r["invariance_within_entry"] = dict(max_abs_rank_diff=int(np.abs(A.rank_matrix(Dk[ok]) - A.rank_matrix(dk[ok])).max()),
                                                max_abs_ptop10_diff=float(np.abs(A.top10_p(Dk[ok]) - A.top10_p(dk[ok])).max()))
            if not a.no_pij:
                r["invariance_within_entry"]["max_abs_pij_diff"] = float(np.abs(A.p_matrix(Dk[ok]) - A.p_matrix(dk[ok])).max())
            rec["entries"][nm] = r
        res["pairs"][p["id"]] = rec
        log("pair", p["id"], "done")
    # does any pass/fail flag differ from the original anchoring?
    summary = {}
    for pid, rec in res["pairs"].items():
        diffs = {}
        for nm, r in rec["entries"].items():
            f0, fk = flags(res["pairs"]["orig"]["entries"][nm]["scores"]), flags(r["scores"])
            if f0 != fk: diffs[nm] = dict(original=failing(f0), this_pair=failing(fk))
        summary[pid] = dict(entries_with_changed_flags=diffs, n_changed=len(diffs),
                            median_width_ratio_all={nm: r["scores"]["all"]["median_width_ratio"] for nm, r in rec["entries"].items()},
                            max_rel_shift_all={nm: r["scores"]["all"]["max_rel_shift"] for nm, r in rec["entries"].items()})
    res["flag_changes_vs_original"] = summary
    (out / "a3.json").write_text(json.dumps(res, indent=1) + "\n")
    log("wrote", out / "a3.json")


if __name__ == "__main__":
    main()
