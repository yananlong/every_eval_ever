"""PROV per-refit runner (pattern of bsel_run_entry.py): one child per fit attempt, 2 h cap (process-group kill), attempts at 4,000 then 8,000 draws,
then a third at target_accept 0.99.  fit_any.run(df, 12345, draws=..., epoch_priors=None) = Epoch's unmodified fit_bayesian_eci.
Per refit: convergence ladder, comparison with P0 (Epoch-data fit) and with the deterministic EEE fit, inclusion-rule check, T1-T7 with max-T p against the
EEE-data and Epoch-data W3 model-true null sets.  Usage (v11 root): prov_run_entry.py ID   -> runs/EEE/PROV/fits/ID.json + ID.npz"""
import sys, os, json, time, signal, subprocess, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import prov_common as P
CAP = int(os.environ.get("PROV_CAP_S", 7200))
ap = argparse.ArgumentParser(); ap.add_argument("id"); ap.add_argument("--draws", type=int, default=P.DRAWS); ap.add_argument("--worker", type=int, default=-1); ap.add_argument("--ta", type=float, default=0.95)
A = ap.parse_args()
FITS = P.OUT / "fits"; ST = P.OUT / "_status"; FITS.mkdir(parents=True, exist_ok=True); ST.mkdir(parents=True, exist_ok=True)
log = lambda *a: print(time.strftime("%H:%M:%S"), A.id, *a, flush=True)


def nulls(path):
    out = []
    for f in Path(path).glob("rep/null_*.json"):
        x = json.loads(f.read_text())
        if x.get("converged"): out.append(x["T"])
    return out


def worker():
    import warnings; warnings.filterwarnings("ignore")
    import numpy as np
    from lib import data, fit as fitmod, fit_any, ppc_checks as ppc
    d = P.design(); fi = data.fit_input(); df = P.build_df(A.id, d, fi)
    assert len(df) == len(fi) == 2879 and (df[["model_id", "benchmark_id"]].values == fi[["model_id", "benchmark_id"]].values).all()
    kept = P.B.apply_inclusion(df); dropped = sorted(set(df.Model) - set(kept.Model))       # Epoch's loader rule; the fit itself does not re-apply it
    res, warns, wall = fit_any.run(df, P.FIT_SEED, draws=A.draws, epoch_priors=None, target_accept=A.ta)
    ok, last = fitmod.verdict(res["attempts"])
    names = list(res["model_names"]); eci = np.asarray(res["eci"], dtype="float64"); post = res["trace"].posterior
    cap = post["capability"].stack(s=("chain", "draw")).transpose("s", ...).to_numpy()
    lo, hi = names.index(P.ANCHORS[0]), names.index(P.ANCHORS[1])
    p0 = P.B.load_p0(); ee = P.load_ref(P.EEE_REF_NC, P.EEE_REF_NPZ)
    rows_full = fi.groupby("Model").size().to_dict()
    cmp0 = P.B.compare(eci, names, p0, rows_full, rows_full); cmpe = P.B.compare(eci, names, ee, rows_full, rows_full)
    anc = dict(refit=P.B.anchor_block(cap[:, lo], cap[:, hi]), p0=P.B.anchor_block(p0["cap_low"], p0["cap_high"]), eee=P.B.anchor_block(ee["cap_low"], ee["cap_high"]))
    # T1-T7 on this refit's data and posterior (thinned to 400 draws as in w4_ppc.py)
    scores = data.read_member(data.SCORES); el = ppc.Elig(df, scores)
    pooled = {v: post[v].stack(s=("chain", "draw")).transpose("s", ...).to_numpy() for v in ("capability", "difficulty", "slope", "sigma")}
    th = {k: ppc.thin(v) for k, v in pooled.items()}
    y = np.clip(df["performance"].to_numpy(dtype=float), ppc.EPS, 1 - ppc.EPS)
    rq = ppc.residual_quantities(th, el); Tobs, comp, mx = ppc.stats(y, rq, el)
    tt = {}
    for lab, path in (("eee_null", "runs/EEE/W3"), ("epoch_null", "runs/W/W3")):
        mt = ppc.max_t(Tobs, nulls(path)); tt[lab] = dict(R=mt["R"], **{k: dict(p_unadjusted=mt[k]["p_unadjusted"], p_adjusted=mt[k]["p_adjusted"]) for k in ppc.TNAMES})
    keep = np.linspace(0, eci.shape[0] - 1, 4000).astype(int)
    np.savez_compressed(ST / f"{A.id}.att{A.worker}.npz", eci=eci[keep].astype("float32"), names=np.array(names), mean=eci.mean(0), q05=np.quantile(eci, 0.05, axis=0), q95=np.quantile(eci, 0.95, axis=0),
                        bench_names=np.array([str(x) for x in post["benchmark"].values]), diff_mean=pooled["difficulty"].mean(0), slope_mean=pooled["slope"].mean(0),
                        sigma_mean=pooled["sigma"].mean(0), diff_sd=pooled["difficulty"].std(0))
    r = dict(draws=A.draws, target_accept=A.ta, converged=bool(ok), last_attempt=last, started_from=res["started_from"], wall=round(wall, 1), warnings=warns[:3], ladder=res["attempts"],
             n_draws_total=int(eci.shape[0]), n_models=len(names), n_rows=int(len(df)), models_failing_inclusion_rule=dropped, anchors=anc, compare=cmp0, compare_eee=cmpe,
             T=dict(observed=Tobs, p=tt, eligibility=el.summary()))
    (ST / f"{A.id}.att{A.worker}.json").write_text(json.dumps(r, indent=1, default=str))


def run_child(cmd):
    t0 = time.time(); p = subprocess.Popen(cmd, start_new_session=True)
    try: return p.wait(timeout=CAP), time.time() - t0, False
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL); p.wait(); return -9, time.time() - t0, True


def attempt(k, draws, ta=0.95):
    rc, wall, to = run_child([sys.executable, "-W", "ignore", __file__, A.id, "--draws", str(draws), "--worker", str(k), "--ta", str(ta)])
    f = ST / f"{A.id}.att{k}.json"
    if to: return dict(k=k, draws=draws, target_accept=ta, timeout=True, wall=round(wall, 1), converged=False)
    if rc != 0 or not f.exists(): return dict(k=k, draws=draws, target_accept=ta, crashed=True, rc=rc, wall=round(wall, 1), converged=False)
    return dict(json.loads(f.read_text()), k=k, child_wall=round(wall, 1))


def orchestrate():
    out = FITS / f"{A.id}.json"
    if out.exists() and json.loads(out.read_text()).get("finished"): log("already done"); return
    final = dict(id=A.id, variant=A.id[0], seed=P.FIT_SEED, cap_s=CAP, started=time.strftime("%FT%TZ", time.gmtime()))
    attempts, resolved, timed_out = [], False, False
    for k, dr, ta in [(0, A.draws, 0.95), (1, 2 * A.draws, 0.95)]:
        log("attempt", k, "draws", dr); a = attempt(k, dr, ta); attempts.append(a)
        if a.get("timeout"): timed_out = True; break
        if a.get("converged"): resolved = True; break
    if not resolved and not timed_out:
        log("third attempt target_accept 0.99"); a = attempt(2, A.draws, 0.99); attempts.append(a); resolved, timed_out = bool(a.get("converged")), bool(a.get("timeout"))
    used = next((a for a in reversed(attempts) if "compare" in a), None)
    final.update(attempts=[{k: v for k, v in a.items() if k not in ("compare", "compare_eee", "anchors", "T")} for a in attempts], resolved=resolved, converged=resolved, timeout=timed_out,
                 used_attempt=None if used is None else used["k"], finished=True)
    if used is not None:
        final.update({k: used[k] for k in ("compare", "compare_eee", "anchors", "T", "n_models", "n_rows", "models_failing_inclusion_rule")})
        os.replace(ST / f"{A.id}.att{used['k']}.npz", FITS / f"{A.id}.npz")
    for p in ST.glob(f"{A.id}.att*.npz"): p.unlink()
    tmp = FITS / f".{A.id}.json.tmp"; tmp.write_text(json.dumps(final, indent=1, default=str)); os.replace(tmp, out)
    log("done resolved", resolved, "timeout", timed_out)


if __name__ == "__main__":
    worker() if A.worker >= 0 else orchestrate()
