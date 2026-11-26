# W5-J summary: normalised Jeffreys priors J1 and J2 against P0, beside PR (exploratory, outside C1)

Fits at the W5 settings of the PR entry (4 chains, 4,000 draws per chain, target acceptance 0.95, seed 12345). S1-S4 are scored against P0 as for a grid entry.

## Fit status

| Fit | Converged | Last attempt |
| --- | --- | --- |
| PR | True | {'stage': 'pilot', 'tune': 500, 'draws': 4000, 'divergences': 0, 'max_rhat': 1.0011571217612083, 'min_ess': 7625.03470967864} |

## S1-S4 against P0

| Fit | Stratum | S1 Spearman | S2 count (limit) | S3 count (limit) | S4 pass |
| --- | --- | --- | --- | --- | --- |
| PR | all | 0.9997 | 64 (12) | 58 (12) | True |
| PR | frontier | 0.9970 | 1 (1) | 0 (1) |  |
| PR | sparse | 0.9982 | 32 (3) | 33 (3) |  |
| PR | dense | 0.9998 | 32 (9) | 25 (9) |  |

## ECI shift and interval width against P0 (non-anchor models)

| Fit | Stratum | Mean absolute shift | Largest absolute shift | Median 90% width, P0 | Median 90% width | Median width ratio |
| --- | --- | --- | --- | --- | --- | --- |
| PR | all | 2.994 | 20.959 | 5.28 | 5.34 | 1.014 |
| PR | frontier | 0.891 | 1.956 | 5.51 | 5.88 | 1.063 |

## Top 10

- PR: same set as P0: True; same order: False; entered: none; left: none; rank change of each P0 top-10 model (P0 order): [0, 0, 0, 1, -1, 0, 0, 0, 0, 0].
