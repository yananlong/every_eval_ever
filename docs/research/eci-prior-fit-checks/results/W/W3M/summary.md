# W3M summary (INTERIM)

Written 2026-11-18 18:57:16. Replicates used per generator: null 22 of 199, 2d 0 of 20, offset 0 of 20, shape 0 of 20, disp 0 of 20, drift 0 of 20.

Thinning to ESS: True. Caveat: truth drawn from the W2 posterior and the refit uses y_sim only; ranks are not exactly uniform even when everything is exact (selftest C). gamma p-values come from 20,000 simulated uniform samples, so the smallest reportable p is 5e-5; the Bonferroni column is p x P and floors at 5e-5 x P. Pearson chi-squared has fewer than 5 expected per bin when R < 50 and is then only indicative.

## Generator null (22 replicates)

| Quantity | P | gamma p (scalar) or min gamma p x P | gamma flagged | chi2 p (scalar) or min chi2 p | chi2 flagged | central 90% share | share u<0.05 / u>0.95 | mean u | median stride |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ECI (non-anchor models) | 254 | 0.0508 | 0 | 1.74e-05 | 1 | 0.87 | 0.08 / 0.06 | 0.49 | 1 |
| EDI (benchmarks) | 57 | 0.00285 | 4 | 1.73e-07 | 3 | 0.85 | 0.09 / 0.06 | 0.48 | 1 |
| slope | 57 | 0.00285 | 23 | 5.44e-27 | 24 | 0.73 | 0.07 / 0.20 | 0.59 | 1 |
| sigma | 57 | 0.00285 | 6 | 1.61e-08 | 4 | 0.86 | 0.05 / 0.09 | 0.53 | 1 |
| hyperparameters | 3 | 0.123 | 0 | 0.0352 | 0 | 0.79 | 0.08 / 0.14 | 0.60 | 1 |
| class summaries | 6 | 0.0003 | 2 | 1.16e-13 | 1 | 0.79 | 0.05 / 0.17 | 0.61 | 1 |
| joint log-likelihood | 1 | 0.138 | | 0.628 | | 0.95 | 0.05 / 0.00 | 0.38 | 1 |
| per-benchmark log-likelihood | 57 | 0.00285 | 1 | 5.65e-11 | 2 | 0.88 | 0.06 / 0.06 | 0.50 | 1 |
| mean residual | 1 | 0.573 | | 0.628 | | 0.86 | 0.09 / 0.05 | 0.47 | 1 |
| per-benchmark mean residual | 57 | 0.616 | 0 | 0.00376 | 0 | 0.89 | 0.06 / 0.05 | 0.50 | 1 |
| Pearson dispersion | 1 | 5e-05 | | 9.23e-13 | | 0.68 | 0.32 / 0.00 | 0.16 | 1 |

## Reading (interim, written by hand; 22 of 199 G-null replicates, no misfit replicate finished)

- Toy validation (`selftest.json`, numpy only): with exact draws the gamma test rejects at about 0.05 (0.02 to 0.07 across quantities, 200 repeats of R = 100); thinning matches the theoretical stride; a posterior equal to the prior passes on every parameter and fails only on the log-likelihood (p below 1e-4); an overconfident posterior fails on mu, log-likelihood and residual; and in the conjugate toy where the truth is drawn from the posterior and the refit sees the simulated data alone, exact inference gives non-uniform ranks (mean u 0.63, analytic 0.635) with a central 90% share of 0.89 to 0.90.
- Joint log-likelihood: gamma p 0.138, chi-square p 0.63; central 90% share 0.95, share below 0.05 is 0.05, mean u 0.38. No evidence of non-uniformity at 22 replicates, and little power at this size.
- Parameters: ECI shows no gamma-flagged element (0 of 254); EDI 4 of 57, sigma 6 of 57 and slope 23 of 57 are flagged at Bonferroni 0.01 / P, with slope ranks high (20% above 0.95, central 90% share 0.73). The log-slope SD (a class summary) and the Pearson dispersion (gamma p 5e-5, 32% of ranks below 0.05) deviate most. These are the quantities whose posterior is pulled by an informative prior or by the fit to the same data, which is where the posterior-draw design is expected to depart from uniformity (M13), so they are descriptive and not a finding about the sampler. Posterior SBC is the check that separates the two.
- Mean residual: gamma p 0.57, chi-square p 0.63; per-benchmark mean residual 0 of 57 flagged.
- With R = 22 the chi-square test has 2.2 expected per bin and is only indicative; the gamma p-values floor at 5e-5.
