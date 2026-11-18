# Deviations from the plan

Each entry: what changed, why, its effect. No registered threshold or rule was changed.

1. **Sampler for our models (M12).** The plan says our models are sampled by our own NUTS call. On the owner's instruction F0 uses Epoch's own sampling routine: `fit_bayesian_eci` is called with `eci.bayesian.build_bayesian_model` replaced in memory by our builder (pilot with a diagonal mass matrix, then a dense mass matrix, Epoch's draw ladder and cold fallback). For expansions and PR the same call is used with `_FREE_VARS` and `_DIAGNOSTIC_VARS` extended in memory for the added variables. Effect: EQ tests the same sampler on both sides, so a fit difference can only come from the model; expansion fits use the pilot and dense stages, which Epoch's README says are about ten times cheaper per effective sample than the cold stage.
2. **Misfit replicate positions (M4).** "As G-null" does not say which posterior draw a misfit replicate uses. Replicate $r$ of a generator with $R_g$ replicates uses the pooled draw at position floor(r S / R_g) (199 for G-null, 20 for each misfit generator), so the 20 misfit replicates spread over all chains instead of clustering in the first draws.
3. **K-fold folds from Epoch's code (M14).** See the W6 entry when written.
