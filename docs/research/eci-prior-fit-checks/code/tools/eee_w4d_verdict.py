"""Assemble runs/EEE/W4/verdict_C2.json for the EEE-data mirror with the rule of gate G3 (decision-gates.md) and M6,
from W4/ppc.json, W3/calibration.json, W4d/step1.json and W4d/deletion_test.json. Run from eci_work/v11 (real root).
The Epoch-data verdict file was assembled by hand with the same rule; this script applies it mechanically."""
import json, os
E = "runs/EEE"
p = json.load(open(f"{E}/W4/ppc.json")); c = json.load(open(f"{E}/W3/calibration.json"))
s1 = json.load(open(f"{E}/W4d/step1.json")) if os.path.exists(f"{E}/W4d/step1.json") else None
dl = json.load(open(f"{E}/W4d/deletion_test.json")) if os.path.exists(f"{E}/W4d/deletion_test.json") else None
rej = p["W4b"]["rejected"]; cov = p["W4c"]["overall_coverage"]; flagged = p["W4c"]["flagged_benchmarks"]
cov_ok = 0.85 <= cov <= 0.95
pw = c["power"]
def has_power(gen): return pw[gen]["n_converged"] >= 15 and pw[gen]["n_reject"] >= 16
power_ok = has_power("2d") or has_power("offset")
v = dict(stage="W4d", date="2026-11-21", component="C2", gate="G3", data="EEE substitution matrix (runs/EEE/input)",
         held_out_coverage=dict(overall=cov, in_rule=cov_ok, flagged_benchmarks=flagged), rejected_checks=rej,
         rejected_adjusted_p={t: p["W4b"]["maxT"][t]["p_adjusted"] for t in rej}, n_null=p["W4b"]["maxT"]["R"], T2_or_T5_power_ok=power_ok)
if not rej and cov_ok and not flagged:
    v["verdict"] = "adequate" if power_ok else "inconclusive"
    v["verdict_text"] = ("Under Epoch's model, no check rejects at 0.01 family-wise and held-out coverage is in range. " +
                         ("T2 or T5 had power in W3, so C2 is supported (Adequate)." if power_ok else "Neither T2 nor T5 had power in W3, so C2 is Inconclusive (lower_assurance) and stays exploratory."))
else:
    nF = s1["n_F"] if s1 else None
    v["F"] = s1["F"] if s1 else None; v["n_F"] = nF; v["F_limit"] = 10; v["F_exceeds_limit"] = bool(nF is not None and nF > 10)
    if s1: v["null_thresholds_99th_pct_of_per_replicate_max"] = s1["thresholds_99"]; v["extreme_components"] = s1.get("extreme_components")
    if dl:
        pr = dl["primary_all_converged_nulls"]
        v["deletion_test"] = dict(rows_kept=dl["sub_info"]["rows_kept"], rows_deleted=dl["sub_info"]["rows_deleted"], n_null_used=dl["n_null_used"],
                                  **{t: dict(statistic_observed=pr[t]["obs_full"], p_unadjusted_before=pr[t]["p_full"], statistic_after_deleting_F=pr[t]["obs_deleted"],
                                             p_unadjusted_after_deleting_F=pr[t]["p_unadjusted_deleted"], localised_to_F=bool(pr[t]["p_unadjusted_deleted"] >= 0.01)) for t in rej if t in pr})
    if nF is not None and nF > 10:
        v["verdict"] = "falsified"
        v["verdict_text"] = (f"Under Epoch's model, C2 is falsified per G3: {len(rej)} check(s) ({', '.join(rej)}) are rejected at max-T adjusted p = {min(v['rejected_adjusted_p'].values()) if rej else float('nan'):.4f}"
                             f" and the localisation set F has {nF} benchmarks (> 10), so the `reframe` branch (adequate with exceptions) is not available."
                             + ("" if power_ok else " 'Adequate' is impossible (T2 and T5 had no demonstrated power in W3).") + " The W4d refit without F was not run (rule applies only for |F| <= 10).")
        v["w4d_refit"] = dict(run=False, reason=f"|F| = {nF} > 10")
    elif nF is not None:
        v["verdict"] = "pending_refit"
        v["verdict_text"] = f"|F| = {nF} <= 10: the registered rule requires the W4d refit without F (shift of retained models against 0.25 W) before C2 can be read as adequate with exceptions or falsified."
    else:
        v["verdict"] = "pending_localisation"; v["verdict_text"] = "Rejections or flags present; localisation (W4d) not available."
json.dump(v, open(f"{E}/W4/verdict_C2.json", "w"), indent=1)
print(json.dumps({k: v[k] for k in ("verdict", "verdict_text", "rejected_checks", "n_F") if k in v}, indent=1))
