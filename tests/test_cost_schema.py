import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator


SCHEMA_PATH = Path(__file__).parents[1] / "every_eval_ever" / "schemas" / "cost.schema.json"


@pytest.fixture(scope="module")
def validator():
    schema = json.loads(SCHEMA_PATH.read_text())
    Draft7Validator.check_schema(schema)
    return Draft7Validator(schema)


def test_cost_schema_accepts_componentized_agentic_costs(validator):
    record = {
        "currency": "USD",
        "status": "observed",
        "total": 1.3042,
        "components": [
            {
                "category": "agent_model",
                "component_id": "anthropic/claude-sonnet",
                "amount": 1.118,
                "usage": {
                    "input_tokens": 82000,
                    "output_tokens": 9100,
                    "cache_read_tokens": 40000,
                },
                "pricing": {
                    "source_url": "https://example.com/pricing",
                    "effective_at": "2026-07-01",
                    "provider": "anthropic",
                },
            },
            {
                "category": "tool",
                "component_id": "browser.search",
                "amount": 0.011,
                "usage": {"tool_calls": 3},
            },
            {
                "category": "sandbox_compute",
                "amount": 0.1752,
                "usage": {"cpu_seconds": 600, "memory_gb_seconds": 3200},
            },
        ],
    }

    assert list(validator.iter_errors(record)) == []


def test_cost_schema_keeps_judge_and_simulator_costs_distinct(validator):
    record = {
        "currency": "USD",
        "status": "reconstructed",
        "components": [
            {"category": "judge_model", "amount": 0.12},
            {"category": "user_simulator", "amount": 0.08},
        ],
    }

    assert list(validator.iter_errors(record)) == []


def test_cost_schema_rejects_untyped_cost_metadata(validator):
    record = {
        "currency": "USD",
        "status": "observed",
        "components": [{"category": "model", "amount": "1.30"}],
    }

    errors = list(validator.iter_errors(record))
    assert errors
