# First form J (rejected): unnormalised Jeffreys potential on capability and difficulty

The first form J added one unnormalised potential to Epoch's model. The builder is verified (`checks.json`). The prior predictive check of J could not be run, because the prior as defined is not normalisable (`propriety.json`, `fig_J_propriety.png`). No draws were obtained and no figure of the three priors exists.

## Prior predictive table (1,000 datasets on the 2,879 cells)

| Prior | Mean share at the clip bounds | Mean share in [0.1, 0.9] | Datasets with mid-range share at least 0.15 |
| --- | --- | --- | --- |
| Epoch's flat priors (W1) | 0.888 | 0.049 | 3 of 1,000 |
| Reference prior PR (W1) | 0.261 | 0.453 | 986 of 1,000 |
| Jeffreys prior J | not defined | not defined | not defined |

## Verification of the builder

All four checks pass (`checks.json`).

- (a) With the potential removed, the J model's log density and gradient equal F0's at 50 random points exactly. With the likelihood also removed, the log density equals F0's minus the Beta log-likelihood (maximum absolute error $8\times10^{-10}$ at 10 points).
- (b) The potential equals an independent numpy and scipy computation of $g$ at 20 points, maximum relative error $3.7\times10^{-16}$ (and $2.2\times10^{-16}$ at 20 more points with $\lvert\eta\rvert$ up to 295). The PyTensor $g$ matches the formula to $10^{-15}$. A Monte Carlo estimate of $\operatorname{Var}(\text{score in }\eta)$ from $10^6$ draws of `scipy.stats.beta` agrees with $g$ to a relative error of at most 0.002 at six $(\mu, \kappa)$ pairs, which is the Monte Carlo error. The trigamma used (recurrence to an argument of at least 7, then the asymptotic series) matches `scipy.special.polygamma` to $1.7\times10^{-14}$ over 4,014 arguments from 0 to $10^{12}$. PyTensor's own `tri_gamma` has a working gradient but runs in Python object mode (about 0.2 s per log density and gradient, against 2 ms), so it is not used.
- (c) The gradient of the potential agrees with central finite differences along 18 random directions, maximum relative error $1.4\times10^{-8}$.
- (d) Tails. For one model with the others fixed, $\tfrac12\log I_m(c)$ does not decay in the tails. It is a bump of height about 0.8 near $\eta = 0$ on a plateau at $\tfrac12\log\sum_b a_b^2$, reached to within $1.5\times10^{-7}$ for $\lvert c\rvert \ge 30$, because $g \to 1$ as $\lvert\eta\rvert \to \infty$ (a Beta shape below 1 carries information about $\eta$ that does not fade). The conditional prior on $(c, d)$ is therefore bounded below in the tails and proper only because of Epoch's box on $c$ and $d$.

## Why the prior predictive check is not available

1. J as defined is not normalisable in the slope scale. Writing $\log a = \tau_\alpha w$ with $w$ fixed, the potential grows about linearly in $\tau_\alpha$ (about 480 per unit at large $\tau_\alpha$) while the LogNormal hyperprior on $\tau_\alpha$ falls only like $(\ln\tau_\alpha)^2$. When $\eta$ saturates, $g \to 1$, so $\sum_m \tfrac12\log I_m \to \sum_m \log$ (root-mean-square slope over the benchmarks of model $m$), which is larger than the geometric mean (fixed at 1 by the zero-sum constraint) and grows with the spread of the slopes. The log density in $\tau_\alpha$ at fixed $(c, d, \kappa, w)$ is 437 at $\tau_\alpha = 0.25$, 661 at 1, 3,913 at 8 and 15,280 at 32 (`propriety.json`).
2. PyMC NUTS on the J prior without the likelihood (1 chain, 1,000 tuning steps planned) fails during tuning with a bad initial energy in both seeds tried. The chain has by then moved to log slopes near 358 (slopes of order $e^{358}$), where the potential overflows to $+\infty$.
3. Separately, NUTS on Epoch's prior alone, with no potential, already has a divergence at every iteration (200 of 200), because of the hard box on the difficulties. Epoch's prior predictive in W1 is therefore a direct simulation, and J has no direct simulation.

The user decided to replace J by the normalised capability-only variants J1 and J2 (`summary.md`).
