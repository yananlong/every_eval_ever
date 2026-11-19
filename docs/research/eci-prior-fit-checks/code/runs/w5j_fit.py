"""W5-J1 / W5-J2 (exploratory): fit a normalised capability-only Jeffreys prior on the real data at the W5 settings of the PR entry
(Epoch's fit_bayesian_eci with our builder swapped in, seed 12345, 4,000 draws per chain, 4 chains, target_accept 0.95; posterior and
log-likelihood saved). Output: runs/W/W5J/<variant>/<variant>.nc and .json. Score with w5j_score.py. Run from the v11 root.
  w5j_fit.py --variant J1|J2 [--draws 4000] [--seed 12345]
  w5j_fit.py --variant J1 --smoke      # one chain, one core, a few draws, no Epoch routine (for checking the wiring only)"""
import sys, json, time, argparse, warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
warnings.filterwarnings("ignore")
from lib import data, fit as fitmod, models, jeffreys_norm as N

ap = argparse.ArgumentParser()
ap.add_argument("--variant", required=True, choices=["J1", "J2"])
ap.add_argument("--draws", type=int, default=4000)
ap.add_argument("--seed", type=int, default=12345)
ap.add_argument("--smoke", action="store_true")
A = ap.parse_args()
LIB = Path(__file__).resolve().parent / "lib"
log = lambda *a: print(time.strftime("%H:%M:%S"), *a, flush=True)


def main():
    df = data.fit_input()
    if A.smoke:
        import pymc as pm, numpy as np
        m = N.build_jn(df, A.variant); t0 = time.time()
        with m:
            tr = pm.sample(draws=10, tune=20, chains=1, cores=1, random_seed=A.seed, progressbar=False, compute_convergence_checks=False)
            pm.compute_log_likelihood(tr, extend_inferencedata=True, progressbar=False)
        post = tr["posterior"].to_dataset()
        log("smoke ok", A.variant, "seconds", round(time.time() - t0, 1), "log_likelihood vars", list(tr["log_likelihood"].data_vars),
            "max slope", float(post["slope"].max()), "tau_alpha", float(post["tau_alpha"].mean()))
        return
    out = Path("runs/W/W5J") / A.variant
    with N.epoch_with_jn(A.variant):
        side, _ = fitmod.fit(A.variant, out, df, spec=models.Spec(), seed=A.seed, draws=A.draws, loglik=True, extra_code=(LIB / "jeffreys.py", LIB / "jeffreys_norm.py"))
    log(A.variant, "converged", side["converged"], side["last_attempt"], "wall", side["wall_seconds"])


if __name__ == "__main__":
    main()
