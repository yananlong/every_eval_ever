# W1-J1 and W1-J2 summary: normalised capability-only Jeffreys priors (exploratory, no gate)

J1 and J2 replace the first form J, which was rejected (see "Why the first form J was revised" below and `summary_J_first_form.md`). Both keep Epoch's model unchanged and add one potential, $\sum_m [\tfrac12\log I_m(c_m) - \log Z_m]$ with $Z_m = \int_{-50}^{50}\sqrt{I_m(c)}\,dc$, so that each capability has the proper conditional density $\sqrt{I_m(c)}/Z_m$ on $[-50, 50]$ given the slopes, difficulties and noise. J1 uses the Beta information $g = [\mu(1-\mu)]^2\kappa^2[\psi_1(\mu\kappa) + \psi_1((1-\mu)\kappa)]$; J2 uses the Bernoulli information $g = \mu(1-\mu)$, the textbook item-response form, which is Jeffreys only heuristically for the Beta likelihood. Under a Jeffreys ability prior the posterior mode is the weighted likelihood estimate (Warm, 1989, Psychometrika 54, 427-450).

## Prior predictive table (1,000 datasets on the 2,879 cells, direct simulation)

Hyperparameters, slopes and noise are drawn from Epoch's priors and the difficulties from centred uniforms, exactly as in W1; each capability is drawn from its normalised density by inverse CDF on an 8,001-point grid over $[-50, 50]$ (`prior_predictive_J1J2.json`, `fig_prior_predictive_J1J2.png`). The W1 numbers for Epoch's priors and PR are regenerated from the W1 seeds and match the stored values.

| Prior | Mean share at the clip bounds | Mean share in [0.1, 0.9] | 5th to 95th percentile of the mid-range share | Datasets with mid-range share at least 0.15 | Share of cells with pre-noise $\mu$ in [0.1, 0.9] | Share of cells with $\lvert\eta\rvert > 6.9$ |
| --- | --- | --- | --- | --- | --- | --- |
| Epoch's flat priors | 0.888 | 0.049 | 0.034 to 0.075 | 3 of 1,000 | 0.053 | 0.843 |
| Reference prior PR | 0.261 | 0.453 | 0.210 to 0.712 | 986 of 1,000 | 0.494 | 0.134 |
| J1 (Beta information) | 0.878 | 0.057 | 0.037 to 0.086 | 3 of 1,000 | 0.061 | 0.833 |
| J2 (Bernoulli information) | 0.828 | 0.092 | 0.069 to 0.118 | 22 of 1,000 | 0.099 | 0.780 |

Against the PR criterion (descriptive for J1 and J2, which go to W5 whatever W1 shows): J1 fails all three (mean mid-range share 0.057 against at least 0.40; 3 datasets against at least 950; mean clip-bound share 0.878 against at most 0.35), and so does J2 (0.092; 22; 0.828). Both are close to Epoch's flat priors. The reason is that the difficulties keep Epoch's flat prior on $[-50, 50]$, and each capability is placed where its own information is large, which is near the difficulties of the benchmarks it was run on; those are spread over the whole box, so most (model, benchmark) gaps are large. The mean absolute capability is about 24 under both (share beyond 25 of about 0.5).

## Verification of the builders (`checks_normalised.json`)

Both variants pass every check.

- With the potential removed, the model's log density and gradient equal F0's exactly at 50 random points.
- The potential equals an independent numpy and scipy computation, with $Z_m$ from `scipy.integrate.quad`, at 20 points: maximum relative error $2.2\times10^{-12}$ (J1) and $1.7\times10^{-12}$ (J2). The fixed-node $Z_m$ (composite Gauss-Legendre, 304 nodes) agrees with `quad` to $3.6\times10^{-11}$ (J1) and $1.4\times10^{-10}$ (J2) over 120 model-point pairs. The rule is accurate for difficulties within about $\pm 16$ (the W2 posterior means span $-9.5$ to $3.9$) and slopes up to about 6.
- The gradient of the potential matches a 4-point central finite difference along 18 random directions: maximum relative error $8.9\times10^{-9}$ (J1) and $9.2\times10^{-11}$ (J2).
- For models with the other parameters fixed, $\sqrt{I_m(c)}/Z_m$ integrates to 1 over $[-50, 50]$ to $3\times10^{-11}$ (J1) and $9\times10^{-12}$ (J2).
- Slope pressure is gone. The conditional density of $c_m$ integrates to one, so the prior marginal of the hyperparameters, slopes, noise and difficulties is exactly Epoch's. At fixed $(c, d, \kappa, w)$ with $\log a = \tau_\alpha w$ the potential has no upward trend in $\tau_\alpha$ (J1 falls from $-1130$ at 0.1 to $-1179$ and is flat from 4 to 32; J2 falls from $-878$ to $-1244$), where the first form rose to $+15{,}000$. Beyond $\tau_\alpha \approx 2$ the slopes exceed the quadrature rule's range, so those entries are indicative.
- Cost of one log density plus gradient on the real data: F0 0.33 ms, J1 13.5 ms (41 times F0), J2 3.2 ms (9 times F0).

## Why the first form J was revised

The first form added the unnormalised $\tfrac12\sum_m\log I_m + \tfrac12\sum_b\log I_b$ on both capabilities and difficulties. It is not normalisable in the slope scale: with $\log a = \tau_\alpha w$ fixed, its log density in $\tau_\alpha$ rose from 437 at 0.25 to 15,280 at 32 (`propriety.json`, `fig_J_propriety.png`), and PyMC NUTS on that prior failed with slopes near $e^{358}$ in both seeds tried. Its information also tends to 1 in the tails of $c$, so the conditional prior is bounded below there (`checks.json`). The user chose to replace it by J1 and J2.
