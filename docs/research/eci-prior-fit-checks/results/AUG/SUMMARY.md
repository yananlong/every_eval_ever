# Augmented input: every distinct EEE source per cell (exploratory, beyond plan; deviations entry 14)

Results hold under Epoch's model. P0 is Epoch's data fit `runs/W/W2/seed12345.nc`.

## Input (`input_report.json`)
- The crosswalk covers 688 of 2,879 cells (23.9%).
- After dropping same-upstream rows and relays (a value within 0.0015 of one already kept), 365 cells keep a distinct extra value: 584 rows, of which 447 are independent and 137 upstream-unknown.
- The other 323 covered cells only repeat Epoch's number.
- The independent-only set has 269 cells and 447 rows.

## Source disagreement against P0's noise, no refit (`diag_p0.json`)
| Pairs | n pairs (cells) | Residual correlation, Epoch vs EEE value | Model-true 90% range | Disagreement / model noise | Model-true 90% range |
|---|---|---|---|---|---|
| All | 584 (365) | 0.43 | -0.06 to 0.06 | 0.77 | 0.88 to 1.12 |
| Independent | 447 (269) | 0.45 | -0.09 to 0.07 | 0.69 | 0.86 to 1.17 |
| Independent, no GPQA diamond | 126 (122) | 0.45 | -0.13 to 0.15 | 0.74 | 0.78 to 1.24 |

- Outside GPQA diamond, independent values sit 3.4 points below Epoch's value on average; 42% of them are higher.
- Older benchmarks (BBH, ARC AI2, OpenBookQA, PIQA) disagree 1.5 to 2.9 times the model's noise.

## ECI against P0 (`compare.json`; lib/sens_metrics.py; S2 and S3 limit 12 of 254, frontier 1 of 20)
| Fit | Rows | S2 all | S3 all | S2 frontier | Top 10 | Frontier max shift | Mean shift <100 / 100-130 / >=130 |
|---|---|---|---|---|---|---|---|
| AUG_base_all (stacked) | 3,463 | 38 | 13 | 0 | same | 1.26 | -2.46 / -1.41 / +0.63 |
| AUG_base_ind (stacked) | 3,326 | 19 | 21 | 0 | same | 0.46 | -1.91 / -1.15 / +0.36 |
| AUG_mean_all (cell mean) | 2,879 | 4 | 0 | 0 | same | 0.41 | +0.77 / -0.52 / +0.23 |
| AUG_mean_ind (cell mean) | 2,879 | 2 | 0 | 0 | same | 0.07 | +0.64 / -0.40 / +0.12 |

- All four fits converged at the pilot stage.
- Stacking treats each source as an independent replicate. The residual correlation above indicates they are not, so the stacked fits overweight multi-source cells.
- The cell-mean fits stay within every S limit.

## Cell model (`aug_model.py`)
- First fits: AUG_cell_all and AUG_cell_ind reached the 3-hour cap.
- Pilot diagnostics (`pilot_diag_*.json`): on `all`, one chain sat in a near-zero-cell-effect mode. On `ind`, the fit was near convergence: tau_u 0.22 (0.19 to 0.26) on the logit scale, independent-source offset +0.017 (-0.020 to 0.051).
- Refits at target acceptance 0.99 are running (`AUG_cell_*_ta99`).
