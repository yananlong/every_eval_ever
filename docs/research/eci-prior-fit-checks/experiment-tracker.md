# Experiment Tracker

| Run ID | Block ID | Gate ID | Purpose | Priority | Status | Owner | Dependency | Output artifact | Notes | Kind |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R001 | B0 | G0 | Reproduce published ECI from the published fit input, seeds 12345, 22345, 32345, evaluate=True; B0b on the loader output | must-run | ready | analyst | | runs/B0/reproduction.json | Code e04929a and 2026-11-13 zip already fetched; environment not yet built | planned |
| R002 | B1 | G1 | Positive-control prior, prior predictive, 199 null replicates (recovery, reference values), 5 misfit generators x 20 (power) | must-run | blocked | analyst | R001 | runs/B1/calibration.json | Needs the B0 posterior; about 10 h, restartable per replicate | planned |
| R003 | B2 | G2 | P0 and P0b noise floor, S5 screen, refit grid P1-P10 and X1-X2, S1-S4 | must-run | blocked | analyst | R001, R002 | runs/B2/sensitivity.json | Grid frozen in prior-grid.json | planned |
| R004 | B3 | G3 | Epoch's suite, checks T1-T7 with max-T, 5 held-out folds, B3d if needed | must-run | blocked | analyst | R001, R002 | runs/B3/ppc.json | Needs the B1 null reference values | planned |
| R005 | B4 | G4 | EEE crosswalk, audit, cross-source coverage | must-run | ready | analyst | R001 (stage b only) | runs/B4/transfer.json | Stage a can start now (datastore: Hugging Face dataset evaleval/EEE_datastore, manifest dd7efcff); it does not need B0 | planned |
| R006 | B5 | G5 | ECI refit on EEE-matched matrix | nice-to-have | blocked | analyst | R005 | runs/B5/eee_refit.json | Opens only if G4 size condition holds | planned |
| R007 | B6 | G6 | Data-handling sensitivity | nice-to-have | blocked | analyst | R003 | runs/B6/handling.json | Inclusion and ceiling variants compare with B0b | planned |
