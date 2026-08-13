"""Shared helpers for experiment-plan audit blocks."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Callable

import yaml

from every_eval_ever.eval_types import EvaluationLog

from .source_schema import bundle_digest

PACKAGE_ROOT = Path(__file__).resolve().parent
PLAN_ROOT = PACKAGE_ROOT / 'experiment-plan'
EVIDENCE_ROOT = PLAN_ROOT / 'evidence'

def _write(report: dict[str, object], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + '\n',
        encoding='utf-8',
    )


def _base_report(block: str) -> dict[str, object]:
    return {
        'block_id': block,
        'technical_status': 'pass',
        'scientific_gate_status': 'not_interpreted',
        'evidence_class': 'exploratory',
    }
def _scan_forbidden(root: Path) -> list[dict[str, str]]:
    findings = []
    patterns = {
        'drugbank_identifier': re.compile(r'\bDB\d{5}\b'),
        'protein_sequence': re.compile(r'\b[ACDEFGHIKLMNPQRSTVWY]{40,}\b'),
        'raw_smiles_field': re.compile(r'(?i)\b(raw_smiles|drug_smiles|canonical_smiles)\b'),
        'raw_drug_description_field': re.compile(
            r'(?i)\b(raw_description|drug_description_text|drugbank_description)\b'
        ),
    }
    for path in sorted(root.rglob('*')):
        if not path.is_file() or path.suffix not in {'.yaml', '.csv', '.json', '.md'}:
            continue
        text = path.read_text(encoding='utf-8')
        for name, pattern in patterns.items():
            if pattern.search(text):
                findings.append({'path': str(path), 'pattern': name})
    return findings
def _read_output(root: Path) -> dict[str, dict[str, object]]:
    output: dict[str, dict[str, object]] = {}
    for path in sorted(root.rglob('*.json')):
        log = EvaluationLog.model_validate_json(path.read_text(encoding='utf-8'))
        if log.evaluation_id in output:
            raise AssertionError(f'duplicate evaluation_id {log.evaluation_id}')
        output[log.evaluation_id] = log.model_dump(mode='json', exclude_none=True)
    return output
def _copy_sources(source_root: Path, destination: Path) -> Path:
    target = destination / 'sources'
    shutil.copytree(source_root, target)
    return target


def _refresh_bundle_digest(source_root: Path, study_id: str) -> None:
    catalog_path = source_root / 'catalog.yaml'
    raw = yaml.safe_load(catalog_path.read_text(encoding='utf-8'))
    for entry in raw['snapshots']:
        if entry['study_id'] == study_id:
            entry['bundle_sha256'] = bundle_digest(source_root / study_id)
    catalog_path.write_text(
        yaml.safe_dump(raw, sort_keys=False), encoding='utf-8'
    )


def _expect_failure(
    name: str,
    function: Callable[[], object],
    *,
    redact_roots: tuple[Path, ...] = (),
) -> dict[str, str]:
    try:
        function()
    except Exception as exc:
        message = str(exc)
        for root in redact_roots:
            message = message.replace(str(root), '<TMP>')
        return {'case': name, 'status': 'rejected', 'error': message}
    raise AssertionError(f'negative control {name!r} was accepted')
