# W3M summary (final)

Written 2026-11-20 15:23:37. Replicates used per generator: null 180 of 180.

Thinning to ESS: True. Caveat: truth drawn from the W2 posterior and the refit uses y_sim only; ranks are not exactly uniform even when everything is exact (selftest C). 32 W3 fits plus 148 W4d refits. gamma p-values come from 20,000 simulated uniform samples, so the smallest reportable p is 5e-5; the Bonferroni column is p x P and floors at 5e-5 x P. Pearson chi-squared has fewer than 5 expected per bin when R < 50 and is then only indicative.

## Generator null (180 replicates)

| Quantity | P | gamma p (scalar) or min gamma p x P | gamma flagged | chi2 p (scalar) or min chi2 p | chi2 flagged | central 90% share | share u<0.05 / u>0.95 | mean u | median stride |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ECI (non-anchor models) | 254 | 0.0127 | 0 | 5.87e-15 | 18 | 0.88 | 0.06 / 0.05 | 0.49 | 1 |
| EDI (benchmarks) | 57 | 0.00285 | 20 | 1.38e-68 | 16 | 0.87 | 0.08 / 0.06 | 0.48 | 1 |
| slope | 57 | 0.00285 | 46 | 6.7e-271 | 45 | 0.75 | 0.06 / 0.19 | 0.58 | 1 |
| sigma | 57 | 0.00285 | 30 | 2.59e-46 | 27 | 0.87 | 0.05 / 0.07 | 0.53 | 1 |
| hyperparameters | 3 | 0.00015 | 2 | 5.73e-17 | 2 | 0.86 | 0.02 / 0.12 | 0.63 | 1 |
| class summaries | 6 | 0.0003 | 6 | 6.7e-133 | 4 | 0.77 | 0.06 / 0.17 | 0.60 | 1 |
| joint log-likelihood | 1 | 0.0001 | | 0.000839 | | 0.87 | 0.11 / 0.02 | 0.39 | 1 |
| per-benchmark log-likelihood | 57 | 0.00285 | 16 | 1.38e-45 | 13 | 0.88 | 0.06 / 0.06 | 0.51 | 1 |
| mean residual | 1 | 0.36 | | 0.397 | | 0.87 | 0.04 / 0.08 | 0.51 | 1 |
| per-benchmark mean residual | 57 | 0.0598 | 0 | 0.000174 | 1 | 0.89 | 0.05 / 0.05 | 0.50 | 1 |
| Pearson dispersion | 1 | 5e-05 | | 7.99e-63 | | 0.66 | 0.34 / 0.01 | 0.20 | 1 |
