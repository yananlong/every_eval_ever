# Execution Bridge

## Block Hand-off

### B1

- Claim IDs: C1
- Decision gate ID: G1
- Current evidence class: exploratory
- Requested evidence class: confirmatory; current self-audit remains exploratory
- Inputs required: every_eval_ever/adapters/drug_interaction_papers/sources; every_eval_ever/adapters/drug_interaction_papers/experiment-plan/source-verification-ledger.md
- Declared input snapshot paths: every_eval_ever/adapters/drug_interaction_papers/sources; every_eval_ever/adapters/drug_interaction_papers/experiment-plan/source-verification-ledger.md
- Declared evaluator snapshot paths: every_eval_ever/adapters/drug_interaction_papers/source_schema.py
- Expected implementation entrypoint: every_eval_ever.adapters.drug_interaction_papers.adapter
- Expected command or notebook: `python -m every_eval_ever.adapters.drug_interaction_papers.audit --block B1 --output every_eval_ever/adapters/drug_interaction_papers/experiment-plan/evidence/B1-source-audit.json`
- Output artifacts to produce: every_eval_ever/adapters/drug_interaction_papers/experiment-plan/evidence/B1-source-audit.json
- Auditor-facing checks: Verify the artifact exists, records all outcome categories, matches the frozen gate criteria, and is not treated as proof beyond its declared evidence class.
- Intended lineage relation: baseline for the valid run; negative_control or technical_retry only where declared in `run-blocks.json`.
- Parent run ID or rationale: Baseline run in the same block; no scientific pivot lineage is permitted.
- Hidden information unavailable to the evaluated system: Expected source values and gate disposition are frozen outside converter output; mutated test expectations are controlled by the test harness.
- Failure, skip, null, timeout, and retry states to retain: Source failures, declared exclusions, null/invalid values, validation failures, empty selections, write failures, retries, timeouts, and harness failures.
- Idempotency and restart requirements: A retry starts from unchanged declared inputs; publication uses a fresh staging directory; prior valid output remains unchanged until all validation passes.
- Known blockers: Any unresolved predecessor failure listed in the claim/block contracts; independent source-cell verification is a human review gate.

### B2

- Claim IDs: C1
- Decision gate ID: G2
- Current evidence class: exploratory
- Requested evidence class: confirmatory; current self-audit remains exploratory
- Inputs required: every_eval_ever/adapters/drug_interaction_papers/sources; every_eval_ever/adapters/drug_interaction_papers/adapter.py
- Declared input snapshot paths: every_eval_ever/adapters/drug_interaction_papers/sources; every_eval_ever/adapters/drug_interaction_papers/adapter.py
- Declared evaluator snapshot paths: tests/test_drug_interaction_papers_adapter.py
- Expected implementation entrypoint: every_eval_ever.adapters.drug_interaction_papers.audit
- Expected command or notebook: `python -m every_eval_ever.adapters.drug_interaction_papers.audit --block B2 --output every_eval_ever/adapters/drug_interaction_papers/experiment-plan/evidence/B2-semantic-audit.json`
- Output artifacts to produce: every_eval_ever/adapters/drug_interaction_papers/experiment-plan/evidence/B2-semantic-audit.json
- Auditor-facing checks: Verify the artifact exists, records all outcome categories, matches the frozen gate criteria, and is not treated as proof beyond its declared evidence class.
- Intended lineage relation: baseline for the valid run; negative_control or technical_retry only where declared in `run-blocks.json`.
- Parent run ID or rationale: Baseline run in the same block; no scientific pivot lineage is permitted.
- Hidden information unavailable to the evaluated system: Expected source values and gate disposition are frozen outside converter output; mutated test expectations are controlled by the test harness.
- Failure, skip, null, timeout, and retry states to retain: Source failures, declared exclusions, null/invalid values, validation failures, empty selections, write failures, retries, timeouts, and harness failures.
- Idempotency and restart requirements: A retry starts from unchanged declared inputs; publication uses a fresh staging directory; prior valid output remains unchanged until all validation passes.
- Known blockers: Any unresolved predecessor failure listed in the claim/block contracts; independent source-cell verification is a human review gate.

### B3

- Claim IDs: C1, C2
- Decision gate ID: G3
- Current evidence class: exploratory
- Requested evidence class: confirmatory; current self-audit remains exploratory
- Inputs required: every_eval_ever/adapters/drug_interaction_papers/sources; every_eval_ever/adapters/drug_interaction_papers/adapter.py
- Declared input snapshot paths: every_eval_ever/adapters/drug_interaction_papers/sources; every_eval_ever/adapters/drug_interaction_papers/adapter.py
- Declared evaluator snapshot paths: every_eval_ever/eval_types.py; every_eval_ever/cli.py
- Expected implementation entrypoint: every_eval_ever.adapters.drug_interaction_papers.adapter
- Expected command or notebook: `python -m every_eval_ever.adapters.drug_interaction_papers.audit --block B3 --output every_eval_ever/adapters/drug_interaction_papers/experiment-plan/evidence/B3-conversion-audit.json`
- Output artifacts to produce: every_eval_ever/adapters/drug_interaction_papers/experiment-plan/evidence/B3-conversion-audit.json
- Auditor-facing checks: Verify the artifact exists, records all outcome categories, matches the frozen gate criteria, and is not treated as proof beyond its declared evidence class.
- Intended lineage relation: baseline for the valid run; negative_control or technical_retry only where declared in `run-blocks.json`.
- Parent run ID or rationale: Baseline run in the same block; no scientific pivot lineage is permitted.
- Hidden information unavailable to the evaluated system: Expected source values and gate disposition are frozen outside converter output; mutated test expectations are controlled by the test harness.
- Failure, skip, null, timeout, and retry states to retain: Source failures, declared exclusions, null/invalid values, validation failures, empty selections, write failures, retries, timeouts, and harness failures.
- Idempotency and restart requirements: A retry starts from unchanged declared inputs; publication uses a fresh staging directory; prior valid output remains unchanged until all validation passes.
- Known blockers: Any unresolved predecessor failure listed in the claim/block contracts; independent source-cell verification is a human review gate.

### B4

- Claim IDs: C2
- Decision gate ID: G4
- Current evidence class: exploratory
- Requested evidence class: confirmatory; current self-audit remains exploratory
- Inputs required: every_eval_ever/adapters/drug_interaction_papers/sources; every_eval_ever/adapters/drug_interaction_papers/adapter.py
- Declared input snapshot paths: every_eval_ever/adapters/drug_interaction_papers/sources; every_eval_ever/adapters/drug_interaction_papers/adapter.py
- Declared evaluator snapshot paths: tests/test_drug_interaction_papers_adapter.py
- Expected implementation entrypoint: every_eval_ever.adapters.drug_interaction_papers.audit
- Expected command or notebook: `python -m every_eval_ever.adapters.drug_interaction_papers.audit --block B4 --output every_eval_ever/adapters/drug_interaction_papers/experiment-plan/evidence/B4-negative-control-audit.json`
- Output artifacts to produce: every_eval_ever/adapters/drug_interaction_papers/experiment-plan/evidence/B4-negative-control-audit.json
- Auditor-facing checks: Verify the artifact exists, records all outcome categories, matches the frozen gate criteria, and is not treated as proof beyond its declared evidence class.
- Intended lineage relation: baseline for the valid run; negative_control or technical_retry only where declared in `run-blocks.json`.
- Parent run ID or rationale: Baseline run in the same block; no scientific pivot lineage is permitted.
- Hidden information unavailable to the evaluated system: Expected source values and gate disposition are frozen outside converter output; mutated test expectations are controlled by the test harness.
- Failure, skip, null, timeout, and retry states to retain: Source failures, declared exclusions, null/invalid values, validation failures, empty selections, write failures, retries, timeouts, and harness failures.
- Idempotency and restart requirements: A retry starts from unchanged declared inputs; publication uses a fresh staging directory; prior valid output remains unchanged until all validation passes.
- Known blockers: Any unresolved predecessor failure listed in the claim/block contracts; independent source-cell verification is a human review gate.

### B5

- Claim IDs: C2
- Decision gate ID: G5
- Current evidence class: exploratory
- Requested evidence class: confirmatory; current self-audit remains exploratory
- Inputs required: every_eval_ever/adapters/drug_interaction_papers/sources; every_eval_ever/adapters/drug_interaction_papers/adapter.py
- Declared input snapshot paths: every_eval_ever/adapters/drug_interaction_papers/sources; every_eval_ever/adapters/drug_interaction_papers/adapter.py
- Declared evaluator snapshot paths: every_eval_ever/adapters/drug_interaction_papers/adapter.py; tests/test_drug_interaction_papers_adapter.py
- Expected implementation entrypoint: every_eval_ever.adapters.drug_interaction_papers.adapter
- Expected command or notebook: `python -m every_eval_ever.adapters.drug_interaction_papers.audit --block B5 --output every_eval_ever/adapters/drug_interaction_papers/experiment-plan/evidence/B5-release-audit.json`
- Output artifacts to produce: every_eval_ever/adapters/drug_interaction_papers/experiment-plan/evidence/B5-release-audit.json
- Auditor-facing checks: Verify the artifact exists, records all outcome categories, matches the frozen gate criteria, and is not treated as proof beyond its declared evidence class.
- Intended lineage relation: baseline for the valid run; negative_control or technical_retry only where declared in `run-blocks.json`.
- Parent run ID or rationale: Baseline run in the same block; no scientific pivot lineage is permitted.
- Hidden information unavailable to the evaluated system: Expected source values and gate disposition are frozen outside converter output; mutated test expectations are controlled by the test harness.
- Failure, skip, null, timeout, and retry states to retain: Source failures, declared exclusions, null/invalid values, validation failures, empty selections, write failures, retries, timeouts, and harness failures.
- Idempotency and restart requirements: A retry starts from unchanged declared inputs; publication uses a fresh staging directory; prior valid output remains unchanged until all validation passes.
- Known blockers: Any unresolved predecessor failure listed in the claim/block contracts; independent source-cell verification is a human review gate.
