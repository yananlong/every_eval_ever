# Experiment Tracker

| Run ID | Block ID | Gate ID | Purpose | Priority | Status | Owner | Dependency | Output artifact | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| R001 | B1 | G1 | Source freeze and transcription audit | must-run | blocked | Adapter author and source verifier | None | `evidence/B1-source-audit.json` | Human second-pass verification remains required for independent status. |
| R002 | B2 | G2 | Semantic mapping and licensing audit | must-run | analyzed | Adapter author and adversarial reviewer | B1 | `evidence/B2-semantic-audit.json` | Must use current EEE schema at branch tip. |
| R003 | B3 | G3 | Full conversion, schema validation, deterministic replay | must-run | analyzed | Adapter author | B1, B2 | `evidence/B3-conversion-audit.json` | Compare by logical IDs and semantic JSON, not UUID filenames. |
| R004 | B4 | G4 | Negative-control and atomicity matrix | must-run | analyzed | Adapter author and reviewer | B3 | `evidence/B4-negative-control-audit.json` | Preserve the predefined failure matrix. |
| R005 | B5 | G5 | Datastore release dry run | must-run | blocked | Adapter author / maintainer | B3, B4 | `evidence/B5-release-audit.json` | No datastore mutation or PR in this stage. |
