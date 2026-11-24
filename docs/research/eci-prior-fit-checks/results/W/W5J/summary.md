# W5-J summary: normalised Jeffreys priors J1 and J2 against P0, beside PR (exploratory, outside C1)

Fits at the W5 settings of the PR entry (4 chains, 4,000 draws per chain, target acceptance 0.95, seed 12345). S1-S4 are scored against P0 as for a grid entry.

## Fit status

| Fit | Converged | Last attempt |
| --- | --- | --- |
| J2 | True | {'stage': 'pilot', 'tune': 500, 'draws': 4000, 'divergences': 0, 'max_rhat': 1.00139131833373, 'min_ess': 3506.834032333641} |
| PR | True | {'stage': 'pilot', 'tune': 500, 'draws': 4000, 'divergences': 0, 'max_rhat': 1.0010125213188805, 'min_ess': 7361.7398228973425} |

## S1-S4 against P0

| Fit | Stratum | S1 Spearman | S2 count (limit) | S3 count (limit) | S4 pass |
| --- | --- | --- | --- | --- | --- |
| J2 | all | 0.9999 | 40 (12) | 21 (12) | True |
| J2 | frontier | 0.9985 | 0 (1) | 0 (1) |  |
| J2 | sparse | 0.9997 | 21 (3) | 16 (3) |  |
| J2 | dense | 0.9999 | 19 (9) | 5 (9) |  |
| PR | all | 0.9997 | 62 (12) | 60 (12) | True |
| PR | frontier | 0.9955 | 0 (1) | 0 (1) |  |
| PR | sparse | 0.9986 | 32 (3) | 34 (3) |  |
| PR | dense | 0.9998 | 30 (9) | 26 (9) |  |

## ECI shift and interval width against P0 (non-anchor models)

| Fit | Stratum | Mean absolute shift | Largest absolute shift | Median 90% width, P0 | Median 90% width | Median width ratio |
| --- | --- | --- | --- | --- | --- | --- |
| J2 | all | 1.777 | 15.470 | 5.24 | 5.13 | 0.980 |
| J2 | frontier | 0.174 | 0.643 | 5.42 | 5.47 | 1.010 |
| PR | all | 3.933 | 31.750 | 5.24 | 5.28 | 1.005 |
| PR | frontier | 0.765 | 1.787 | 5.42 | 5.69 | 1.063 |

## Top 10

- J2: same set as P0: True; same order: True; entered: none; left: none; rank change of each P0 top-10 model (P0 order): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0].
- PR: same set as P0: True; same order: True; entered: none; left: none; rank change of each P0 top-10 model (P0 order): [0, 0, 0, 0, 0, 0, 0, 0, 0, 0].
