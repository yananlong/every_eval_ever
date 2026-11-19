"""W6 (M14, exploratory): candidates F0-F7, PSIS-LOO or K-fold, preference rule, reduced SBC, adequate set, multiverse of ECI."""
import sys, json, time, subprocess, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd, xarray as xr
from lib import data, fit as fitmod, fit_any, freeze, models, expand, compare, sbc, sens_metrics as sm

OUT = Path("runs/W/W6"); OUT.mkdir(parents=True, exist_ok=True)
W2, W4, W5 = Path("runs/W/W2"), Path("runs/W/W4"), Path("runs/W/W5")
PY = sys.executable
log = lambda *a: print(time.strftime("%H:%M:%S"), *a, flush=True)
FEATS = {"F1": "2d", "F2": "dev", "F3": "asym", "F4": "drift", "F5": "hetero"}
TIMEOUT = {"F1": 3600}


def call(args, timeout=None):
    cmd = [PY, "runs/w6_fit_one.py"] + args
    try:
        r = subprocess.run(cmd, timeout=timeout, capture_output=True, text=True)
        (OUT / "logs").mkdir(exist_ok=True)
        (OUT / "logs" / ("_".join(a for a in args if not a.startswith("--"))[:60] + ".log")).write_text((r.stdout or "")[-4000:] + (r.stderr or "")[-4000:])
        return r.returncode == 0, "ok" if r.returncode == 0 else (r.stderr or "")[-300:]
    except subprocess.TimeoutExpired:
        return False, "timeout"


def trace_of(name, folder=OUT): return xr.open_datatree(folder / f"{name}.nc")


def side_of(name, folder=OUT): return json.loads((folder / f"{name}.json").read_text())


def fit_candidate(name, features, prior, extra=()):
    nc = OUT / f"{name}.nc"
    if nc.exists(): return side_of(name), "reused"
    args = ["--name", name, "--features", features, "--prior", prior] + list(extra)
    ok, msg = call(args, TIMEOUT.get(name))
    if not ok: return dict(converged=False, error=msg), msg
    return side_of(name), "fitted"


def main():
    ex_rep = json.loads((W2 / "reproduction.json").read_text())
    assert ex_rep["EQ"]["passed"], "EQ failed: W6 is not run"
    v1, v2 = W5 / "verdict_C1.json", W4 / "verdict_C2.json"
    assert v1.exists() and v2.exists(), "C1 and C2 verdict files must exist before W6"
    freeze.freeze("compare.py", "models.py", extra={"verdict_C1_sha256": fitmod.sha_file(v1), "verdict_C2_sha256": fitmod.sha_file(v2)})
    df = data.fit_input(); names = [str(x) for x in xr.open_datatree(W2 / "seed12345.nc")["posterior"].to_dataset()["model"].values]
    strata = json.loads(Path("runs/strata.json").read_text()); masks = {k: np.array([n in set(strata[k]) for n in names]) for k in ("all", "frontier", "sparse", "dense")}
    R = dict(candidates={}, notes=[])
    # ---- baseline and candidates
    t0 = trace_of("f0_seed12345", W2); loo0 = compare.loo_stats(t0); d0 = fitmod.load_eci(W2 / "f0_seed12345.nc")[0]
    R["F0"] = dict(elpd=loo0["elpd"], se=loo0["se"], p_loo=loo0["p"], k_share=loo0["k_share"], n_k_gt_0_7=loo0["n_k_gt_0_7"])
    cand = {}
    for name, feat in FEATS.items():
        log("candidate", name)
        side, how = fit_candidate(name, feat, "epoch", ["--cap4000"] if name == "F1" else [])
        entry = dict(how=how, converged=side.get("converged", False), side={k: side.get(k) for k in ("started_from", "last_attempt", "wall_seconds", "error")})
        if name == "F1" and not (entry["converged"] and side.get("started_from") == "pilot"):
            # fallback step 1: target acceptance 0.99
            log("F1 fallback 1: target_accept 0.99")
            s2, how2 = fit_candidate("F1_ta99", feat, "epoch", ["--cap4000", "--target-accept", "0.99"])
            entry["fallback_1"] = dict(converged=s2.get("converged", False), started_from=s2.get("started_from"), how=how2)
            if s2.get("converged") and s2.get("started_from") == "pilot": name_used, side, entry["converged"] = "F1_ta99", s2, True; entry["fallback_used"] = 1
            else:
                entry["fallback_2_needed"] = True; entry["status"] = "not fitted (fallbacks 1 failed; fallback 2 requires lib/models_f1r.py)"
        cand[name] = entry
    # F6 = PR from W5
    pr = json.loads((W5 / "PR.json").read_text()); cand["F6"] = dict(how="W5", converged=pr["converged"], side=dict(started_from=pr["started_from"], last_attempt=pr["last_attempt"]))
    json.dump(R, open(OUT / "partial.json", "w"), default=str)
    folder = {n: OUT for n in cand}; folder["F6"] = W5
    file_of = {n: n for n in cand}; file_of["F6"] = "PR"
    if cand["F1"].get("fallback_used") == 1: file_of["F1"] = "F1_ta99"
    loo = {}
    for n, e in cand.items():
        if not e["converged"]: e["status"] = e.get("status", "not converged / not fitted"); continue
        tr = trace_of(file_of[n], folder[n]); loo[n] = compare.loo_stats(tr)
        e.update(elpd=loo[n]["elpd"], se=loo[n]["se"], p_loo=loo[n]["p"], k_share=loo[n]["k_share"], n_k_gt_0_7=loo[n]["n_k_gt_0_7"])
    # ---- comparison with F0
    fold = pd.read_csv(W4 / "folds.csv")["fold"].to_numpy(); eligible = np.where(fold >= 0)[0]
    f0kf = pd.read_csv(W4 / "fold_logdens_F0.csv").set_index("row")["logdens_F0"]
    for n, e in cand.items():
        if n not in loo: continue
        trig = compare.kfold_trigger(loo0["k_share"], loo[n]["k_share"]); e["kfold_triggered"] = trig
        if not trig:
            e["estimator"] = "PSIS-LOO"; e["delta"], e["delta_se"] = compare.paired(loo[n]["elpd_i"], loo0["elpd_i"])
        else:
            e["estimator"] = "K-fold"; ok = True; ld = {}
            for f in range(5):
                nz = OUT / "kfold" / f"{n}_fold{f}.npz"
                if not nz.exists():
                    log("kfold", n, f)
                    feat = FEATS.get(n, ""); prior = "reference" if n == "F6" else "epoch"
                    extra = ["--fold", str(f), "--seed", str(12345 + f)] + (["--cap4000"] if n == "F1" else [])
                    okc, msg = call(["--name", n, "--features", feat, "--prior", prior] + extra, TIMEOUT.get(n))
                    if not okc: ok = False; e.setdefault("kfold_errors", []).append(msg); continue
                z = np.load(nz); ld.update(dict(zip(z["rows"].tolist(), z["logd"].tolist()))); e.setdefault("kfold_folds_converged", []).append(bool(z["converged"]))
            if ok and len(ld) == len(eligible):
                dj = np.array([ld[r] for r in eligible]) - f0kf.loc[eligible].to_numpy()
                e["delta"], e["delta_se"] = float(dj.sum()), float(np.sqrt(len(dj)) * dj.std(ddof=1))
            else: e["status"] = "K-fold incomplete"; continue
        e["preferred"] = compare.preferred(e["delta"], e["delta_se"])
        log(n, e["estimator"], "delta", e["delta"], "se", e["delta_se"], "preferred", e["preferred"])
    # ---- reduced SBC for preferred expansions, adoption
    low, high = names.index("Claude 3.5 Sonnet"), names.index("GPT-5"); anchor = np.array([n in sm.ANCHORS for n in names]); na = ~anchor
    rng = np.random.default_rng(20261113)

    def run_sbc(n, feat, prior, src, nrep):
        for r in range(nrep):
            if not (OUT / "sbc" / f"{n}_{r}.json").exists():
                call(["--name", n, "--features", feat, "--prior", prior, "--sbc", str(r), "--n-reps", str(nrep), "--src", str(src)] + (["--cap4000"] if n == "F1" else []), TIMEOUT.get(n))
        reps = [json.loads(p.read_text()) for p in sorted((OUT / "sbc").glob(f"{n}_*.json"))]
        conv = [x for x in reps if x["converged"]]
        U = np.array([x["u_eci"] for x in conv])[:, na]
        cov_all = sbc.coverage(U, masks["all"][na], rng); cov_fr = sbc.coverage(U, masks["frontier"][na], rng)
        ok, passed = sbc.reduced_verdict(cov_all, cov_fr)
        return dict(n_planned=nrep, n_run=len(reps), n_converged=len(conv), c90_all=cov_all["c90"], c50_all=cov_all["c50"], c90_frontier=cov_fr["c90"], checks=ok, passed=bool(passed))
    for n, e in cand.items():
        if e.get("preferred"):
            feat = FEATS.get(n, ""); prior = "reference" if n == "F6" else "epoch"
            e["reduced_sbc"] = run_sbc(n, feat, prior, folder[n] / f"{file_of[n]}.nc", 20 if n == "F1" else 30)
            e["checks_pass"] = bool(e["converged"]); e["adopted"] = bool(e["checks_pass"] and e["reduced_sbc"]["passed"])
            e["status"] = "adopted" if e["adopted"] else "preferred, not adopted"
        elif "preferred" in e: e["status"] = "not preferred"
    adopted = {n: e["delta"] for n, e in cand.items() if e.get("adopted")}
    # ---- combination F7 (I2)
    singles = [n for n in adopted if n in FEATS]
    if len(singles) >= 2:
        top = sorted(singles, key=lambda n: -adopted[n])[:3]; feat7 = ",".join(FEATS[n] for n in top)
        log("F7 features", feat7)
        side, how = fit_candidate("F7", feat7, "epoch")
        e7 = dict(components=top, features=feat7, converged=side.get("converged", False))
        if e7["converged"]:
            tr = trace_of("F7"); l7 = compare.loo_stats(tr); best = max(top, key=lambda n: adopted[n])
            e7.update(elpd=l7["elpd"], k_share=l7["k_share"])
            trig = compare.kfold_trigger(loo[best]["k_share"], l7["k_share"]); e7["kfold_triggered"] = trig; e7["compared_with"] = best
            if not trig:
                e7["estimator"] = "PSIS-LOO"; e7["delta"], e7["delta_se"] = compare.paired(l7["elpd_i"], loo[best]["elpd_i"]); e7["delta_vs_F0"] = compare.paired(l7["elpd_i"], loo0["elpd_i"])[0]
            else:
                e7["estimator"] = "K-fold"; ld = {}
                for f in range(5):
                    nz = OUT / "kfold" / f"F7_fold{f}.npz"
                    if not nz.exists(): call(["--name", "F7", "--features", feat7, "--prior", "epoch", "--fold", str(f), "--seed", str(12345 + f)])
                    z = np.load(nz); ld.update(dict(zip(z["rows"].tolist(), z["logd"].tolist())))
                lb = {}
                for f in range(5):
                    z = np.load(OUT / "kfold" / f"{best}_fold{f}.npz"); lb.update(dict(zip(z["rows"].tolist(), z["logd"].tolist())))
                dj = np.array([ld[r] - lb[r] for r in eligible]); e7["delta"], e7["delta_se"] = float(dj.sum()), float(np.sqrt(len(dj)) * dj.std(ddof=1))
                e7["delta_vs_F0"] = float(np.sum([ld[r] - f0kf.loc[r] for r in eligible]))
            e7["preferred"] = compare.preferred(e7["delta"], e7["delta_se"])
            if e7["preferred"]:
                e7["reduced_sbc"] = run_sbc("F7", feat7, "epoch", OUT / "F7.nc", 20 if "2d" in feat7 else 30)
                e7["adopted"] = bool(e7["reduced_sbc"]["passed"]); e7["status"] = "adopted" if e7["adopted"] else "preferred, not adopted"
                if e7["adopted"]: adopted["F7"] = e7["delta_vs_F0"]
            else: e7["status"] = "not preferred"
        cand["F7"] = e7
    A = compare.adequate_set(adopted)
    # ---- multiverse
    mv = {}
    for n in A:
        draws = fitmod.load_eci(Path(folder.get(n, OUT)) / f"{file_of.get(n, n)}.nc")[0]
        sc = sm.score(draws, d0, names, masks)
        mv[n] = {k: v for k, v in sc.items() if k != "S4"} | {"S4": {a: b for a, b in sc["S4"].items() if not a.startswith("p_top10")}}
        mv[n]["top10_prob_change_max"] = float(np.max(np.abs(np.array(sc["S4"]["p_top10_k"]) - np.array(sc["S4"]["p_top10_0"]))))
        mv[n]["would_pass_C1_thresholds"] = {s: bool(sc[s]["S1_pass"] and sc[s]["S2_pass"] and sc[s]["S3_pass"]) for s in ("all", "frontier", "sparse")} | {"S4": bool(sc["S4"]["pass_"])}
    R["candidates"] = cand; R["adopted"] = sorted(adopted); R["adequate_set"] = A; R["output"] = "base model adequate" if not adopted else "adequate set: " + ", ".join(A)
    R["multiverse_vs_F0"] = mv
    (OUT / "expansion.json").write_text(json.dumps(R, indent=1, default=str)); log("W6 done:", R["output"])


if __name__ == "__main__":
    main()
