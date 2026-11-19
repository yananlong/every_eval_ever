"""W5 (M3): S5 screen first, then P0/P0b noise floor, the pre-registered grid P1-P10 X1 X2, the exploratory PR entry and targeted refits."""
import sys, json, time, argparse, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")
import numpy as np, xarray as xr
from lib import data, fit as fitmod, fit_any, freeze, models, sens_metrics as sm

OUT = Path("runs/W/W5"); OUT.mkdir(parents=True, exist_ok=True)
W2, W3 = Path("runs/W/W2"), Path("runs/W/W3")
GRID = json.loads(freeze.PATHS["prior-grid.json"].read_text())
log = lambda *a: print(time.strftime("%H:%M:%S"), *a, flush=True)
HYPER = ("tau_alpha", "sigma_median", "tau_sigma")


def parse(v):  # ["ln 0.25", 0.5] -> (log 0.25, 0.5)
    return (float(np.log(float(v[0].split()[1]))), float(v[1]))


def epoch_priors(entry):
    return {k: parse(v) for k, v in entry.items()}


def powered(prior, a):
    mu, s = prior; return (mu + s * s * (1 - a) / a, s / np.sqrt(a))


def sidecar_ok(js, want):
    if not js.exists(): return None
    old = json.loads(js.read_text()); return old if all(old.get(k) == v for k, v in want.items()) else None


def entry_fit(name, df, names, seed, draws, **kw):
    """One entry with the plan's retry: failed checks -> retry once with draws doubled, then unresolved (G2 'add_evidence' attempt is separate)."""
    js, npz = OUT / f"{name}.json", OUT / f"{name}.npz"
    want = dict(name=name, seed=seed, draws=draws, kw=json.dumps(kw, sort_keys=True, default=str), input_sha256=fitmod.input_digest(df))
    old = sidecar_ok(js, want)
    if old and npz.exists(): return old, np.load(npz)["eci"].astype("float64")
    attempts = []
    for k, dr in enumerate((draws, 2 * draws)):
        log("fit", name, "draws", dr)
        d, warns, wall = fit_any.run(df, seed, draws=dr, **kw)
        ok, last = fitmod.verdict(d["attempts"])
        attempts.append(dict(draws=dr, converged=ok, last_attempt=last, started_from=d["started_from"], wall=round(wall, 1), warnings=warns[:3], ladder=d["attempts"]))
        if ok: break
    side = dict(want, converged=ok, resolved=ok, attempts=attempts, n_draws_total=int(d["eci"].shape[0]))
    np.savez_compressed(npz, eci=d["eci"].astype("float32")); fit_any.atomic_json(js, side)
    save_nc(name, df, d, kw)
    return side, d["eci"].astype("float64")



def save_nc(name, df, d, kw):
    """Posterior (with per-draw ECI) and log_likelihood, thinned to 500 draws per chain, for the per-arm predictive checks (R30). Not committed."""
    import pymc as pm
    from lib import variants
    nc = OUT / f"{name}.nc"
    if nc.exists(): return
    tr = d["trace"]; post = tr["posterior"].to_dataset()
    n_chain, n_draw = post.sizes["chain"], post.sizes["draw"]
    post = post.assign(eci=(("chain", "draw", "model"), np.asarray(d["eci"]).reshape(n_chain, n_draw, -1)))
    post = post.isel(draw=np.linspace(0, n_draw - 1, 500).astype(int))
    if kw.get("variant"):
        m = variants.build(kw["variant"], df, kw.get("s0"), kw.get("noncentred", False))
    else:
        m = models.build_model(df, models.Spec(), priors={**models.DEFAULT_PRIORS, **(kw.get("epoch_priors") or {})})
    t = xr.DataTree.from_dict({"posterior": post})
    with m:
        pm.compute_log_likelihood(t, extend_inferencedata=True, progressbar=False)
    tmp = OUT / f".{name}.nc.tmp"; t.to_netcdf(tmp); import os; os.replace(tmp, nc)

def build_entries(s0):
    ent = {}
    for k, v in GRID["defensible"].items():
        ent[k] = dict(epoch_priors=epoch_priors(v)) if k in ("P1", "P2", "P3", "P4", "P5", "P6", "P7") else dict(variant=k, s0=s0)
    for k, v in GRID["stress_reported_not_scored"].items(): ent[k] = dict(epoch_priors=epoch_priors(v))
    return ent


def strata_masks(names):
    strata = json.loads(Path("runs/strata.json").read_text())
    return {k: np.array([n in set(strata[k]) for n in names]) for k in ("all", "frontier", "sparse", "dense")}


def s5_screen(names, masks):
    """Power-scaling sensitivity of each model's ECI on the W2 seed-12345 draws (M3 S5)."""
    import arviz as az
    t = xr.open_datatree(W2 / "seed12345.nc")
    post = t["posterior"].to_dataset()
    lp = {}
    for h in HYPER:
        mu, s = models.DEFAULT_PRIORS[h]; x = post[h]
        lp["lp_" + h] = -np.log(x) - np.log(s) - 0.5 * np.log(2 * np.pi) - 0.5 * ((np.log(x) - mu) / s) ** 2
    lp["lp_joint"] = lp["lp_tau_alpha"] + lp["lp_sigma_median"] + lp["lp_tau_sigma"]
    t["log_prior"] = xr.DataTree(dataset=xr.Dataset({k: v for k, v in lp.items()}))
    anchor = np.array([n in sm.ANCHORS for n in names]); out = {}
    for case in ("lp_joint",) + tuple("lp_" + h for h in HYPER):
        r = az.psense(t, var_names=["eci"], group="prior", group_var_names=case)
        ds = r.to_dataset() if hasattr(r, "to_dataset") else r
        v = np.asarray(ds["eci"] if "eci" in ds else list(ds.data_vars.values())[0]).ravel()
        res = {}
        for sname, m in masks.items():
            na = m & ~anchor; share = float((v[na] <= 0.05).mean()); res[sname] = dict(n=int(na.sum()), share_le_0_05=share, passes=bool(share >= 0.95), max_psens=float(np.nanmax(v[na])))
        out[case] = dict(by_stratum=res, flagged_strata=[s for s in res if not res[s]["passes"]])
    hyp = {}
    for h in HYPER:
        r = az.psense(t, var_names=[h], group="prior", group_var_names="lp_joint")
        ds = r.to_dataset() if hasattr(r, "to_dataset") else r
        hyp[h] = float(np.asarray(list(ds.data_vars.values())[0]).ravel()[0])
    # importance-reweighted ECI means at alpha 0.8 and 1.25
    rw = {}
    eci = post["eci"].stack(s=("chain", "draw")).transpose("s", "model").to_numpy(); lj = lp["lp_joint"].stack(s=("chain", "draw")).to_numpy()
    for a in (0.8, 1.25):
        lw = (a - 1) * lj
        try:
            from arviz_stats.base import array_stats
            lw2, k = array_stats.psislw(lw[None, :], r_eff=1, axis=-1)
            lw2 = np.asarray(lw2).ravel(); w = np.exp(lw2 - lw2.max()); w /= w.sum(); kk = float(np.asarray(k).ravel()[0])
        except Exception as e:
            w = np.exp(lw - lw.max()); w /= w.sum(); kk = f"psislw unavailable: {type(e).__name__}"
        m = (w[:, None] * eci).sum(0); rw[str(a)] = dict(pareto_k=kk, max_abs_mean_change=float(np.abs(m - eci.mean(0))[~anchor].max()))
    return out, hyp, rw


def noise_floor(d0, db, names):
    s0 = sm.summarise(d0); sb = sm.summarise(db); anchor = np.array([n in sm.ANCHORS for n in names])
    rel = np.abs(sb["mean"] - s0["mean"]) / np.where(anchor, np.nan, s0["width"])
    order0 = np.argsort(-s0["mean"])
    pc = [abs(sm.p_greater(db, order0[r], order0[r + 1]) - sm.p_greater(d0, order0[r], order0[r + 1])) for r in range(9)]
    return dict(max_rel_shift=float(np.nanmax(rel)), max_pair_change=float(max(pc)), passes=bool(np.nanmax(rel) <= .05 and max(pc) <= .03))


def short(sc):
    o = {}
    for k, v in sc.items():
        if isinstance(v, dict): o[k] = {a: b for a, b in v.items() if not a.startswith("p_top10")}
    return o


if __name__ == "__main__":
    df = data.fit_input(); freeze.check("prior-grid.json", "sens_metrics.py", "strata.json")
    t2 = xr.open_datatree(W2 / "seed12345.nc"); names = [str(x) for x in t2["posterior"].to_dataset()["model"].values]
    masks = strata_masks(names); d12 = fitmod.load_eci(W2 / "seed12345.nc")[0]
    cap = t2["posterior"].to_dataset()["capability"].mean(("chain", "draw")).to_numpy(); s0 = float(cap.std())
    cal = json.loads((W3 / "calibration.json").read_text()) if (W3 / "calibration.json").exists() else {}
    s2_shift = 0.25; g1 = cal.get("G1", {})
    pcs = cal.get("positive_control", {})
    if pcs and not all(v["fails_S1_S4_in_frontier_or_all"] for v in pcs.values()): s2_shift = 0.15
    R = dict(s2_shift=s2_shift, s0_raw_capability_sd=s0, P8_guard_triggered=bool(s0 > 3), G1=g1)
    # ---- 1. S5 screen
    log("S5 screen"); s5, hyp, rw = s5_screen(names, masks)
    R["S5"] = s5; R["S5_hyper_psens"] = hyp; R["S5_reweighted"] = rw
    flagged_h = [h for h in HYPER if s5["lp_" + h]["flagged_strata"]]
    R["S5_joint_flagged_strata"] = s5["lp_joint"]["flagged_strata"]; R["flagged_hyperpriors"] = flagged_h
    (OUT / "s5_screen.json").write_text(json.dumps(R, indent=1, default=str))
    # ---- 2. P0, P0b
    draws = 4000
    def p0pair(draws):
        a, d0 = entry_fit("P0", df, names, 12345, draws, epoch_priors=None)
        b, db = entry_fit("P0b", df, names, 22345, draws, epoch_priors=None)
        return a, d0, b, db
    a0, d0, b0, db = p0pair(draws); nf = noise_floor(d0, db, names); R["noise_floor"] = dict(draws_per_chain=draws, **nf)
    if not nf["passes"]:
        log("noise floor failed; doubling draws for all W5 fits (once)")
        draws = 8000
        for nm in ("P0", "P0b"):
            for ext in (".json", ".npz"): (OUT / f"{nm}{ext}").unlink(missing_ok=True)
        a0, d0, b0, db = p0pair(draws); nf2 = noise_floor(d0, db, names); R["noise_floor_after_doubling"] = dict(draws_per_chain=draws, **nf2)
    R["P0"] = dict(converged=a0["converged"]); R["P0b"] = dict(converged=b0["converged"])
    # S5 on P0's draws is a Monte Carlo check only (reported, not decisive): skipped unless P0's trace is kept; documented in summary.
    # ---- 3. grid
    ent = build_entries(s0); scores = {}; fits = {}
    for k in list(GRID["defensible"]) + list(GRID["stress_reported_not_scored"]):
        side, dk = entry_fit(k, df, names, 12345, draws, **ent[k])
        if not side["resolved"]:   # G2 add_evidence: one more attempt, non-centred (P9) or target_accept 0.99
            kw2 = dict(ent[k]); 
            if k == "P9": kw2["noncentred"] = True
            else: kw2["target_accept"] = 0.99
            side2, dk2 = entry_fit(k + "_retry3", df, names, 12345, draws, **kw2)
            side["third_attempt"] = dict(converged=side2["converged"], kw={a: b for a, b in kw2.items() if a != "s0"})
            if side2["converged"]: side, dk = dict(side, resolved=True, resolved_by="third_attempt"), dk2
        fits[k] = side; scores[k] = short(sm.score(dk, d0, names, masks, s2_shift)) | dict(resolved=side["resolved"], converged=side["converged"]) if side["resolved"] else dict(resolved=False)
        log(k, "resolved", side["resolved"])
    R["entries"] = {k: dict(resolved=fits[k]["resolved"], scores=scores[k]) for k in scores}
    # ---- 4. PR (exploratory), after EQ and W1
    eq_ok = json.loads((W2 / "reproduction.json").read_text())["EQ"]["passed"]
    pr_ok = json.loads(Path("runs/W/W1/prior_predictive.json").read_text())["PR_passes"]
    R["PR"] = dict(run=bool(eq_ok and pr_ok), EQ_passed=bool(eq_ok), W1_criterion_passed=bool(pr_ok))
    if eq_ok and pr_ok:
        spec = models.Spec(prior="reference")
        side, _ = fitmod.fit("PR", OUT, df, spec=spec, seed=12345, draws=draws, loglik=True)
        dpr = fitmod.load_eci(OUT / "PR.nc")[0]
        R["PR"].update(converged=side["converged"], scores=short(sm.score(dpr, d0, names, masks, s2_shift)), exploratory=True, nc="PR.nc")
    # ---- 5. S5 follow-ups (C1 rule) and targeted refits (exploratory)
    follow = {}
    for h in flagged_h:
        for a in (0.8, 1.25):
            pri = {h: powered(models.DEFAULT_PRIORS[h], a)}
            side, dk = entry_fit(f"S5F_{h}_{a}", df, names, 12345, draws, epoch_priors=pri)
            follow[f"{h}_{a}"] = dict(resolved=side["resolved"], scores=short(sm.score(dk, d0, names, masks, s2_shift)) if side["resolved"] else None)
    R["S5_followup_C1"] = follow
    targeted = {}
    for h in flagged_h:
        for a in (0.5, 2.0):
            pri = {h: powered(models.DEFAULT_PRIORS[h], a)}
            side, dk = entry_fit(f"S5T_{h}_{a}", df, names, 12345, draws, epoch_priors=pri)
            targeted[f"{h}_{a}"] = dict(resolved=side["resolved"], exploratory=True, scores=short(sm.score(dk, d0, names, masks, s2_shift)) if side["resolved"] else None)
    R["S5_targeted_exploratory"] = targeted
    # ---- 6. verdict (C1 rule)
    def stratum_pass(sc, s): return sc[s]["S1_pass"] and sc[s]["S2_pass"] and sc[s]["S3_pass"]
    fails = {}; unresolved = []
    for k in GRID["defensible"]:
        e = R["entries"][k]
        if not e["resolved"]: unresolved.append(k); continue
        sc = e["scores"]; f = [s for s in ("all", "frontier", "sparse") if not stratum_pass(sc, s)]
        if not sc["S4"]["pass_"]: f.append("S4")
        if f: fails[k] = f
    sensitive = [k for k, f in fails.items() if any(x in ("all", "frontier", "S4") for x in f)]
    sparse_only = [k for k, f in fails.items() if f == ["sparse"]]
    s5_pass = not R["S5_joint_flagged_strata"] and not flagged_h
    s5_follow_pass = True
    for key, v in follow.items():
        if not v["resolved"]: s5_follow_pass = False; continue
        sc = v["scores"]
        s5_follow_pass &= all(stratum_pass(sc, s) for s in ("all", "frontier", "sparse")) and sc["S4"]["pass_"]
    s5_ok = s5_pass or (follow and s5_follow_pass)
    dense_ok = all(R["entries"][k]["scores"]["dense"]["S1_pass"] and R["entries"][k]["scores"]["dense"]["S2_pass"] and R["entries"][k]["scores"]["dense"]["S3_pass"] for k in sparse_only) if sparse_only else True
    if sensitive: verdict = "Sensitive"
    elif unresolved: verdict = "Not established (unresolved: %s)" % ",".join(unresolved)
    elif not fails and s5_ok: verdict = "Robust"
    elif fails and len(sparse_only) == len(fails) and dense_ok: verdict = "Conditionally robust (narrow to the 184 models with 7 or more scores)"
    elif not fails and not s5_ok: verdict = "Sensitive (S5 follow-up refits fail)"
    else: verdict = "Sensitive"
    R["C1_verdict"] = dict(verdict=verdict, failures_by_prior=fails, unresolved=unresolved, sensitive_priors=sensitive, S5_passes=bool(s5_pass), S5_followup_passes=bool(s5_follow_pass) if follow else None,
                           s2_limit_in_use=s2_shift)
    (OUT / "sensitivity.json").write_text(json.dumps(R, indent=1, default=str))
    (OUT / "verdict_C1.json").write_text(json.dumps(R["C1_verdict"], indent=1))
    log("C1:", verdict, fails)
