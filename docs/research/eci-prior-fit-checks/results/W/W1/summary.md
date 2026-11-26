# W1 summary: prior predictive check (no gate)

1,000 simulated datasets per prior on the 2,879 observed (model, benchmark) cells (`prior_predictive.json`, `fig_prior_predictive.png`).

| Prior | Mean share at the clip bounds | Mean share in [0.1, 0.9] | 5th to 95th percentile of the mid-range share | Datasets with mid-range share at least 0.15 |
| --- | --- | --- | --- | --- |
| Epoch's flat priors | 0.888 | 0.049 | 0.034 to 0.075 | 3 of 1,000 |
| Reference prior PR | 0.261 | 0.453 | 0.210 to 0.712 | 986 of 1,000 |

Epoch's priors reproduce the review's figures (0.89 and 0.05). Shares of cells whose pre-noise mean lies in [0.1, 0.9]: 0.053 (Epoch), 0.494 (PR); cells with $\lvert a(c - d)\rvert > 6.9$: 0.843 (Epoch), 0.134 (PR).

Pre-declared PR criterion: mean mid-range share at least 0.40 (0.453, met); at least 950 of 1,000 datasets at or above 0.15 (986, met); mean clip-bound share at most 0.35 (0.261, met). **PR passes** and is used in W5 and W6. Epoch's priors fail all three, which is descriptive.
