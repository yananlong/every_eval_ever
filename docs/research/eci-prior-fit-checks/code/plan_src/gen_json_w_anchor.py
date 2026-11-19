"""Write claim-map.json, run-blocks.json and prior-grid.json for the ECI Bayesian-workflow plan (block W).

Usage (from the v11/ directory):  python3 -I plan_src/gen_json_w.py [OUT_DIR]
OUT_DIR defaults to wt-pr14/docs/research/eci-prior-fit-checks/, a sibling of the v11/ directory.

"M1" ... "M10" refer to the numbered parts of the "Methods Specification" section of
experiment-plan.md. Thresholds are defined once here (constants below) and repeated in the
Markdown files by hand; if you change one, change the Markdown and add a Revision log entry.
"""
import json
import sys
from pathlib import Path

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[2] / "wt-pr14" / "docs" / "research" / "eci-prior-fit-checks"
EXT = "ext"  # relative to v11/

# ---- Frozen constants (also quoted in the Markdown files) --------------------------------------
N_OBS, N_MODELS, N_BENCH = 2879, 256, 57
N_SPARSE, N_DENSE, N_FRONTIER = 72, 184, 20      # <=6 scores, >=7 scores, top 20 by published eci
R_NULL = 199                                     # G-null replicates (also the SBC replicates)
R_MISFIT = 20                                    # replicates per misfit generator
ALPHA_FW = 0.01                                  # family-wise level for T1-T7
W5_DRAWS = 4000                                  # fixed draws per chain for every W5 grid fit (old B2)
R_SBC_RED = 30                                   # replicates of the reduced SBC for an expansion (20 for the 2-D model)
DELTA_ELPD, Z_ELPD = 4, 2.5                      # W6 preference rule: elpd difference > 4 and > 2.5 SE
K_SHARE = 0.02                                   # W6 K-fold trigger: share of rows with Pareto k > 0.7
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
PRIOR_GRID = {"path": "experiment-plan/prior-grid.json", "role": "frozen before any W3 positive-control fit, W5 refit or screen", "snapshot": "digest-at-start"}
CHECKS = {"path": "runs/lib/ppc_checks.py", "role": "T1-T7 and the max-T calibration; frozen before any W3 generator runs", "snapshot": "digest-at-start"}
SENS = {"path": "runs/lib/sens_metrics.py", "role": "S1-S5 on the anchored scale; frozen before the W3 positive-control fit", "snapshot": "digest-at-start"}
SBC = {"path": "runs/lib/sbc.py", "role": "SBC rank statistic and test (M13); frozen before any W3 replicate runs", "snapshot": "digest-at-start"}
COMPARE = {"path": "runs/lib/compare.py", "role": "PSIS-LOO, K-fold elpd, the W6 preference rule and the multiverse summary (M14); frozen before any W6 fit", "snapshot": "digest-at-start"}
MODELS = {"path": "runs/lib/models.py", "role": "our reimplementation of the base model (F0), the reference-prior variant (F6) and the expansions F1-F5 (M12, M14); frozen before any expansion is fitted", "snapshot": "digest-at-start"}
W2_NC = "runs/W/W2/seed12345.nc"

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
        "minimum_convincing_evidence": ("W2 reproduces the published scores and intervals; W3 shows the sensitivity metrics "
                                        "flag a deliberately strong prior; W5 runs the power-scaling screen and then scores every "
                                        "defensible prior of the full pre-registered grid against the C1 decision rule, with a "
                                        "seed-to-seed noise floor measured for every metric."),
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
        "linked_blocks": ["W", "B6"],
        "current_evidence_class": "exploratory",
        "evidence_class": "confirmatory",
        "decision_rule": ("Quantities (M1): per-draw anchored ECI; point estimate = posterior mean; W = 95th minus 5th "
                          "percentile. Baseline = fit P0 (default priors, W5 sampler settings, seed 12345). " + STRATA + " "
                          "For each defensible prior k in P1-P10 and each stratum: S1 Spearman(ECI_k, ECI_0) >= 0.99 over "
                          "the stratum's models; S2 share of non-anchor models with abs(ECI_k - ECI_0) > 0.25 x W_0 is <= 5% "
                          "(at most 12 of 254, 1 of 20, 3 of 72); S3 share with W_k / W_0 outside [0.8, 1.25] is <= 5% (same "
                          "counts); S4 (scored once, counted in the frontier and all-models strata) the set of the 10 highest "
                          "posterior-mean ECI is unchanged and abs(P_k(i>j) - P_0(i>j)) < 0.10 for each of the 9 adjacent "
                          "pairs of the baseline top-10 order. S5 (screen on the W2 seed-12345 draws, no refit, run first in W5): power-scaling sensitivity "
                          "psens of the three hyperpriors <= 0.05 for at least 95% of non-anchor models' ECI in each stratum. "
                          "Verdicts. Robust: all ten priors resolved, S1-S4 pass in all three strata, S5 passes. Conditionally "
                          "robust: every S1-S3 failure is in the sparse stratum only and S4 passes. Sensitive: any S1-S4 "
                          "failure in the all-models or frontier stratum. An S5-only flag does not decide the verdict: the "
                          "two exact power-scaled refits of the flagged hyperprior (alpha 0.8 and 1.25, M3) are scored with "
                          "S1-S4 as extra grid entries and they decide. An entry still unresolved after its retry means C1 "
                          "cannot be Robust and is reported as not established for that prior. Added by the restructure of "
                          "2026-11-18 and exploratory, outside this rule: the reference-prior entry PR (W1) and the S5-targeted "
                          "refits at alpha 0.5 and 2 are scored with S1-S4 and reported, but never enter the verdict."),
        "loss_contract": ("Every grid entry is reported, including the stress priors X1 and X2 (reported, not scored), fits "
                          "that fail convergence (counted as unresolved, never dropped), and the two anchor models (kept in "
                          "S1 and S4, excluded from S2, S3 and S5 because their values are fixed by definition). The "
                          "seed-to-seed noise floor of every metric (P0 against P0b) is reported next to each result. The exploratory entry PR "
                          "and every S5-targeted refit are listed with the grid and labelled exploratory."),
        "falsification_test": "W5 refit grid scored against the decision rule; see falsifier.",
        "selection_history": [
            ("Before writing this plan we inspected: Epoch's code and README, the 2026-11-13 zip's benchmark list, "
             "per-model observation counts, published ECI and interval widths, and EEE collection names. No refit was run. "
             "The prior grid is written from the README's stated priors and the observation-count distribution."),
            ("Restructure of 2026-11-18 (nothing executed): B0-B3 were merged into block W (Revision Log R17-R25). No threshold, "
             "grid entry P1-P10, X1, X2 or rule of this claim was changed. The reference prior PR was chosen by a prior predictive "
             "simulation on the observed (model, benchmark) pattern only, with the published capability spread of the review in "
             "view; it is exploratory."),
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
             "mass matrix, but W2 must confirm convergence before any sensitivity number is trusted."),
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
        "minimum_convincing_evidence": ("Epoch's own suite run and reported (W4a); the structural checks T1-T7 referred to "
                                        f"{R_NULL} null simulations with refits and shown in W3 to detect planted misfit (W4b); "
                                        "5-fold held-out coverage (W4c)."),
        "anti_claim": ("A clean result reflects checks with no power (posterior predictive p-values are conservative "
                       "because the data are used twice), not an adequate model."),
        "falsifier": ("The Inadequate verdict of the decision rule: a check with max-T adjusted p < 0.01, or overall held-out "
                      "90% coverage outside [0.85, 0.95], or a benchmark with 20 or more held-out scores whose coverage "
                      "fails the Bonferroni binomial test, where the failure is not localised to at most 10 benchmarks or "
                      "removing those benchmarks (W4d) moves a model by more than 0.25 x W_0."),
        "decision_if_unproven": {
            "action": "reframe",
            "note": ("Report the misfit as a finding: which check fails, on which benchmarks or developers, and the "
                     "size of the ECI shift when the offending benchmarks are dropped (W4d). The claim becomes "
                     "'ECI is adequate except for X, which moves scores by Y'."),
        },
        "linked_blocks": ["W"],
        "current_evidence_class": "exploratory",
        "evidence_class": "confirmatory",
        "decision_rule": ("T1-T7 (M5) are scalar discrepancy statistics, larger meaning worse fit, computed the same way on "
                          f"the real data with the W2 fit and on each of R = {R_NULL} G-null datasets with its own refit. "
                          "Unadjusted p_k = (1 + number of converged null replicates with T_k >= observed T_k) / (R' + 1). "
                          "Family-wise adjusted p_k by single-step max-T over the seven checks on standardised log statistics "
                          f"(M6). A check is rejected if adjusted p_k < {ALPHA_FW}; with R' = 199 the smallest attainable "
                          "value is 0.005. Held-out coverage (M7): the share of the 2,704 held-out scores whose PIT lies in "
                          "[0.05, 0.95] must be in [0.85, 0.95]; each of the 44 benchmarks with 20 or more held-out scores "
                          "is flagged if an exact two-sided binomial test of coverage = 0.90 gives p < 0.01 / 44. "
                          "Adequate: no check rejected, overall coverage in range, no benchmark flagged; the statement is "
                          "limited to misfit types whose targeted check reached power >= 0.8 in W3, and the others are listed "
                          "as not assessed. Adequate with exceptions: every rejection or flag is localised (M6) to a benchmark "
                          "set F with at most 10 members, and the W4d refit without F moves no retained non-anchor model by "
                          "more than 0.25 x W_0 and drops no frontier model. Inadequate: any other rejection or coverage "
                          "failure. Inconclusive: nothing rejected, but neither T2 (on G-2D) nor T5 (on G-offset) reached "
                          "power 0.8; C2 then stays exploratory. The model expansions of W6 are exploratory, are fitted after this "
                          "verdict is recorded and frozen, and never change it."),
        "loss_contract": ("All seven checks are reported with unadjusted, adjusted and raw in-sample posterior predictive "
                          "p-values; no check is dropped after seeing results. Non-converged null replicates are excluded "
                          "from the reference set and counted. Scores at 0 or 1 are clipped to [0.001, 0.999] exactly as the "
                          "likelihood sees them; Epoch's min and max statistics are excluded as Epoch excludes them."),
        "falsification_test": "W4 checks and held-out coverage against the decision rule; see falsifier.",
        "selection_history": [
            "No posterior or residual was inspected before the check list T1-T7 was written.",
            "Restructure of 2026-11-18 (nothing executed): B1 and B3 became W3 and W4; T1-T7, M5-M7, thresholds and the decision rule are unchanged. The G-null refits now also serve as SBC replicates (W3), which adds a report and no gate.",
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
                          "90% cluster-bootstrap interval is reported beside it. The verdict is defined on Epoch's base model as published "
                          "(the W2 fit). Coverage under the adequate expansions of W6 is reported beside it as exploratory and never "
                          "replaces it."),
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
        "block_id": "W", "paper_role": "main", "claim_ids": ["C1", "C2"], "decision_gate_id": "G0",
        "anti_claims_ruled_out": [
            "Our results describe a different fit from Epoch's (W2).",
            "Robustness in W5 comes from metrics that cannot detect sensitivity, or from perturbations too small to matter (C1 anti-claim; W3 positive control).",
            "Clean checks in W4 come from checks with no power (C2 anti-claim; W3 power runs).",
            "A fixed one-dimensional model hides structure that moves the scores (exploratory, W6).",
        ],
        "why_this_block_exists": ("One Bayesian workflow on Epoch's model (Gelman, Vehtari, McElreath et al. 2026, Bayesian Workflow), "
                                  "replacing four separate audits of a fixed model: prior predictive check (W1), fit and reproduction "
                                  "(W2), computational and check calibration by simulation from the fitted posterior (W3), posterior "
                                  "predictive and LOO-PIT checks (W4), prior sensitivity (W5) and model expansion with comparison "
                                  "(W6). The stages share the W2 fit, the W3 refits and one set of frozen check code, so each "
                                  "stage's output is the next stage's input."),
        "dataset_split_task": (f"Fit input: {FIT_INPUT} inside the zip ({N_BENCH} benchmarks, {N_MODELS} models, {N_OBS} rows). "
                               "W1: prior predictive simulation on its (model, benchmark) pattern. W2: Epoch's fit on the fit input "
                               "(W2a) and on the output of prepare_benchmark_data(zip) (W2b, three different GPQA diamond scores: Claude "
                               "Fable 5 0.957 vs 0.845; Claude Opus 5.5 0.959 vs 0.911; Claude Fable 5.2 0.986 vs 0.957), plus our "
                               "reimplementation of the base model (equivalence check EQ, M12). W3: data simulated on the observed "
                               f"pattern (M4): G-null ({R_NULL} replicates from the fitted posterior, also the SBC replicates) and five "
                               "misfit generators with 20 replicates each; the real data refitted with the positive-control prior. W4: the "
                               "real data and its 5 folds over the 217 models with 6 or more scores (M7). W5: the real data under the "
                               "prior grid. W6: the real data under the candidate models F0-F6 (M14), with PSIS-LOO over all 2,879 rows "
                               "or K-fold over the 2,704 eligible rows."),
        "systems_compared": [
            "W2a: fit_bayesian_eci(processed_data_for_eci.csv) with defaults, seeds 12345, 22345, 32345, against the published eci_scores.csv, edi_scores.csv, eci_bootstraps.json",
            "W2b: fit_bayesian_eci(prepare_benchmark_data(zip)), seed 12345 (data-provenance check, reported, not gated)",
            "EQ: our reimplementation F0 against Epoch's fit, seeds 12345 and 22345",
            "W3: the default ECI fit on each G-null and misfit replicate; the positive-control prior against the W2 fits",
            "W5: the baseline P0, its second-seed copy P0b, P1-P10, the stress priors X1 and X2, and the exploratory reference prior PR; added post-freeze (R26), the exploratory normalised Jeffreys priors J1 and J2, each fitted once like PR",
            "W6: F0 (base, Epoch's priors), F1 two-dimensional capability, F2 developer-by-benchmark offset, F3 upper asymptote below 1, F4 time drift, F5 per-model noise scale, F6 (base under PR), and at most one combined model F7",
        ],
        "fixed_factors": ["observation pattern of the real data", "code e04929a", "default BayesianPriors except where a stage varies them",
                          "performance_clip_eps=1e-3", "anchors Claude 3.5 Sonnet=130, GPT-5=150",
                          "check implementations in runs/lib/ppc_checks.py, runs/lib/sbc.py, runs/lib/sens_metrics.py and runs/lib/compare.py as frozen",
                          f"W5 sampler: 4 chains, target_accept 0.95, draws={W5_DRAWS} per chain, seed 12345"],
        "variable_factors": ["stage", "seed (W2, positive control)", "generator and replicate (W3)", "prior grid entry (W5)", "candidate model F0-F7 (W6)"],
        "metrics": [
            "W1: share of prior-simulated scores at the clip bounds and in [0.1, 0.9], per dataset, for Epoch's priors and PR; the PR criterion (mean mid-range share >= 0.40, at least 95% of datasets >= 0.15, mean bound share <= 0.35). Added post-freeze (R26): the same quantities for the normalised Jeffreys priors J1 and J2, by direct simulation, descriptive only",
            "W2: per model d_m = ECI_ours - ECI_published and d_m / W_m,published (seed 12345); Spearman over 256 models; interval-width ratio; max abs difference of edi and slope (reported); divergences, r_hat, bulk and tail ESS, BFMI, stage and attempts; seed-to-seed SD; W2b S1-S4 against W2a; EQ density difference, per-model difference, Spearman, width ratio and elpd_loo difference",
            "W3: recovery coverage overall and by stratum; SBC normalised ranks of ECI and EDI, per-parameter chi-square tests and pooled 50% and 90% coverage by stratum (M13); null reference values of T1-T7 from the converged G-null replicates (target 199); power of each targeted check; S1-S4 of the positive-control prior per seed; non-converged counts",
            "W4: Epoch's suite as shipped (W4a); T1-T7 unadjusted, max-T adjusted and raw p (W4b); held-out 90% coverage overall and per benchmark with a model-cluster bootstrap interval (W4c); relative ECI shift per model after removing the localised set F (W4d)",
            "W5: S1 Spearman, S2 share shifting by more than a quarter of the interval width, S3 interval-width ratio, S4 top-10 set and adjacent-pair probabilities, per stratum; S5 psens of the hyperpriors (decisive) and of each hyperprior separately (reported); noise floor; P(model in top 10); raw-scale S2 and S3 and posterior mass beyond abs 49 (reported)",
            "W6: PSIS-LOO elpd and SE of the difference to F0, Pareto-k shares, K-fold elpd where triggered, computational diagnostics and reduced-SBC coverage of each preferred expansion, the adequate set, and S1-S4 and interval-width change of ECI under each adequate model relative to F0",
        ],
        "setup_details": ("Stage order and dependencies are in the stage table of experiment-plan.md and the stage hand-offs of "
                          "execution-bridge.md; one wrapper, runs/w_run.py, runs a stage or all of them and stops at a failed gate. "
                          "W1 simulates and sets nothing. W2 fits with evaluate=True, adds the summed hyperprior log density (group "
                          "log_prior) and the per-draw ECI to each trace, and fits our F0 for EQ. W3 freezes the check code, runs the "
                          "positive control first, then G-null, then the misfit generators; replicate seed = first 4 bytes of "
                          "sha256('<generator>:<index>'); the SBC ranks and the T values come from the same refits. W4 reads the W2 "
                          "trace and the W3 reference values. W5 runs the S5 screen on the W2 seed-12345 draws first, then P0 and P0b "
                          "and the noise floor, then every grid entry including PR, then the targeted refits. W6 starts only after the "
                          "C1 and C2 verdicts are recorded and their files digested in runs/freeze.json."),
        "seeds": 3,
        "success_criterion": ("W2 (G0): seed 12345 abs(d_m) <= max(0.5, 0.07 x W_m,published) for every non-anchor model, Spearman >= "
                              "0.999, median width ratio in [0.95, 1.05] and at least 95% of the 254 ratios in [0.85, 1.15]; all three seeds "
                              "zero divergences, r_hat <= 1.01, bulk ESS >= 400. W3 (G1): recovery coverage over all non-anchor models in "
                              "[0.85, 0.95]; at least 150 converged null replicates; T2 power >= 0.8 on G-2D and T5 power >= 0.8 on "
                              "G-offset (16 of 20); the positive-control prior fails at least one of S1-S4 in the frontier or all-models "
                              "stratum on all three seeds. W4 (G3): C2 decision rule. W5 (G2): C1 decision rule. W1 has no gate. W6 (G7, "
                              "exploratory): equivalence check EQ passed; an expansion is preferred only if its elpd difference to F0 exceeds "
                              f"{DELTA_ELPD} and {Z_ELPD} standard errors, and adopted only if its computational checks and reduced SBC pass."),
        "minimum_effect_size": ("0.5 ECI points, or 0.07 of the published width where larger (G0); power 0.8 at family-wise alpha 0.01 (G1); "
                                "adjusted p < 0.01, coverage outside [0.85, 0.95], binomial p < 0.01 / 44 (G3); a quarter of a model's baseline "
                                "interval width, 1.1 to 1.9 ECI points for the 20 frontier models (G2); elpd difference above 4 (G7)."),
        "failure_interpretation": ("W2: production settings or data differ from the public ones; find the difference or rebaseline openly. "
                                   "W3: poor recovery means the published intervals are miscalibrated even when the model is true; a check "
                                   "without power cannot support C2. W4: W4d measures how far a localised misfit moves the scores. W5: a "
                                   "sparse-only failure narrows C1, a frontier or all-models failure falsifies it. W6: an adopted expansion "
                                   "is a finding about model structure and is reported beside, never instead of, the verdicts on Epoch's model."),
        "expected_output_artifact": "runs/W/workflow.json",
        "compute_budget": ("W1 about 5 minutes (no fits). W2 6 fits (4 Epoch, 2 of ours), about 30 minutes. W3 302 fits, about 10 hours "
                           "(about 40 CPU-hours), restartable. W4 about 30 minutes. W5 up to 23 fits (14 grid, PR, up to 2 C1 follow-ups, "
                           "up to 6 exploratory targeted refits), about 1 to 2 hours; the post-freeze exploratory fits of J1 and J2 (R26) are two more fits of PR's size, outside this count. W6 about 3 to 10 hours typical and up to about 24 hours in the "
                           "worst case, plus up to 8 hours if the combination F7 is fitted (M14); exploratory and stoppable. Without W6 the plan is "
                           "about 13.5 hours; with W6 about 17 to 24 hours typical (worst case about 46 hours). Under 2 GB RAM per fit; about 3.5 GB disk."),
        "dependencies": [],
        "priority": "must-run",
        "current_evidence_class": "exploratory", "evidence_class": "confirmatory",
        "selection_rule": ("Grid, check list, statistics, strata, generators, thresholds and the candidate list F0-F7 are fixed before any "
                           "refit (digests in runs/freeze.json). Planted effect sizes and the seed rule are fixed in M4; fold assignment "
                           "from numpy default_rng(20261113) as in M7. W6 fits every listed candidate; none is dropped after its elpd is seen."),
        "non_vacuity_check": ("The W2 comparison can fail; the positive-control prior must fail S1-S4 in W3 or G1 tightens S2 once; a check counts "
                              "towards 'Adequate' only if its targeted generator gave power >= 0.8; T6 and T7 are 'power not assessed'; the W1 "
                              "prior predictive check can fail for PR, which is then dropped; EQ can fail, which blocks W6."),
        "complete_outcome_accounting": ("Every seed, replicate, fold, grid entry and candidate model is reported with its convergence status; "
                                        "non-converged replicates are counted and excluded from the null reference, SBC and power; unresolved grid "
                                        "entries are reported as unresolved; every W6 candidate is listed with its elpd, including the ones not preferred."),
        "hidden_information_controls": ("Grid, metric code, check code, SBC code and thresholds frozen by digest before use; true simulation parameters "
                                        "written only to runs/W/W3/truth/, which ppc_checks.py never reads; held-out scores removed before sampling; the C1 "
                                        "and C2 verdict files are digested before any W6 elpd is computed."),
        "independence_requirements": ["Self-review only; simulation and analysis by the same agent; no independence claimed."],
        "independence_evidence": "None claimed; confirmatory status of C1 and C2 rests on pre-registration, not independence.",
        "operational_threat_model": "", "operational_harms": "",
        "predecessor_failures": ["v1 NUTS non-convergence (C1).", "v1 Q3 local-dependence failure (C2)."],
        "stages": [
            {"stage": "W1", "name": "Prior predictive check", "replaces": "G-prior of B1", "evidence_class": "exploratory", "gate": None,
             "depends_on": [], "claims": [], "entrypoint": "runs/w1_prior_predictive.py", "output": "runs/W/W1/prior_predictive.json", "compute": "about 5 minutes, no fits"},
            {"stage": "W2", "name": "Fit and reproduction", "replaces": "B0", "evidence_class": "exploratory", "gate": "G0",
             "depends_on": [], "claims": ["C1", "C2"], "entrypoint": "runs/w2_fit.py", "output": "runs/W/W2/reproduction.json", "compute": "6 fits, about 30 minutes"},
            {"stage": "W3", "name": "Computational and check calibration", "replaces": "B1", "evidence_class": "exploratory", "gate": "G1",
             "depends_on": ["W2"], "claims": ["C1", "C2"], "entrypoint": "runs/w3_calibrate.py", "output": "runs/W/W3/calibration.json", "compute": "302 fits, about 10 hours"},
            {"stage": "W4", "name": "Posterior predictive and LOO-PIT checks", "replaces": "B3", "evidence_class": "confirmatory", "gate": "G3",
             "depends_on": ["W2", "W3"], "claims": ["C2"], "entrypoint": "runs/w4_ppc.py", "output": "runs/W/W4/ppc.json", "compute": "about 30 minutes"},
            {"stage": "W5", "name": "Prior sensitivity", "replaces": "B2", "evidence_class": "confirmatory", "gate": "G2",
             "depends_on": ["W1", "W2", "W3"], "claims": ["C1"], "entrypoint": "runs/w5_sensitivity.py", "output": "runs/W/W5/sensitivity.json", "compute": "up to 23 fits, about 1 to 2 hours"},
            {"stage": "W6", "name": "Model expansion and comparison", "replaces": "new", "evidence_class": "exploratory", "gate": "G7",
             "depends_on": ["W1", "W2", "W3", "W4", "W5"], "claims": [], "entrypoint": "runs/w6_expand.py", "output": "runs/W/W6/expansion.json", "compute": "about 3 to 10 hours typical, up to about 24 hours (plus up to 8 hours for F7)"},
        ],
        "execution": {
            "mode": "command",
            "entrypoint": {"argv": ["uv", "run", "--project", "runs", "python", "runs/w_run.py", "--stage", "all"], "cwd": "."},
            "declared_inputs": [ZIP],
            "declared_evaluator_artifacts": [ECI_CODE, CHECKS, SENS, SBC, COMPARE, MODELS, PRIOR_GRID],
            "required_outputs": [{"path": "runs/W/workflow.json", "kind": "metrics"},
                                 {"path": "runs/W/W1/prior_predictive.json", "kind": "metrics"},
                                 {"path": "runs/W/W2/reproduction.json", "kind": "metrics"},
                                 {"path": W2_NC, "kind": "posterior"},
                                 {"path": "runs/W/W3/calibration.json", "kind": "metrics"},
                                 {"path": "runs/W/W4/ppc.json", "kind": "metrics"},
                                 {"path": "runs/W/W4/evaluation_report.pdf", "kind": "figure"},
                                 {"path": "runs/W/W5/sensitivity.json", "kind": "metrics"},
                                 {"path": "runs/W/W5/fig_sensitivity.png", "kind": "figure"},
                                 {"path": "runs/W/W6/expansion.json", "kind": "metrics"}],
        },
        "lineage_policy": {"allowed_relations": ["baseline", "replication", "ablation", "negative_control", "sensitivity", "parameter_variation", "alternative_hypothesis", "technical_retry"]},
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
        "systems_compared": ["ECI predictive distribution (W2 seed-12345 fit; the C3 verdict is defined on this model)", "exploratory add-on: the same coverage under each adequate expansion of W6, if any", "EEE-vs-EEE agreement on the same model x benchmark (noise floor)",
                             "same-upstream pairs (for example ARC Prize, Terminal-Bench, Mercor APEX) as the crosswalk positive control"],
        "fixed_factors": ["W2 posterior", "normalisation", "frozen maps and source classes"],
        "variable_factors": ["pair class: same-upstream / independent / upstream-unknown", "Epoch's own score for the pair in the fit or not"],
        "metrics": ["crosswalk counts by class and exclusion reason", "audit errors among 50 random matched pairs, with Clopper-Pearson 95% upper bound",
                    "same-upstream median and 90th percentile absolute difference", "90% coverage on independent pairs with a 90% model-cluster bootstrap interval (2,000 resamples)",
                    "coverage split by in-fit / not-in-fit and by benchmark", "EEE-vs-EEE agreement rate", "signed mean difference (EEE minus ECI predictive mean) per benchmark",
                    "sensitivity: coverage after removing independent pairs whose raw score equals Epoch's to 3 decimals; coverage excluding pairs with Pareto k > 0.7",
                    "exploratory: coverage on the same pairs under each adequate W6 expansion, reported beside the verdict"],
        "setup_details": ("Stage a (no ECI predictions loaded): download objects, verify sha256 against the manifest, build "
                          "runs/B4/collection_screen.csv, benchmark_map.csv, model_map.csv and source_class.csv by the rules in "
                          "M9, classify every result, aggregate to pairs, draw the audit sample, audit, and freeze the maps "
                          "(digests in runs/freeze.json). Stage b (only after the audit passes): join the W2 posterior, "
                          "compute PIT, coverage, agreement and bias; if W6 has adequate expansions, repeat the coverage under each (exploratory). One wrapper runs both: runs/b4_run.py --stage a|b|all."),
        "seeds": 1,
        "success_criterion": "C3 decision rule with its preconditions: audit errors <= 2 of 50, same-upstream median absolute difference <= 0.02, at least 100 independent pairs over 20 model groups and 5 benchmarks, and coverage >= 0.80 with agreement not below 0.80.",
        "minimum_effect_size": "coverage thresholds 0.80 and 0.65; agreement threshold 0.80",
        "failure_interpretation": ("More than 2 audit errors stop stage b until one round of fixes and a fresh audit sample. Low "
                                   "coverage with agreement >= 0.80 falsifies C3; agreement below 0.80 gives the verdict "
                                   "`harness-limited`."),
        "expected_output_artifact": "runs/B4/transfer.json",
        "compute_budget": "Download and parse 122,861 JSON objects (2.2 GB); no new fits. 2 to 4 hours wall-clock, mostly I/O, plus the manual mapping and audit.",
        "dependencies": ["W"],
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
            "declared_inputs": [ZIP, EEE_MAN, {"path": W2_NC, "role": "posterior (stage b only)", "snapshot": "digest-at-start"},
                                {"path": "runs/W/W6/expansion.json", "role": "adequate set for the exploratory add-on (stage b only)", "snapshot": "digest-at-start"}],
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
        "why_this_block_exists": "Fits the ECI model to the EEE-matched matrix and compares rankings and intervals with W2.",
        "dataset_split_task": ("Matched-independent pairs from B4a, one row per (model group, benchmark) taking the highest "
                               "normalised score across sources, then Epoch's inclusion rule (at least 4 benchmarks and at "
                               "least 4 with a score in [0.1, 0.9])."),
        "systems_compared": ["ECI on Epoch data (W2)", "ECI on EEE-matched data", "exploratory: the best adopted W6 expansion on the EEE-matched data, if W6 adopted one"],
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
        "compute_budget": "2 to 3 fits, about 10 minutes; one more fit of the adopted expansion if W6 adopted one",
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
                                {"path": W2_NC, "role": "W2 posterior for comparison", "snapshot": "digest-at-start"}],
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
        "dataset_split_task": ("Clip and anchor variants use the W2a fit input. Inclusion and ceiling variants must rebuild the "
                               "input with prepare_benchmark_data(zip, ...), so they are compared with W2b (the loader-input "
                               "baseline), not W2a."),
        "systems_compared": ["performance_clip_eps 1e-4 / 1e-2", "min_mid_range_benchmarks_per_model 3 / 6",
                             "score_ceiling set to 1.0 for every benchmark (benchmark_metadata override)",
                             "anchors swapped for two other models with 20+ scores (no refit: re-anchor the P0 draws; rank and interval width only)"],
        "fixed_factors": ["priors", "likelihood", f"sampler as W5 (draws={W5_DRAWS})"],
        "variable_factors": ["one handling choice per run"],
        "metrics": ["C1 metrics S1-S4 against the matching baseline, on models present in both fits; models added or dropped by the variant"],
        "setup_details": "Same pipeline and metric code as the W5 grid refits. Metadata overrides are passed as DataFrames; nothing under ext/ is edited.",
        "seeds": 1,
        "success_criterion": "S1-S4 pass, reported per choice.",
        "minimum_effect_size": "as C1",
        "failure_interpretation": "Report which handling choice matters; does not change C1's verdict.",
        "expected_output_artifact": "runs/B6/handling.json",
        "compute_budget": "6 fits (5 variants and a W2b-input baseline at W5 settings), about 30 minutes",
        "dependencies": ["W"],
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
    "frozen_at": "2026-11-13, before any refit or power-scaling screen (revised the same day by pre-run review; restructured into block W on 2026-11-18, which added only the exploratory entry PR and the S5-targeted refits; see the Revision Log in experiment-plan.md)",
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
    "positive_control_W3": {"PC": {"tau_alpha": ["ln 0.05", 0.1]}},
    "reference_prior_W1_exploratory": {
        "PR": {"capability": "Normal(mu_c, s); mu_c ~ Normal(0, 2)",
               "difficulty": "ZeroSumNormal(sigma = s * sqrt(K / (K - 1))), K = 57, so its marginal SD is s",
               "s": "LogNormal(ln 2, 0.5), one scale shared by capability and difficulty",
               "unchanged": "tau_alpha, sigma_median, tau_sigma, log_slope and sigma are as in the baseline"},
        "status": ("exploratory. Fitted once in W5 (our reimplementation, only if the equivalence check EQ passed), scored with S1-S4 against "
                   "P0 and reported, and reused as candidate F6 in W6. It never enters the C1 decision rule."),
        "plausibility_criterion": ("Pre-declared in W1 on 1,000 datasets simulated on the 2,879 observed (model, benchmark) cells with "
                                   "numpy default_rng(20261113): mean share of scores in [0.1, 0.9] >= 0.40; at least 95% of datasets with that share >= 0.15; "
                                   "mean share at the clip bounds (<= 0.001 or >= 0.999) <= 0.35. If PR fails, it is dropped from W5 and W6 and the failure is reported; it is not retuned."),
    },
    "jeffreys_priors_exploratory": {
        "common": {"unchanged": "Epoch's model: tau_alpha, sigma_median, tau_sigma, log_slope and sigma as in the baseline; capability Uniform(-50, 50); difficulty flat on the sum-to-zero subspace with each coordinate bounded to [-50, 50] (no Jeffreys term on difficulty)",
                   "added": ("one potential, sum over models m of [1/2 log I_m(c_m) - log Z_m], with I_m(c) = sum over the cells observed for model m of a_b^2 g(a_b (c - d_b), kappa_b) "
                             "and Z_m = integral over [-50, 50] of sqrt(I_m(c)) dc, so that c_m has the proper density sqrt(I_m(c)) / Z_m on [-50, 50] given the slopes, difficulties and noise; "
                             "Z_m by a fixed-node composite Gauss-Legendre rule; g is evaluated from the unclipped eta and ignores the clipping of y in the likelihood"),
                   "reference": "Warm (1989), Psychometrika 54, 427-450: under a Jeffreys ability prior the posterior mode is the weighted likelihood estimate"},
        "J1": {"g": "[mu (1 - mu)]^2 kappa^2 [psi1(mu kappa) + psi1((1 - mu) kappa)], mu = sigmoid(eta), psi1 the trigamma function (Beta information about eta)"},
        "J2": {"g": "mu (1 - mu), mu = sigmoid(eta) (Bernoulli information, the textbook item-response form; Jeffreys only heuristically for the Beta likelihood)"},
        "status": ("exploratory, added after the freeze at the user's request (Revision Log R26). Each of J1 and J2 is fitted once in W5 at the PR settings with our "
                   "reimplementation (runs/lib/jeffreys_norm.py), scored with S1-S4 against P0 and reported beside PR. They never enter the C1 decision rule, a gate or any "
                   "confirmatory verdict, and the entries P1-P10, X1, X2 and PR above are unchanged. They replace a first, unnormalised form J that was rejected because its "
                   "joint prior is not normalisable in the slope scale (results/W/W1J/summary_J_first_form.md)."),
        "W1_check": "the W1 quantities for J1 and J2 by direct simulation (1,000 datasets; hyperparameters, slopes, noise and difficulties as in W1's Epoch arm, each capability by inverse CDF from its normalised density on an 8,001-point grid); descriptive for J1 and J2, which go to W5 whatever the outcome",
    },
    "s5_targeted_refits_exploratory": ("For each hyperprior that S5 flags (the S5 pass rule applied to its own psens): refit with the power a = 0.5 and a = 2, "
                                       "using LogNormal(mu + s^2 (1 - a) / a, s / sqrt(a)); at most 6 such fits in total. Scored with S1-S4, reported, "
                                       "never part of the C1 verdict."),
    "s5_followup_refits": ("Only if S5 flags a hyperprior LogNormal(mu, s): refit with LogNormal(mu + s^2 (1 - a) / a, s / sqrt(a)) "
                           "for a = 0.8 and a = 1.25, which is that prior raised to the power a. For s = 0.5: mu + 0.0625 with "
                           "sigma 0.559, and mu - 0.05 with sigma 0.447."),
    "sampler": {"chains": 4, "target_accept": 0.95, "draws_per_chain": W5_DRAWS, "seed": 12345, "noise_floor_seed": 22345},
    "note": ("P8 and P9 scales are on the raw (pre-anchor) scale, where the geometric-mean slope is 1 and difficulties sum to 0. "
             "Guard fixed before any fit: let s0 be the SD across the 256 models of the posterior-mean raw capability in W2 seed "
             "12345. If s0 > 3, P8 uses Normal(0, 2 x s0) for capability and ZeroSumNormal(2 x s0) for difficulty. The published "
             "draws give s0 = 2.62, so the guard is not expected to trigger."),
}
(OUT / "prior-grid.json").write_text(json.dumps(grid, indent=2) + "\n")
print(f"ok: wrote claim-map.json, run-blocks.json, prior-grid.json to {OUT}")
