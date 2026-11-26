# W3M summary (final)

Written 2026-11-21 20:37:53. Replicates used per generator: null 192 of 192.

Thinning to ESS: True. Caveat: truth drawn from the W2 posterior and the refit uses y_sim only; ranks are not exactly uniform even when everything is exact (selftest C). 32 W3 fits plus 148 W4d refits. gamma p-values come from 20,000 simulated uniform samples, so the smallest reportable p is 5e-5; the Bonferroni column is p x P and floors at 5e-5 x P. Pearson chi-squared has fewer than 5 expected per bin when R < 50 and is then only indicative.

## Generator null (192 replicates)

| Quantity | P | gamma p (scalar) or min gamma p x P | gamma flagged | chi2 p (scalar) or min chi2 p | chi2 flagged | central 90% share | share u<0.05 / u>0.95 | mean u | median stride |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ECI (non-anchor models) | 254 | 0.0127 | 0 | 1.05e-10 | 8 | 0.88 | 0.07 / 0.05 | 0.49 | 1 |
| EDI (benchmarks) | 57 | 0.00285 | 15 | 5.11e-59 | 17 | 0.86 | 0.08 / 0.06 | 0.49 | 1 |
| slope | 57 | 0.00285 | 41 | 2.52e-301 | 40 | 0.76 | 0.06 / 0.18 | 0.58 | 1 |
| sigma | 57 | 0.00285 | 30 | 5.38e-59 | 28 | 0.87 | 0.05 / 0.08 | 0.54 | 1 |
| hyperparameters | 3 | 0.00015 | 2 | 6.17e-17 | 2 | 0.88 | 0.01 / 0.11 | 0.64 | 1 |
| class summaries | 6 | 0.0003 | 5 | 2.62e-136 | 4 | 0.77 | 0.04 / 0.19 | 0.61 | 1 |
| joint log-likelihood | 1 | 5e-05 | | 4.57e-07 | | 0.88 | 0.09 / 0.03 | 0.38 | 1 |
| per-benchmark log-likelihood | 57 | 0.00285 | 15 | 7.14e-30 | 15 | 0.88 | 0.06 / 0.06 | 0.50 | 1 |
| mean residual | 1 | 0.00685 | | 0.0018 | | 0.86 | 0.05 / 0.08 | 0.54 | 1 |
| per-benchmark mean residual | 57 | 0.0142 | 0 | 0.00072 | 0 | 0.89 | 0.05 / 0.06 | 0.51 | 1 |
| Pearson dispersion | 1 | 5e-05 | | 7.51e-95 | | 0.59 | 0.41 / 0.00 | 0.17 | 1 |
