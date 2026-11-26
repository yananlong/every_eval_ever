# Experiment Tracker

Stages W1 to W6 are rows of block W; the stage is the first word of Purpose. Runs R001 to R006 replace the first version's rows R001 to R004 (B0 to B3); its rows R005 to R007 (B4 to B6) are now R007 to R009.

| Run ID | Block ID | Gate ID | Purpose | Priority | Status | Owner | Dependency | Output artifact | Notes | Kind |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R001 | W | G2 | W1 prior predictive check: 1,000 datasets from Epoch's priors and from the reference prior PR; PR criterion | must-run | ready | analyst | | runs/W/W1/prior_predictive.json | No gate stops on W1; PR feeds W5 (G2) and W6 (G7); needs only the zip, no fits | planned |
| R002 | W | G0 | W2 fit and reproduction: published fit input, seeds 12345, 22345, 32345, evaluate=True; W2b on the loader output; our F0 and the equivalence check EQ | must-run | ready | analyst | | runs/W/W2/reproduction.json | Code e04929a and 2026-11-13 zip already fetched; environment not yet built; an EQ failure blocks W6 and PR only | planned |
| R003 | W | G1 | W3 computational and check calibration: positive-control prior, 199 null replicates (SBC ranks, recovery, T1-T7 reference), 5 misfit generators x 20 (power) | must-run | blocked | analyst | R002 | runs/W/W3/calibration.json | Needs the W2 posterior; about 10 h, restartable per replicate | planned |
| R004 | W | G3 | W4 posterior predictive and LOO-PIT checks: Epoch's suite, T1-T7 with max-T, 5 held-out folds, W4d if needed | must-run | blocked | analyst | R002, R003 | runs/W/W4/ppc.json | Needs the W3 null reference values | planned |
| R005 | W | G2 | W5 prior sensitivity: S5 screen first, then P0, P0b, grid P1-P10 and X1-X2, PR, S1-S4; exploratory targeted refits | must-run | blocked | analyst | R001, R002, R003 | runs/W/W5/sensitivity.json | Grid frozen in prior-grid.json; PR and targeted refits are exploratory | planned |
| R006 | W | G7 | W6 model expansion and comparison (exploratory): F0 to F7, PSIS-LOO or K-fold, preference rule, reduced SBC, adequate set | must-run | blocked | analyst | R001, R002, R003, R004, R005 | runs/W/W6/expansion.json | Starts only after the C1 and C2 verdict files are digested; about 3 to 10 h typical | planned |
| R007 | B4 | G4 | EEE crosswalk, audit, cross-source coverage on Epoch's model; exploratory add-on under adequate expansions | must-run | ready | analyst | R002 (stage b only), R006 (add-on only) | runs/B4/transfer.json | Stage a can start now (datastore: Hugging Face dataset evaleval/EEE_datastore, manifest dd7efcff); it does not need W2 | planned |
| R008 | B5 | G5 | ECI refit on EEE-matched matrix | nice-to-have | blocked | analyst | R007 | runs/B5/eee_refit.json | Opens only if G4 size condition holds | planned |
| R009 | B6 | G6 | Data-handling sensitivity | nice-to-have | blocked | analyst | R005 | runs/B6/handling.json | Inclusion and ceiling variants compare with W2b | planned |
