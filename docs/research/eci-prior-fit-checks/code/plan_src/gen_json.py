"""Write claim-map.json, run-blocks.json and prior-grid.json for the ECI sensitivity/PPC plan.

Usage (from the v11/ directory):  python3 plan_src/gen_json.py [OUT_DIR]
OUT_DIR defaults to the experiment-plan/ directory next to plan_src/.

"M1" ... "M10" refer to the numbered parts of the "Methods Specification" section of
experiment-plan.md. Thresholds are defined once here (constants below) and repeated in the
Markdown files by hand; if you change one, change the Markdown and add a Revision log entry.
"""
import json
import sys
from pathlib import Path

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "experiment-plan"
EXT = "ext"  # relative to v11/

# ---- Frozen constants (also quoted in the Markdown files) --------------------------------------
N_OBS, N_MODELS, N_BENCH = 2879, 256, 57
N_SPARSE, N_DENSE, N_FRONTIER = 72, 184, 20      # <=6 scores, >=7 scores, top 20 by published eci
R_NULL = 199                                     # G-null replicates
R_MISFIT = 20                                    # replicates per misfit generator
ALPHA_FW = 0.01                                  # family-wise level for T1-T7
B2_DRAWS = 4000                                  # fixed draws per chain for every B2 fit
RNG_SEED = 20261113                              # seed for folds, audit sample, bootstrap
ZIP_SHA = "9d728f9f8635069812530a157aef7a6cec935fffc93f33d3031bad5c6888b1d5"
EEE_SHA = "98e5f48af77952d478013cf578ca00ecd17e5e41f7a647bbc80e8e37b2b120fe"
FIT_INPUT = "epoch_capabilities_index/processed_data_for_eci.csv"

ZIP = {"path": f"{EXT}/epoch_zip/benchmark_data.zip",
       "role": (f"Epoch data release retrieved 2026-11-13, sha256 {ZIP_SHA}. Members used: {FIT_INPUT} (the fit input), "
                "epoch_capabilities_index/eci_scores.csv, edi_scores.csv and eci_bootstraps.json (published results), "
                "benchmark_metadata.csv, model_metadata.csv"),
       "snapshot": "digest-at-start"}
ECI_CODE = {"path": f"{EXT}/eci-public", "role": "Epoch's code at git e04929ab751531e558b1a61e86f436487c710ef8 (read-only; installed from the copy runs/vendor/eci-public)",
            "snapshot": "digest-at-start"}
EEE_MAN = {"path": f"{EXT}/eee/entries.jsonl", "role": f"EEE manifest dd7efcff (2026-11-13), 122,861 aggregate records, sha256 {EEE_SHA}",
           "snapshot": "digest-at-start"}
PRIOR_GRID = {"path": "experiment-plan/prior-grid.json", "role": "frozen before any B1 positive-control fit, B2 refit or screen", "snapshot": "digest-at-start"}
CHECKS = {"path": "runs/lib/ppc_checks.py", "role": "T1-T7 and the max-T calibration; frozen before any B1 generator runs", "snapshot": "digest-at-start"}
SENS = {"path": "runs/lib/sens_metrics.py", "role": "S1-S5 on the anchored scale; frozen before the B1 positive-control fit", "snapshot": "digest-at-start"}
B0_NC = "runs/B0/seed12345.nc"

STRATA = (f"Strata (M2), fixed from the published files before any fit: all ({N_MODELS} models; 254 non-anchor models for S2, S3, S5); "
          f"frontier (the {N_FRONTIER} models with the highest published eci in eci_scores.csv, Claude Fable 5.2 down to GPT-5.5); "
          f"sparse (the {N_SPARSE} models with 6 or fewer rows in the fit input). Dense (the {N_DENSE} models with 7 or more rows, "
          "182 non-anchor) is reported and is used only to state the narrowed claim.")

claims = [
    {
        "claim_id": "C1",
        "priority": "primary",
        "claim": ("The published Bayesian ECI (code e04929a, data of 2026-11-13) is robust to its priors: under every prior "
                  "in a pre-registered set of defensible alternatives, model scores, the frontier ranking and the 90% "
                  "credible intervals move by less than would change any conclusion Epoch reports."),
        "why_it_matters": ("The repository switched ECI to a Bayesian fit (merge commit e04929a, 2026-11-03) and Epoch reports 90% "
                           "credible intervals, but publishes no prior sensitivity. Capabilities and difficulties have flat "
                           "Uniform(-50, 50) priors, and 72 of 256 models have 6 or fewer scores. The newest frontier models, "
                           "which carry the headline numbers, have few benchmarks still in the mid-range, so the priors on "
                           "slopes and noise could matter most where readers look."),
        "minimum_convincing_evidence": ("B0 reproduces the published scores and intervals; B1 shows the sensitivity metrics "
                                        "flag a deliberately strong prior; B2 scores every defensible prior against the C1 "
                                        "decision rule, with a seed-to-seed noise floor measured for every metric."),
        "anti_claim": ("Apparent robustness is an artefact of perturbations too small to matter, or of metrics that "
                       "average over the many dense models and hide shifts at the frontier and in sparse models."),
        "falsifier": ("Any defensible prior P1-P10 in prior-grid.json for which, in the all-models or frontier stratum, "
                      "S1 Spearman(ECI_k, ECI_0) < 0.99, or S2 more than 5% of non-anchor models shift by more than a quarter "
                      "of their baseline 90% interval width, or S3 more than 5% have an interval-width ratio outside "
                      "[0.8, 1.25], or S4 the top-10 set changes or a top-10 adjacent pair's P(i ranked above j) moves by "
                      "0.10 or more. Definitions in M1-M3."),
        "decision_if_unproven": {
            "action": "narrow",
            "note": ("If every failure is in the sparse stratum only, restate C1 as robust for the 184 models with 7 or more "
                     "scores (requires S1-S3 to pass in the dense stratum) and list the sparse models as prior-dependent. If "
                     "the frontier or all-models stratum fails, C1 is false as stated: report which prior drives it. "
                     "add_evidence does not apply to a failed rule because the data are fixed; it applies only to an "
                     "unresolved grid entry (one more attempt) and to an S5-only flag (two exact power-scaled refits)."),
        },
        "linked_blocks": ["B0", "B1", "B2", "B6"],
        "current_evidence_class": "exploratory",
        "evidence_class": "confirmatory",
        "decision_rule": ("Quantities (M1): per-draw anchored ECI; point estimate = posterior mean; W = 95th minus 5th "
                          "percentile. Baseline = fit P0 (default priors, B2 sampler settings, seed 12345). " + STRATA + " "
                          "For each defensible prior k in P1-P10 and each stratum: S1 Spearman(ECI_k, ECI_0) >= 0.99 over "
                          "the stratum's models; S2 share of non-anchor models with abs(ECI_k - ECI_0) > 0.25 x W_0 is <= 5% "
                          "(at most 12 of 254, 1 of 20, 3 of 72); S3 share with W_k / W_0 outside [0.8, 1.25] is <= 5% (same "
                          "counts); S4 (scored once, counted in the frontier and all-models strata) the set of the 10 highest "
                          "posterior-mean ECI is unchanged and abs(P_k(i>j) - P_0(i>j)) < 0.10 for each of the 9 adjacent "
                          "pairs of the baseline top-10 order. S5 (screen on P0's draws, no refit): power-scaling sensitivity "
                          "psens of the three hyperpriors <= 0.05 for at least 95% of non-anchor models' ECI in each stratum. "
                          "Verdicts. Robust: all ten priors resolved, S1-S4 pass in all three strata, S5 passes. Conditionally "
                          "robust: every S1-S3 failure is in the sparse stratum only and S4 passes. Sensitive: any S1-S4 "
                          "failure in the all-models or frontier stratum. An S5-only flag does not decide the verdict: the "
                          "two exact power-scaled refits of the flagged hyperprior (alpha 0.8 and 1.25, M3) are scored with "
                          "S1-S4 as extra grid entries and they decide. An entry still unresolved after its retry means C1 "
                          "cannot be Robust and is reported as not established for that prior."),
        "loss_contract": ("Every grid entry is reported, including the stress priors X1 and X2 (reported, not scored), fits "
                          "that fail convergence (counted as unresolved, never dropped), and the two anchor models (kept in "
                          "S1 and S4, excluded from S2, S3 and S5 because their values are fixed by definition). The "
                          "seed-to-seed noise floor of every metric (P0 against P0b) is reported next to each result."),
        "falsification_test": "B2 refit grid scored against the decision rule; see falsifier.",
        "selection_history": [
            ("Before writing this plan we inspected: Epoch's code and README, the 2026-11-13 zip's benchmark list, "
             "per-model observation counts, published ECI and interval widths, and EEE collection names. No refit was run. "
             "The prior grid is written from the README's stated priors and the observation-count distribution."),
            ("Review of 2026-11-13 (before any run): the reviewer read the published file eci_bootstraps.json (500 posterior "
             "draws per model and benchmark) to check that thresholds are attainable. Facts used: published means differ "
             "from the 500-draw means by up to 0.88 ECI points (0.053 x W), which sets the Monte Carlo tolerance in G0; "
             "published adjacent-pair probabilities in the top 10 range from 0.52 to 0.996; raw capability draws stay within "
             "abs 12.6, far from the +/-50 bounds; the across-model SD of raw capability means is 2.62. No prior in the grid "
             "was added, removed or re-centred using these numbers."),
        ],
        "predecessor_failures": [
            ("Our own v1 composite model: full NUTS did not converge on the 45k-observation fitting set and we fell "
             "back to SVI. Carry forward: ECI's 2,879 observations are 15x fewer and Epoch's sampler uses a dense "
             "mass matrix, but B0 must confirm convergence before any sensitivity number is trusted."),
        ],
    },
    {
        "claim_id": "C2",
        "priority": "primary",
        "claim": ("The ECI's Beta-IRT model is adequate for Epoch's data: checks with simulation-calibrated "
                  "p-values find no structural misfit (dimensionality, item-curve shape, dispersion, time drift or "
                  "developer-specific effects) large enough to bias ECI scores, and held-out 90% predictive intervals "
                  "cover at their nominal rate."),
        "why_it_matters": ("Epoch's repo ships a diagnostic suite (per-benchmark and pooled posterior predictive p-values for "
                           "nine marginal statistics, in-sample and PSIS-LOO PIT calibration and coverage, PSIS-LOO), but the "
                           "ECI page publishes no results from it, and marginal score statistics have little power against "
                           "the misfits that matter for a one-dimensional index: a second skill dimension, "
                           "benchmark-specific contamination, or developer-specific over-performance."),
        "minimum_convincing_evidence": ("Epoch's own suite run and reported (B3a); the structural checks T1-T7 referred to "
                                        f"{R_NULL} null simulations with refits and shown in B1 to detect planted misfit (B3b); "
                                        "5-fold held-out coverage (B3c)."),
        "anti_claim": ("A clean result reflects checks with no power (posterior predictive p-values are conservative "
                       "because the data are used twice), not an adequate model."),
        "falsifier": ("The Inadequate verdict of the decision rule: a check with max-T adjusted p < 0.01, or overall held-out "
                      "90% coverage outside [0.85, 0.95], or a benchmark with 20 or more held-out scores whose coverage "
                      "fails the Bonferroni binomial test, where the failure is not localised to at most 10 benchmarks or "
                      "removing those benchmarks (B3d) moves a model by more than 0.25 x W_0."),
        "decision_if_unproven": {
            "action": "reframe",
            "note": ("Report the misfit as a finding: which check fails, on which benchmarks or developers, and the "
                     "size of the ECI shift when the offending benchmarks are dropped (B3d). The claim becomes "
                     "'ECI is adequate except for X, which moves scores by Y'."),
        },
        "linked_blocks": ["B0", "B1", "B3"],
        "current_evidence_class": "exploratory",
        "evidence_class": "confirmatory",
        "decision_rule": ("T1-T7 (M5) are scalar discrepancy statistics, larger meaning worse fit, computed the same way on "
                          f"the real data with the B0 fit and on each of R = {R_NULL} G-null datasets with its own refit. "
                          "Unadjusted p_k = (1 + number of converged null replicates with T_k >= observed T_k) / (R' + 1). "
                          "Family-wise adjusted p_k by single-step max-T over the seven checks on standardised log statistics "
                          f"(M6). A check is rejected if adjusted p_k < {ALPHA_FW}; with R' = 199 the smallest attainable "
                          "value is 0.005. Held-out coverage (M7): the share of the 2,704 held-out scores whose PIT lies in "
                          "[0.05, 0.95] must be in [0.85, 0.95]; each of the 44 benchmarks with 20 or more held-out scores "
                          "is flagged if an exact two-sided binomial test of coverage = 0.90 gives p < 0.01 / 44. "
                          "Adequate: no check rejected, overall coverage in range, no benchmark flagged; the statement is "
                          "limited to misfit types whose targeted check reached power >= 0.8 in B1, and the others are listed "
                          "as not assessed. Adequate with exceptions: every rejection or flag is localised (M6) to a benchmark "
                          "set F with at most 10 members, and the B3d refit without F moves no retained non-anchor model by "
                          "more than 0.25 x W_0 and drops no frontier model. Inadequate: any other rejection or coverage "
                          "failure. Inconclusive: nothing rejected, but neither T2 (on G-2D) nor T5 (on G-offset) reached "
                          "power 0.8; C2 then stays exploratory."),
        "loss_contract": ("All seven checks are reported with unadjusted, adjusted and raw in-sample posterior predictive "
                          "p-values; no check is dropped after seeing results. Non-converged null replicates are excluded "
                          "from the reference set and counted. Scores at 0 or 1 are clipped to [0.001, 0.999] exactly as the "
                          "likelihood sees them; Epoch's min and max statistics are excluded as Epoch excludes them."),
        "falsification_test": "B3 checks and held-out coverage against the decision rule; see falsifier.",
        "selection_history": [
            "No posterior or residual was inspected before the check list T1-T7 was written.",
            ("Review of 2026-11-13 (before any run): the scalar statistics, the max-T adjustment, the binomial coverage rule "
             "and three extra misfit generators were fixed from the observation pattern only (benchmark sizes, shared-model "
             "counts, organisation counts). No residual was computed."),
        ],
        "predecessor_failures": [
            ("Our v1 composite model failed its local-dependence kill test (Q3) on EEE data. Not inherited by ECI, "
             "but it is why T2 (residual correlation) is in the check list and why its threshold is pre-registered."),
        ],
    },
    {
        "claim_id": "C3",
        "priority": "supporting",
        "claim": ("ECI's posterior predictive intervals transfer to independently sourced scores: for model x benchmark "
                  "pairs that EEE holds from a different source than Epoch, the ECI 90% predictive interval covers the "
                  "EEE score at close to the nominal rate once EEE's own between-source spread is accounted for."),
        "why_it_matters": ("The ECI intervals describe Epoch's own scores. Readers use them as statements about a "
                           "model's capability, which only holds if they also predict scores obtained elsewhere. EEE "
                           "is the one place where independent re-runs of the same benchmarks sit in a common schema."),
        "minimum_convincing_evidence": ("An audited crosswalk (B4a) with a same-upstream positive control that matches "
                                        "near-exactly; coverage on independent pairs with a bootstrap interval; and the "
                                        "EEE-vs-EEE agreement rate on the same benchmarks as the noise floor."),
        "anti_claim": ("Low coverage is caused by crosswalk errors (wrong model or benchmark version) or by differences "
                       "in evaluation setup that any single-source index would suffer, not by ECI."),
        "falsifier": ("Coverage of the 90% predictive interval on independent pairs below 0.65 while the EEE-vs-EEE "
                      "agreement rate on the same benchmarks is estimable and at least 0.80, with the audit and "
                      "same-upstream preconditions met."),
        "decision_if_unproven": {
            "action": "sharpen_comparator",
            "note": ("If coverage is low but EEE-vs-EEE agreement is equally low, the comparison cannot separate ECI "
                     "from evaluation-setup variance: restrict to pairs whose EEE source matches Epoch's evaluation "
                     "settings and report the result as `harness-limited`."),
        },
        "linked_blocks": ["B4", "B5"],
        "current_evidence_class": "exploratory",
        "evidence_class": "exploratory",
        "decision_rule": ("Coverage = share of matched independent pairs (M9) whose normalised EEE score has PIT in "
                          "[0.05, 0.95] under the ECI predictive distribution (M8; PSIS-LOO weighted when Epoch's own score "
                          "for the pair is in the fit). Agreement = share of independent source pairs for the same model "
                          "and benchmark whose normalised scores differ by at most sqrt(2) x half the width of the ECI 90% "
                          "predictive interval (nominal 0.90 if both were draws from the ECI predictive). Preconditions: "
                          "audit finds at most 2 errors in 50 pairs; same-upstream median absolute difference <= 0.02; at "
                          "least 100 independent pairs over at least 20 model groups and 5 benchmarks, else C3 is 'not "
                          "assessed'. Verdicts: if agreement is estimable (30 or more source pairs) and below 0.80, the "
                          "verdict is `harness-limited` whatever the coverage. Otherwise transfers if coverage >= 0.80; "
                          "partial if 0.65 <= coverage < 0.80; does not transfer if coverage < 0.65. 'Does not transfer' "
                          "falsifies C3 only when agreement is estimable and >= 0.80; if agreement is not estimable the "
                          "result is reported as 'low coverage, noise floor unknown'. Verdicts use the point estimate; the "
                          "90% cluster-bootstrap interval is reported beside it."),
        "loss_contract": ("Every candidate EEE result is kept in the accounting with one class: matched-independent, "
                          "matched-same-upstream, upstream-unknown, ambiguous-model, model-unmapped, model-not-in-fit, "
                          "benchmark-not-in-fit, version-mismatch, metric-mismatch, duplicate. Classes are decided from "
                          "metadata before any ECI prediction is computed."),
        "falsification_test": "B4b coverage against the decision rule; see falsifier.",
        "selection_history": [
            ("We looked at EEE collection names and source_metadata for 12 sampled records to judge independence "
             "(Arcadia inspect_ai, Writer wasp, UK AISI and Scale SEAL run their own evaluations; ARC Prize, "
             "Terminal-Bench and Mercor APEX are the same upstream Epoch cites). No scores were compared."),
            ("Review of 2026-11-13: llm-stats 'first_party' records relay developer-reported scores, so they are "
             "same-upstream wherever Epoch's source for that row is the developer's own report; the earlier note "
             "called them independent without that condition. The class is now decided per pair by the rule in M9."),
        ],
        "predecessor_failures": [
            ("Our v1 composite model reached only 0.70 coverage on its cross-source mask against a 0.85-0.95 target. "
             "C3 tests whether ECI shares that failure; the same EEE source offsets are the main suspect for both."),
        ],
    },
]

blocks = [
    {
        "block_id": "B0", "paper_role": "appendix", "claim_ids": ["C1", "C2"], "decision_gate_id": "G0",
        "anti_claims_ruled_out": ["Sensitivity or misfit results describe a different fit from the published one."],
        "why_this_block_exists": ("Every later number is a difference from this baseline fit. If we cannot reproduce "
                                  "Epoch's published scores with their code and data, later differences are uninterpretable."),
        "dataset_split_task": (f"Fit input: {FIT_INPUT} inside the zip ({N_BENCH} benchmarks, {N_MODELS} models, {N_OBS} "
                               "rows, one per model x benchmark). Reference: eci_scores.csv (posterior mean and 5th/95th "
                               "percentiles per model), edi_scores.csv (edi and estimated_slope_scaled per benchmark; no "
                               "sigma and no intervals are published) and eci_bootstraps.json (500 published posterior draws). "
                               "B0b: the same fit on prepare_benchmark_data(zip), which returns the same 2,879 keys but three "
                               "different GPQA diamond scores (Claude Fable 5: 0.957 vs 0.845; Claude Opus 5.5: 0.959 vs "
                               "0.911; Claude Fable 5.2: 0.986 vs 0.957) because it selects the '-fallback_max' versions."),
        "systems_compared": ["B0a: fit_bayesian_eci(processed_data_for_eci.csv) with defaults, seeds 12345, 22345, 32345",
                             "Published eci_scores.csv, edi_scores.csv, eci_bootstraps.json",
                             "B0b: fit_bayesian_eci(prepare_benchmark_data(zip)), seed 12345 (data-provenance check, reported, not gated)"],
        "fixed_factors": ["code e04929a", "default BayesianPriors", "performance_clip_eps=1e-3",
                          "anchors Claude 3.5 Sonnet=130, GPT-5=150", "4 chains, target_accept 0.95, adaptive draws"],
        "variable_factors": ["random_seed (3 seeds)", "fit input (B0b only)"],
        "metrics": ["per model d_m = ECI_ours - ECI_published and d_m / W_m,published (seed 12345)", "Spearman over the 256 models",
                    "interval-width ratio W_ours / W_published per non-anchor model",
                    "max abs difference of edi and of estimated_slope_scaled (reported)",
                    "divergences, max r_hat, min bulk ESS, min tail ESS, min BFMI, sampler stage and attempts (per seed)",
                    "seed-to-seed SD of posterior-mean ECI per model (Monte Carlo floor)",
                    "B0b: S1-S4 of the loader-input fit against B0a, and the three differing rows"],
        "setup_details": ("uv project runs/ with Epoch's code installed from runs/vendor/eci-public (a byte-identical copy of "
                          "ext/eci-public at e04929a), dependency versions taken from Epoch's uv.lock. Read the fit input from "
                          "the zip with zipfile. Call fit_bayesian_eci(df, evaluate=True, random_seed=s, progressbar=False) for "
                          "s in {12345, 22345, 32345}. evaluate=True adds the log_likelihood and posterior_predictive groups; "
                          "the log prior is not stored by Epoch's code, so compute the summed log density of the three "
                          "hyperpriors per draw (LogNormal log-pdf at the tau_alpha, sigma_median, tau_sigma draws) and store "
                          "it as group log_prior. Add the per-draw anchored ECI (M1) to the posterior group. Save each trace "
                          "with to_netcdf plus a sidecar JSON (M10). Comparison with the published files uses seed 12345."),
        "seeds": 3,
        "success_criterion": ("Seed 12345: for every non-anchor model abs(d_m) <= max(0.5, 0.07 x W_m,published); Spearman >= "
                              "0.999; the median interval-width ratio is in [0.95, 1.05] and at least 95% of the 254 ratios are "
                              "in [0.85, 1.15]. All three seeds: zero divergences, r_hat <= 1.01, bulk ESS >= 400 on Epoch's "
                              "seven parameter groups."),
        "minimum_effect_size": ("0.5 ECI points, or 0.07 of the model's published interval width where that is larger. Published "
                                "values are rounded to 0.01; the published 500-draw file already differs from the published "
                                "means by up to 0.88 points (0.053 x W) from Monte Carlo error alone."),
        "failure_interpretation": ("A larger gap means the published file came from different code, data or settings "
                                   "(for example production overrides); find the cause before B2/B3, or switch the baseline to "
                                   "our own fit and say so in every result."),
        "expected_output_artifact": "runs/B0/reproduction.json",
        "compute_budget": "4 fits with evaluate=True, about 5 minutes each on 4 CPUs: about 20 minutes wall-clock; under 2 GB RAM; about 0.8 GB disk.",
        "dependencies": [],
        "priority": "must-run",
        "current_evidence_class": "exploratory", "evidence_class": "exploratory",
        "selection_rule": "All models and benchmarks in the published fit input; no filtering of our own.",
        "non_vacuity_check": "The comparison can fail: the published file could come from production settings that differ from the public defaults, and the public loader already disagrees with the published fit input on three rows.",
        "complete_outcome_accounting": "Record each seed's sampler stage (pilot or cold), every attempt with its draws and diagnostics, warnings, and failed seeds.",
        "hidden_information_controls": "None needed: no held-out data.",
        "independence_requirements": ["Same agent; recomputation of a third party's result, so no independence claimed."],
        "independence_evidence": "Not applicable.",
        "operational_threat_model": "", "operational_harms": "",
        "predecessor_failures": ["v1 NUTS non-convergence (C1)."],
        "execution": {
            "mode": "command",
            "entrypoint": {"argv": ["uv", "run", "--project", "runs", "python", "runs/b0_reproduce.py"], "cwd": "."},
            "declared_inputs": [ZIP],
            "declared_evaluator_artifacts": [ECI_CODE],
            "required_outputs": [{"path": "runs/B0/reproduction.json", "kind": "metrics"},
                                 {"path": B0_NC, "kind": "posterior"}],
        },
        "lineage_policy": {"allowed_relations": ["baseline", "replication", "sensitivity", "technical_retry"]},
    },
    {
        "block_id": "B1", "paper_role": "appendix", "claim_ids": ["C1", "C2"], "decision_gate_id": "G1",
        "anti_claims_ruled_out": [
            "Robustness in B2 comes from metrics that cannot detect sensitivity (C1 anti-claim).",
            "Clean checks in B3 come from checks with no power (C2 anti-claim).",
        ],
        "why_this_block_exists": ("Prior predictive check, parameter recovery, the null reference distribution of every B3 "
                                  "check, and power against planted misfit, on simulated data where the truth is known."),
        "dataset_split_task": ("Simulated score tables on the exact (model, benchmark) pattern of the fit input (2,879 cells; "
                               "Epoch's inclusion rule is not re-applied to simulated data). Generators (M4): G-prior (parameters "
                               f"drawn from the prior; no fits); G-null ({R_NULL} replicates, each from one joint posterior draw "
                               "of the B0 seed-12345 fit); and five misfit generators that modify G-null, 20 replicates each: "
                               "G-2D (two capability dimensions with correlation 0.7, a random 28 of 57 benchmarks on the "
                               "second), G-offset (+0.5 logit for one developer on 3 benchmarks), G-shape (upper asymptote 0.85 "
                               "on a random 19 benchmarks), G-disp (constant-SD Gaussian noise instead of Beta), G-drift (+0.3 "
                               "logit per year between benchmark release and model release, capped at 3 years). Positive "
                               "control: the real data refitted with tau_alpha ~ LogNormal(ln 0.05, 0.1)."),
        "systems_compared": ["ECI default fit on each G-null replicate", "ECI default fit on each misfit replicate",
                             "real data with the positive-control slope prior against the B0 fits (seeds 12345, 22345, 32345)"],
        "fixed_factors": ["observation pattern of the real data", "code e04929a", "default priors for all simulation fits",
                          "check implementations in runs/lib/ppc_checks.py"],
        "variable_factors": ["generator", "replicate"],
        "metrics": ["prior predictive: share of about 100,000 simulated scores at the clip bounds and share in [0.1, 0.9] (reported, not gated; a direct calculation from the priors gives about 0.89 and 0.05)",
                    "recovery: share of (replicate, non-anchor model) with the true anchored ECI inside the 90% interval, overall and by stratum",
                    f"null reference values of T1-T7 from the converged G-null replicates (target {R_NULL})",
                    "power: share of converged misfit replicates whose targeted check has max-T adjusted p < 0.01 (T1 on G-shape, T2 on G-2D, T3 on G-disp, T4 on G-drift, T5 on G-offset)",
                    "S1-S4 of the positive-control prior against the default fit, per seed",
                    "count of non-converged replicates per generator"],
        "setup_details": ("Order: (1) freeze prior-grid.json, sens_metrics.py and ppc_checks.py (digests in runs/freeze.json); (2) "
                          "positive-control refits; (3) G-prior; (4) G-null; (5) misfit generators. Replicate seed = first 4 "
                          "bytes of sha256('<generator>:<index>') as a big-endian integer (Python's built-in hash is salted and "
                          "must not be used). Each replicate: simulate (M4), fit with fit_bayesian_eci(df_r, random_seed=seed, "
                          "evaluate=False, progressbar=False), keep 400 evenly spaced draws, compute T1-T7 (M5) and, for G-null, "
                          "the recovery indicator; write one JSON and one thinned .nc per replicate (M10). True parameters go "
                          "to runs/B1/truth/, which ppc_checks.py never reads."),
        "seeds": 3,
        "success_criterion": ("Recovery coverage over all non-anchor models in [0.85, 0.95]; at least 150 converged G-null "
                              "replicates; T2 power >= 0.8 on G-2D and T5 power >= 0.8 on G-offset (at least 16 of 20 converged "
                              "replicates); the positive-control prior fails at least one of S1-S4 in the frontier or all-models "
                              "stratum on all three seeds."),
        "minimum_effect_size": "power >= 0.8 at family-wise alpha 0.01 for the targeted check; with 20 replicates, 16 of 20 has a 90% Clopper-Pearson interval of about 0.60 to 0.93, so power is reported with its interval.",
        "failure_interpretation": ("Low recovery coverage means the published intervals are miscalibrated even when the "
                                   "model is true; low power means a B3 pass for that check is uninformative and is "
                                   "reported as 'no power'; a positive-control prior that passes S1-S4 means C1's rule is too lax."),
        "expected_output_artifact": "runs/B1/calibration.json",
        "compute_budget": (f"{R_NULL} + 100 simulation fits + 3 positive-control fits = 302 fits. At Epoch's quoted 2 minutes per "
                           "fit (4 chains on 4 cores) that is about 10 hours wall-clock (about 40 CPU-hours); restartable per "
                           "replicate. Under 2 GB RAM. About 0.5 GB disk for thinned draws."),
        "dependencies": ["B0"],
        "priority": "must-run",
        "current_evidence_class": "exploratory", "evidence_class": "exploratory",
        "selection_rule": "Planted effect sizes, generator definitions and the seed rule are fixed in M4 before any simulation; the developer and benchmarks receiving an effect are drawn from the replicate's seeded generator.",
        "non_vacuity_check": "The planted misfits are ones the checks can miss, and the positive-control prior is one C1's rule could pass; both outcomes have a stated consequence in G1.",
        "complete_outcome_accounting": "Every replicate is kept with its convergence status; non-converged fits are excluded from the null reference and from power, with counts per generator.",
        "hidden_information_controls": "Check code is frozen before generators are run; true parameters are written only to runs/B1/truth/, which the check code does not read.",
        "independence_requirements": ["Simulation and analysis by the same agent; no independence claimed."],
        "independence_evidence": "Not applicable.",
        "operational_threat_model": "", "operational_harms": "",
        "predecessor_failures": [],
        "execution": {
            "mode": "command",
            "entrypoint": {"argv": ["uv", "run", "--project", "runs", "python", "runs/b1_simulate.py"], "cwd": "."},
            "declared_inputs": [ZIP, {"path": B0_NC, "role": "B0 posterior: parameter draws for the generators", "snapshot": "digest-at-start"}],
            "declared_evaluator_artifacts": [ECI_CODE, CHECKS, SENS, PRIOR_GRID],
            "required_outputs": [{"path": "runs/B1/calibration.json", "kind": "metrics"}],
        },
        "lineage_policy": {"allowed_relations": ["baseline", "negative_control", "sensitivity", "technical_retry"]},
    },
    {
        "block_id": "B2", "paper_role": "main", "claim_ids": ["C1"], "decision_gate_id": "G2",
        "anti_claims_ruled_out": ["Robustness hidden by pooling over dense models (C1 anti-claim)."],
        "why_this_block_exists": "The prior sensitivity analysis Epoch did not publish; tests C1 directly.",
        "dataset_split_task": "Same fit input as B0a (processed_data_for_eci.csv, 2,879 rows).",
        "systems_compared": [
            "P0: default priors, seed 12345 (baseline); P0b: default priors, seed 22345 (noise floor)",
            "P1-P2: tau_alpha ~ LogNormal(ln 0.25, 0.5) / LogNormal(ln 1.0, 0.5)",
            "P3-P4: sigma_median ~ LogNormal(ln 0.05, 0.5) / LogNormal(ln 0.2, 0.5)",
            "P5-P6: tau_sigma ~ LogNormal(ln 0.25, 0.5) / LogNormal(ln 1.0, 0.5)",
            "P7: all three hyperprior SDs doubled (0.5 -> 1.0), centres unchanged",
            "P8: capability ~ Normal(0, 3) and difficulty ~ ZeroSumNormal(sigma=3) on the raw scale instead of the flat priors",
            "P9: capability ~ Normal(mu_c, s_c), mu_c ~ Normal(0, 5), s_c ~ HalfNormal(3); difficulty unchanged",
            "P10: sigma_b ~ LogNormal(ln 0.1, 0.75) truncated to (0, 0.5), independent across benchmarks (no sigma_median, no tau_sigma)",
            "X1 (stress, reported, not scored): tau_alpha ~ LogNormal(ln 0.1, 0.5)",
            "X2 (stress, reported, not scored): sigma_median ~ LogNormal(ln 0.02, 0.5)",
        ],
        "fixed_factors": ["data", "likelihood", "clip_eps 1e-3", "anchors", f"sampler: 4 chains, target_accept 0.95, draws={B2_DRAWS} per chain, seed 12345",
                          "strata"],
        "variable_factors": ["one prior component per entry (P1-P6, P8-P10); all three hyperprior widths jointly (P7)"],
        "metrics": ["S1 Spearman of posterior-mean ECI, per stratum", "S2 share of non-anchor models with abs(ECI_k - ECI_0) > 0.25 x W_0, per stratum",
                    "S3 share with W_k / W_0 outside [0.8, 1.25], per stratum", "S4 top-10 set and max abs change of P(i>j) over the 9 adjacent top-10 pairs",
                    "S5 psens of the hyperpriors for each model's ECI (decisive) and for tau_alpha, sigma_median, tau_sigma (reported)",
                    "importance-reweighted ECI means at alpha 0.8 and 1.25 with Pareto k (reported)",
                    "noise floor: S1-S4 of P0b against P0", "P(model in top 10) under each prior (reported)",
                    "S2 and S3 on the raw capability scale (reported)", "posterior mass with abs(raw capability) > 49 (reported)"],
        "setup_details": (f"Every fit: fit_bayesian_eci(df, priors=..., draws={B2_DRAWS}, random_seed=12345, evaluate=False) "
                          "(P0b uses seed 22345). P1-P7, X1, X2 need only BayesianPriors. P8-P10 need a model variant: "
                          "runs/lib/variants.py supplies a builder with the same signature and variable names as "
                          "build_bayesian_model and, inside a context manager, sets eci.bayesian.build_bayesian_model, "
                          "eci.bayesian._FREE_VARS and eci.bayesian._DIAGNOSTIC_VARS to the variant's builder and variable "
                          "lists (Epoch's dense-mass-matrix code indexes draws by those names); nothing under ext/ is edited. "
                          "Step 1: fit P0 and P0b and compute the noise floor; if P0b against P0 has any model with relative "
                          "shift above 0.05 or any adjacent-pair probability change above 0.03, double draws for all B2 fits "
                          "once. Step 2: S5 screen on P0 (M3). Step 3: fit each grid entry and score S1-S4 against P0. The "
                          "screen never changes the grid; it can only add the two power-scaled refits named in the C1 rule."),
        "seeds": 1,
        "success_criterion": "C1 decision rule: all ten priors resolved, S1-S4 pass in the all-models, frontier and sparse strata, and S5 passes (or its two follow-up refits pass S1-S4).",
        "minimum_effect_size": "0.25 x a model's baseline 90% interval width: 1.1 to 1.9 ECI points for the 20 frontier models (published widths 4.24 to 7.56), and up to 10.5 points for the widest sparse model (width 41.8).",
        "failure_interpretation": "See C1 decision_if_unproven: a sparse-only failure narrows C1; a frontier or all-models failure falsifies it.",
        "expected_output_artifact": "runs/B2/sensitivity.json",
        "compute_budget": f"14 fits at draws={B2_DRAWS} (P0, P0b, P1-P10, X1, X2), roughly 3 to 5 minutes each, plus up to 2 follow-up fits and the screen: 1 to 1.5 hours wall-clock.",
        "dependencies": ["B0", "B1"],
        "priority": "must-run",
        "current_evidence_class": "exploratory", "evidence_class": "confirmatory",
        "selection_rule": "Grid chosen from Epoch's stated priors: each hyperprior centre moved by a factor of 2 each way, widths doubled, and the structural alternatives a reviewer would raise (proper, hierarchical, non-pooled). Frozen in prior-grid.json.",
        "non_vacuity_check": "B1's positive-control prior must fail S1-S4; otherwise G1 tightens S2 once, and if it still passes C1 is capped at exploratory.",
        "complete_outcome_accounting": "Every grid entry reported. A fit that fails Epoch's convergence checks is retried once with draws doubled (P9 may switch to a non-centred parameterisation for the retry), then reported as unresolved.",
        "hidden_information_controls": "Grid, metric code and thresholds frozen (digests in runs/freeze.json) before any refit or screen.",
        "independence_requirements": ["Self-review only."],
        "independence_evidence": "None claimed; confirmatory status rests on pre-registration, not independence.",
        "operational_threat_model": "", "operational_harms": "",
        "predecessor_failures": ["v1 NUTS non-convergence (C1)."],
        "execution": {
            "mode": "command",
            "entrypoint": {"argv": ["uv", "run", "--project", "runs", "python", "runs/b2_sensitivity.py"], "cwd": "."},
            "declared_inputs": [ZIP, {"path": "runs/B1/calibration.json", "role": "positive-control result and any S2 tightening decided at G1", "snapshot": "digest-at-start"}],
            "declared_evaluator_artifacts": [ECI_CODE, PRIOR_GRID, SENS],
            "required_outputs": [{"path": "runs/B2/sensitivity.json", "kind": "metrics"},
                                 {"path": "runs/B2/fig_sensitivity.png", "kind": "figure"}],
        },
        "lineage_policy": {"allowed_relations": ["baseline", "sensitivity", "parameter_variation", "technical_retry"]},
    },
    {
        "block_id": "B3", "paper_role": "main", "claim_ids": ["C2"], "decision_gate_id": "G3",
        "anti_claims_ruled_out": ["Clean checks from tests with no power (C2 anti-claim)."],
        "why_this_block_exists": "Runs and reports Epoch's own diagnostic suite, and adds the structural checks and held-out coverage that suite lacks.",
        "dataset_split_task": ("Same fit input as B0a. B3c: 5 folds over the 217 models with 6 or more scores; each of their "
                               "2,704 scores is held out exactly once (M7); the 39 models with 4 or 5 scores are never held out."),
        "systems_compared": ["ECI default fit (B0 seed 12345)", "5 fold refits (B3c)", "B3d: refit without the localised benchmark set F, only if a check rejects or a benchmark is flagged"],
        "fixed_factors": ["data", "default priors", "code", "ppc_checks.py as frozen in B1"],
        "variable_factors": ["check", "fold"],
        "metrics": [
            "B3a Epoch's suite as shipped (evaluate_fit): sampler diagnostics; RMSE, MAE, bias, per-benchmark RMSE / predicted SD, and their PSIS-LOO versions; elpd_loo, p_loo and Pareto-k bands; mid-p posterior predictive p-values per benchmark and pooled for mean, sd, variance, iqr, skew, frac_below_0.05, frac_above_0.95 (min and max are computed but excluded as degenerate); PIT mean, KS test and coverage at 50/80/90/95%, in-sample and PSIS-LOO",
            "T1 item-curve shape: mean over 44 benchmarks of the 4-bin sum of n x (mean standardised residual)^2",
            "T2 local dependence: mean over 445 benchmark pairs (15+ shared models) of (n - 3) x atanh(r)^2; also max abs r and share with abs r > 0.3 (reported)",
            "T3 dispersion form: weighted squared log of mean z^2 over five bins of predicted mean",
            "T4 time drift: abs Spearman correlation of z with days between benchmark release and model release, over all rows",
            "T5 developer x benchmark: max abs standardised cell mean over the 185 cells with 5+ rows",
            "T6 boundary mass: chi-square distance between observed and predicted counts at the two clip bounds",
            "T7 per-model fit: max over the 217 models with 6+ scores of mean z^2",
            "B3c held-out 90% coverage: overall, per benchmark with 20+ held-out scores (44), with model-cluster bootstrap interval",
            "B3d: relative ECI shift per model after removing F",
        ],
        "setup_details": ("B3a: read draws['evaluation'] from the B0 seed-12345 run and write Epoch's PDF with save_evaluation. "
                          "B3b: compute T1-T7 (M5) on the real data with 400 evenly spaced B0 draws, then unadjusted, max-T "
                          "adjusted (M6) and raw in-sample posterior predictive p-values. B3c: folds and coverage as in M7; "
                          "fold refits use fit_bayesian_eci(train, random_seed=12345+fold). B3d: localisation and refit as in M6."),
        "seeds": 1,
        "success_criterion": "C2 decision rule: no check with max-T adjusted p < 0.01, overall held-out coverage in [0.85, 0.95], and no benchmark flagged by the Bonferroni binomial test.",
        "minimum_effect_size": "max-T adjusted p < 0.01 (attainable minimum 0.005 with 199 null replicates); overall coverage outside [0.85, 0.95]; per-benchmark binomial p < 0.01 / 44.",
        "failure_interpretation": "See C2 decision_if_unproven; B3d measures how much the localised misfit moves ECI scores.",
        "expected_output_artifact": "runs/B3/ppc.json",
        "compute_budget": "5 fold refits and at most 1 B3d refit at about 2 minutes each, plus checks on 400 draws: about 30 minutes wall-clock.",
        "dependencies": ["B0", "B1"],
        "priority": "must-run",
        "current_evidence_class": "exploratory", "evidence_class": "confirmatory",
        "selection_rule": f"Fold assignment from numpy default_rng({RNG_SEED}) as in M7, written to runs/B3/folds.csv before any fold fit; check list and statistics fixed before B0's residuals are viewed.",
        "non_vacuity_check": "A check counts towards 'Adequate' only if its targeted generator gave power >= 0.8 in B1; T6 and T7 have no targeted generator and are reported as 'power not assessed'. Rejections count regardless of power.",
        "complete_outcome_accounting": "All seven checks reported with unadjusted, adjusted and raw p; every fold's convergence status; scores at the clip bounds handled exactly as the likelihood sees them.",
        "hidden_information_controls": "Held-out scores are removed from the fit input before sampling; fold assignment is written before fitting.",
        "independence_requirements": ["Self-review only."],
        "independence_evidence": "None claimed.",
        "operational_threat_model": "", "operational_harms": "",
        "predecessor_failures": ["v1 Q3 local-dependence failure (C2)."],
        "execution": {
            "mode": "command",
            "entrypoint": {"argv": ["uv", "run", "--project", "runs", "python", "runs/b3_ppc.py"], "cwd": "."},
            "declared_inputs": [ZIP, {"path": B0_NC, "role": "posterior", "snapshot": "digest-at-start"},
                                {"path": "runs/B1/calibration.json", "role": "null reference values and power", "snapshot": "digest-at-start"}],
            "declared_evaluator_artifacts": [ECI_CODE, CHECKS],
            "required_outputs": [{"path": "runs/B3/ppc.json", "kind": "metrics"},
                                 {"path": "runs/B3/evaluation_report.pdf", "kind": "figure"}],
        },
        "lineage_policy": {"allowed_relations": ["baseline", "ablation", "sensitivity", "technical_retry"]},
    },
    {
        "block_id": "B4", "paper_role": "main", "claim_ids": ["C3"], "decision_gate_id": "G4",
        "anti_claims_ruled_out": ["Low coverage from crosswalk errors or from evaluation-setup variance (C3 anti-claim)."],
        "why_this_block_exists": "Finds the EEE data that correspond to ECI's benchmarks and models and tests whether ECI's intervals predict them.",
        "dataset_split_task": ("B4a crosswalk (M9): all 122,861 aggregate records of EEE manifest dd7efcff (129 collections, 2.2 GB) "
                               "are downloaded and screened; every evaluation result is mapped, or not, to one of the 57 ECI "
                               "benchmarks and to an Epoch model group. Named-benchmark collections expected to match include "
                               "gpqa-diamond, gpqa_diamond, frontiermath, arc-agi, terminal-bench-2.0, cybench, apex-agents, "
                               "gsm8k, hellaswag, piqa and big_bench_hard; multi-benchmark collections to screen result by "
                               "result include artificial-analysis-llms, vals-ai, paperswithcode, hfopenllm_v2, llm-stats, "
                               "openeval, benchpress, wild and helm_*. Scores are normalised with Epoch's random_baseline and "
                               "score_ceiling. B4b: ECI predictive distribution for each matched pair (M8)."),
        "systems_compared": ["ECI predictive distribution (B0 seed-12345 fit)", "EEE-vs-EEE agreement on the same model x benchmark (noise floor)",
                             "same-upstream pairs (for example ARC Prize, Terminal-Bench, Mercor APEX) as the crosswalk positive control"],
        "fixed_factors": ["B0 posterior", "normalisation", "frozen maps and source classes"],
        "variable_factors": ["pair class: same-upstream / independent / upstream-unknown", "Epoch's own score for the pair in the fit or not"],
        "metrics": ["crosswalk counts by class and exclusion reason", "audit errors among 50 random matched pairs, with Clopper-Pearson 95% upper bound",
                    "same-upstream median and 90th percentile absolute difference", "90% coverage on independent pairs with a 90% model-cluster bootstrap interval (2,000 resamples)",
                    "coverage split by in-fit / not-in-fit and by benchmark", "EEE-vs-EEE agreement rate", "signed mean difference (EEE minus ECI predictive mean) per benchmark",
                    "sensitivity: coverage after removing independent pairs whose raw score equals Epoch's to 3 decimals; coverage excluding pairs with Pareto k > 0.7"],
        "setup_details": ("Stage a (no ECI predictions loaded): download objects, verify sha256 against the manifest, build "
                          "runs/B4/collection_screen.csv, benchmark_map.csv, model_map.csv and source_class.csv by the rules in "
                          "M9, classify every result, aggregate to pairs, draw the audit sample, audit, and freeze the maps "
                          "(digests in runs/freeze.json). Stage b (only after the audit passes): join the B0 posterior, "
                          "compute PIT, coverage, agreement and bias. One wrapper runs both: runs/b4_run.py --stage a|b|all."),
        "seeds": 1,
        "success_criterion": "C3 decision rule with its preconditions: audit errors <= 2 of 50, same-upstream median absolute difference <= 0.02, at least 100 independent pairs over 20 model groups and 5 benchmarks, and coverage >= 0.80 with agreement not below 0.80.",
        "minimum_effect_size": "coverage thresholds 0.80 and 0.65; agreement threshold 0.80",
        "failure_interpretation": ("More than 2 audit errors stop stage b until one round of fixes and a fresh audit sample. Low "
                                   "coverage with agreement >= 0.80 falsifies C3; agreement below 0.80 gives the verdict "
                                   "`harness-limited`."),
        "expected_output_artifact": "runs/B4/transfer.json",
        "compute_budget": "Download and parse 122,861 JSON objects (2.2 GB); no new fits. 2 to 4 hours wall-clock, mostly I/O, plus the manual mapping and audit.",
        "dependencies": ["B0"],
        "priority": "must-run",
        "current_evidence_class": "exploratory", "evidence_class": "exploratory",
        "selection_rule": "Inclusion, exclusion and source class are decided from metadata (benchmark version, split, metric, model identity, source organisation) before ECI predictions are computed for any pair.",
        "non_vacuity_check": "Same-upstream pairs give a case where the comparison must succeed; EEE-vs-EEE agreement gives the rate a perfect index could reach.",
        "complete_outcome_accounting": "Every EEE result is classified into exactly one class of the C3 loss contract; counts per class, collection and benchmark are reported; failed downloads are listed.",
        "hidden_information_controls": "Crosswalk built and audited without loading ECI predictions; stage b refuses to run unless the map digests match runs/freeze.json.",
        "independence_requirements": ["EEE data are independent of Epoch only for pairs classed 'independent' by M9; the class is recorded per pair."],
        "independence_evidence": "source_metadata.source_organization_name, source_type and evaluator_relationship per EEE record, against the source column of Epoch's row.",
        "operational_threat_model": "", "operational_harms": "",
        "predecessor_failures": ["v1 cross-source coverage 0.70 (C3)."],
        "execution": {
            "mode": "command",
            "entrypoint": {"argv": ["uv", "run", "--project", "runs", "python", "runs/b4_run.py", "--stage", "all"], "cwd": "."},
            "declared_inputs": [ZIP, EEE_MAN, {"path": B0_NC, "role": "posterior (stage b only)", "snapshot": "digest-at-start"}],
            "declared_evaluator_artifacts": [{"path": "runs/B4/benchmark_map.csv", "role": "hand-built, frozen after audit", "snapshot": "digest-at-start"},
                                             {"path": "runs/B4/model_map.csv", "role": "rule-built with manual review, frozen after audit", "snapshot": "digest-at-start"},
                                             {"path": "runs/B4/source_class.csv", "role": "source class per EEE source, frozen after audit", "snapshot": "digest-at-start"}],
            "required_outputs": [{"path": "runs/B4/crosswalk.parquet", "kind": "data"},
                                 {"path": "runs/B4/audit_sample.csv", "kind": "audit"},
                                 {"path": "runs/B4/transfer.json", "kind": "metrics"}],
        },
        "lineage_policy": {"allowed_relations": ["baseline", "negative_control", "sensitivity", "technical_retry"]},
    },
    {
        "block_id": "B5", "paper_role": "appendix", "claim_ids": ["C3"], "decision_gate_id": "G5",
        "anti_claims_ruled_out": ["ECI's conclusions depend on Epoch's data collection rather than on the method."],
        "why_this_block_exists": "Fits the ECI model to the EEE-matched matrix and compares rankings and intervals with B0.",
        "dataset_split_task": ("Matched-independent pairs from B4a, one row per (model group, benchmark) taking the highest "
                               "normalised score across sources, then Epoch's inclusion rule (at least 4 benchmarks and at "
                               "least 4 with a score in [0.1, 0.9])."),
        "systems_compared": ["ECI on Epoch data (B0)", "ECI on EEE-matched data"],
        "fixed_factors": ["code", "default priors", "anchors (if both anchor models are present; otherwise rank agreement only)"],
        "variable_factors": ["data source"],
        "metrics": ["Spearman of posterior-mean ECI on shared models", "share of shared non-anchor models whose two 90% intervals intersect",
                    "S5 screen on the EEE fit", "T2 and in-sample 90% coverage on the EEE fit (descriptive; no null reference is simulated)"],
        "setup_details": "Runs only if G4 finds at least 15 benchmarks and at least 100 models after the inclusion rule.",
        "seeds": 1,
        "success_criterion": "Spearman >= 0.9 and at least 80% of shared non-anchor models with intersecting 90% intervals.",
        "minimum_effect_size": "Spearman 0.9",
        "failure_interpretation": "ECI rankings depend on which sources are pooled; report as a data-dependence finding.",
        "expected_output_artifact": "runs/B5/eee_refit.json",
        "compute_budget": "2 to 3 fits, about 10 minutes",
        "dependencies": ["B4"],
        "priority": "nice-to-have",
        "current_evidence_class": "exploratory", "evidence_class": "exploratory",
        "selection_rule": "All matched-independent pairs; no further selection.",
        "non_vacuity_check": "Different sources and evaluation setups can reorder models; agreement is not guaranteed.",
        "complete_outcome_accounting": "Models dropped by the inclusion rule are counted.",
        "hidden_information_controls": "None needed.",
        "independence_requirements": ["As B4."],
        "independence_evidence": "As B4.",
        "operational_threat_model": "", "operational_harms": "",
        "predecessor_failures": [],
        "execution": {
            "mode": "command",
            "entrypoint": {"argv": ["uv", "run", "--project", "runs", "python", "runs/b5_eee_refit.py"], "cwd": "."},
            "declared_inputs": [{"path": "runs/B4/crosswalk.parquet", "role": "EEE-matched matrix", "snapshot": "digest-at-start"},
                                {"path": B0_NC, "role": "B0 posterior for comparison", "snapshot": "digest-at-start"}],
            "declared_evaluator_artifacts": [ECI_CODE],
            "required_outputs": [{"path": "runs/B5/eee_refit.json", "kind": "metrics"}],
        },
        "lineage_policy": {"allowed_relations": ["baseline", "replication", "alternative_hypothesis", "technical_retry"]},
    },
    {
        "block_id": "B6", "paper_role": "appendix", "claim_ids": ["C1"], "decision_gate_id": "G6",
        "anti_claims_ruled_out": ["Prior robustness hides sensitivity to data-handling choices that act like priors."],
        "why_this_block_exists": ("Epoch's own docstring says performance_clip_eps changes capabilities; inclusion rules, "
                                  "ceilings and anchors also shape the posterior. Not priors, so outside C1's rule, but a reviewer will ask."),
        "dataset_split_task": ("Clip and anchor variants use the B0a fit input. Inclusion and ceiling variants must rebuild the "
                               "input with prepare_benchmark_data(zip, ...), so they are compared with B0b (the loader-input "
                               "baseline), not B0a."),
        "systems_compared": ["performance_clip_eps 1e-4 / 1e-2", "min_mid_range_benchmarks_per_model 3 / 6",
                             "score_ceiling set to 1.0 for every benchmark (benchmark_metadata override)",
                             "anchors swapped for two other models with 20+ scores (no refit: re-anchor the P0 draws; rank and interval width only)"],
        "fixed_factors": ["priors", "likelihood", f"sampler as B2 (draws={B2_DRAWS})"],
        "variable_factors": ["one handling choice per run"],
        "metrics": ["C1 metrics S1-S4 against the matching baseline, on models present in both fits; models added or dropped by the variant"],
        "setup_details": "Same pipeline and metric code as B2 step 3. Metadata overrides are passed as DataFrames; nothing under ext/ is edited.",
        "seeds": 1,
        "success_criterion": "S1-S4 pass, reported per choice.",
        "minimum_effect_size": "as C1",
        "failure_interpretation": "Report which handling choice matters; does not change C1's verdict.",
        "expected_output_artifact": "runs/B6/handling.json",
        "compute_budget": "6 fits (5 variants and a B0b-input baseline at B2 settings), about 30 minutes",
        "dependencies": ["B2"],
        "priority": "nice-to-have",
        "current_evidence_class": "exploratory", "evidence_class": "exploratory",
        "selection_rule": "Choices exposed as arguments in Epoch's code.",
        "non_vacuity_check": "Epoch's docstring already predicts clip_eps matters, so a null result is not guaranteed.",
        "complete_outcome_accounting": "All runs reported.",
        "hidden_information_controls": "None needed.",
        "independence_requirements": ["Self-review only."],
        "independence_evidence": "None claimed.",
        "operational_threat_model": "", "operational_harms": "",
        "predecessor_failures": [],
        "execution": {
            "mode": "command",
            "entrypoint": {"argv": ["uv", "run", "--project", "runs", "python", "runs/b6_handling.py"], "cwd": "."},
            "declared_inputs": [ZIP],
            "declared_evaluator_artifacts": [ECI_CODE, SENS],
            "required_outputs": [{"path": "runs/B6/handling.json", "kind": "metrics"}],
        },
        "lineage_policy": {"allowed_relations": ["baseline", "sensitivity", "parameter_variation", "technical_retry"]},
    },
]

OUT.mkdir(parents=True, exist_ok=True)
(OUT / "claim-map.json").write_text(json.dumps(claims, indent=2) + "\n")
(OUT / "run-blocks.json").write_text(json.dumps(blocks, indent=2) + "\n")

# Each hyperprior is LogNormal(mu, sigma) given as [mu written as "ln <median>", sigma], as in
# eci.bayesian.BayesianPriors. An entry lists only what differs from the baseline.
grid = {
    "frozen_at": "2026-11-13, before any refit or power-scaling screen (revised the same day by pre-run review; see the Revision log in experiment-plan.md)",
    "parameterisation": "hyperpriors are LogNormal(mu, sigma) of the underlying normal, as in eci.bayesian.BayesianPriors; 'ln 0.5' means mu = log(0.5)",
    "baseline": {"tau_alpha": ["ln 0.5", 0.5], "sigma_median": ["ln 0.1", 0.5], "tau_sigma": ["ln 0.5", 0.5],
                 "sigma": "LogNormal(ln sigma_median, tau_sigma) truncated to (0, 0.5), per benchmark",
                 "log_slope": "ZeroSumNormal(sigma = tau_alpha * sqrt(K / (K - 1))), K = 57",
                 "capability": "Uniform(-50, 50)", "difficulty": "flat on the sum-to-zero subspace, each coordinate bounded to [-50, 50]"},
    "defensible": {
        "P1": {"tau_alpha": ["ln 0.25", 0.5]}, "P2": {"tau_alpha": ["ln 1.0", 0.5]},
        "P3": {"sigma_median": ["ln 0.05", 0.5]}, "P4": {"sigma_median": ["ln 0.2", 0.5]},
        "P5": {"tau_sigma": ["ln 0.25", 0.5]}, "P6": {"tau_sigma": ["ln 1.0", 0.5]},
        "P7": {"tau_alpha": ["ln 0.5", 1.0], "sigma_median": ["ln 0.1", 1.0], "tau_sigma": ["ln 0.5", 1.0]},
        "P8": {"capability": "Normal(0, 3)", "difficulty": "ZeroSumNormal(sigma=3)"},
        "P9": {"capability": "Normal(mu_c, s_c); mu_c ~ Normal(0, 5); s_c ~ HalfNormal(3)"},
        "P10": {"sigma": "independent LogNormal(ln 0.1, 0.75) truncated to (0, 0.5); sigma_median and tau_sigma removed"},
    },
    "stress_reported_not_scored": {"X1": {"tau_alpha": ["ln 0.1", 0.5]}, "X2": {"sigma_median": ["ln 0.02", 0.5]}},
    "positive_control_B1": {"PC": {"tau_alpha": ["ln 0.05", 0.1]}},
    "s5_followup_refits": ("Only if S5 flags a hyperprior LogNormal(mu, s): refit with LogNormal(mu + s^2 (1 - a) / a, s / sqrt(a)) "
                           "for a = 0.8 and a = 1.25, which is that prior raised to the power a. For s = 0.5: mu + 0.0625 with "
                           "sigma 0.559, and mu - 0.05 with sigma 0.447."),
    "sampler": {"chains": 4, "target_accept": 0.95, "draws_per_chain": B2_DRAWS, "seed": 12345, "noise_floor_seed": 22345},
    "note": ("P8 and P9 scales are on the raw (pre-anchor) scale, where the geometric-mean slope is 1 and difficulties sum to 0. "
             "Guard fixed before any fit: let s0 be the SD across the 256 models of the posterior-mean raw capability in B0 seed "
             "12345. If s0 > 3, P8 uses Normal(0, 2 x s0) for capability and ZeroSumNormal(2 x s0) for difficulty. The published "
             "draws give s0 = 2.62, so the guard is not expected to trigger."),
}
(OUT / "prior-grid.json").write_text(json.dumps(grid, indent=2) + "\n")
print(f"ok: wrote claim-map.json, run-blocks.json, prior-grid.json to {OUT}")
