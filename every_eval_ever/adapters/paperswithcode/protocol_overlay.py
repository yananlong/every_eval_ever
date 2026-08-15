"""Reviewed protocol qualification for Papers with Code DrugBank rows.

The generic Papers with Code adapter intentionally treats ``DrugBank`` as dataset
provenance only. This module applies a curated, fail-closed overlay after generic
conversion when a primary paper or official result artifact establishes the
missing split semantics.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from every_eval_ever.helpers import SourceConversionResult

from . import adapter as generic

DEFAULT_DRUGBANK_OVERLAY_PATH = (
    Path(__file__).with_name('protocol_overlays') / 'drugbank.yaml'
)
_ID_RE = re.compile(r'^[a-z0-9][a-z0-9.-]*$')
_OPAQUE_PROTOCOL_RE = re.compile(r'^(?:s|cs)\d+$', re.IGNORECASE)
_SHA256_RE = re.compile(r'^[0-9a-f]{64}$')
_REQUIRED_NOVELTY_AXES = {
    'drug_entity_overlap',
    'target_entity_overlap',
    'relation_class_overlap',
    'pair_overlap',
    'temporal_ordering',
    'negative_sampling',
    'split_preprocessing',
}


class _StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', frozen=True)


class OverlayAnchors(_StrictModel):
    paper_id: str | int | None
    dataset_id: str | int
    task_id: str | int
    model_name: str

    @field_validator('paper_id', 'dataset_id', 'task_id', 'model_name')
    @classmethod
    def require_nonempty_anchor(cls, value):
        if isinstance(value, str) and not value.strip():
            raise ValueError('protocol overlay anchors must be non-empty')
        return value


class ProtocolQualification(_StrictModel):
    study_id: str
    dataset_id: str
    task_id: str
    collection_slug: str
    protocol_id: str
    condition_id: str | None = None
    task_type: str
    candidate_label_space: str
    novelty: dict[str, str]

    @field_validator(
        'study_id', 'dataset_id', 'task_id', 'collection_slug', 'condition_id'
    )
    @classmethod
    def validate_id(cls, value: str | None):
        if value is None:
            return value
        if not _ID_RE.fullmatch(value):
            raise ValueError(
                'protocol qualification ids must be lowercase semantic slugs'
            )
        return value

    @field_validator('protocol_id')
    @classmethod
    def validate_protocol_id(cls, value: str):
        if _OPAQUE_PROTOCOL_RE.fullmatch(value):
            raise ValueError(
                'opaque source split tokens such as S1/CS2 are not normalized '
                'protocol ids; use the reviewed split semantics'
            )
        if not _ID_RE.fullmatch(value):
            raise ValueError(
                'protocol qualification ids must be lowercase semantic slugs'
            )
        return value

    @field_validator('task_type', 'candidate_label_space')
    @classmethod
    def require_nonempty_semantics(cls, value: str):
        if not value.strip():
            raise ValueError('protocol semantic fields must be non-empty')
        return value

    @model_validator(mode='after')
    def require_novelty_axes(self):
        missing = sorted(_REQUIRED_NOVELTY_AXES - set(self.novelty))
        if missing:
            raise ValueError(
                f'protocol novelty is missing required axis/axes: {missing}'
            )
        empty = sorted(key for key, value in self.novelty.items() if not value.strip())
        if empty:
            raise ValueError(
                f'protocol novelty has empty semantic value(s): {empty}'
            )
        return self

    def evaluation_name(self) -> str:
        return f'{self.collection_slug}.{self.protocol_id}'


class ProtocolEvidence(_StrictModel):
    source_url: str
    source_locator: str
    verification_note: str

    @field_validator('source_url')
    @classmethod
    def validate_source_url(cls, value: str):
        value = value.strip()
        parsed = urlparse(value)
        if parsed.scheme not in {'http', 'https'} or not parsed.netloc:
            raise ValueError(
                'protocol evidence source_url must be an absolute HTTP(S) URL'
            )
        return value

    @field_validator('source_locator', 'verification_note')
    @classmethod
    def require_nonempty_evidence(cls, value: str):
        if not value.strip():
            raise ValueError('protocol evidence fields must be non-empty')
        return value


class ProtocolOverlayEntry(_StrictModel):
    pwc_evaluation_id: str | int
    verified_against_dump_version: str
    anchors: OverlayAnchors
    source_metrics_sha256: str
    qualification: ProtocolQualification
    evidence: ProtocolEvidence
    metrics: list[str]

    @field_validator('pwc_evaluation_id')
    @classmethod
    def require_nonempty_evaluation_id(cls, value):
        if isinstance(value, str) and not value.strip():
            raise ValueError('PwC evaluation id must be non-empty')
        return value

    @field_validator('verified_against_dump_version')
    @classmethod
    def validate_dump_version(cls, value: str):
        return _validated_dump_version(value, 'verified_against_dump_version')

    @field_validator('source_metrics_sha256')
    @classmethod
    def validate_source_metrics_sha256(cls, value: str):
        if not _SHA256_RE.fullmatch(value):
            raise ValueError(
                'source_metrics_sha256 must be a lowercase 64-character SHA-256'
            )
        return value

    @field_validator('metrics')
    @classmethod
    def validate_metrics(cls, value: list[str]):
        if not value:
            raise ValueError('metrics must contain at least one source metric name')
        if any(not name or not name.strip() for name in value):
            raise ValueError('metric selectors must be non-empty source names')
        if len(value) != len(set(value)):
            raise ValueError('metric selectors must be unique within an entry')
        return value

    @model_validator(mode='after')
    def require_drugbank_qualification(self):
        if self.qualification.dataset_id != 'drugbank':
            raise ValueError(
                'DrugBank protocol overlay entries must target normalized '
                'dataset_id drugbank'
            )
        return self


class ProtocolOverlay(_StrictModel):
    schema_version: int = Field(ge=1, le=1)
    entries: list[ProtocolOverlayEntry]

    @model_validator(mode='after')
    def reject_overlapping_entries(self):
        grouped: dict[str, list[ProtocolOverlayEntry]] = defaultdict(list)
        for entry in self.entries:
            grouped[str(entry.pwc_evaluation_id)].append(entry)
        for evaluation_id, entries in grouped.items():
            if len(entries) < 2:
                continue
            seen: set[str] = set()
            for entry in entries:
                overlap = seen.intersection(entry.metrics)
                if overlap:
                    raise ValueError(
                        f'PwC evaluation {evaluation_id} has overlapping metric '
                        f'selectors: {sorted(overlap)}'
                    )
                seen.update(entry.metrics)
        return self


def _validated_dump_version(value: Any, field_name: str) -> str:
    text = str(value)
    if not re.fullmatch(r'\d{8}', text):
        raise ValueError(f'{field_name} must be a valid YYYYMMDD calendar date')
    try:
        parsed = datetime.strptime(text, '%Y%m%d')
    except ValueError as exc:
        raise ValueError(
            f'{field_name} must be a valid YYYYMMDD calendar date'
        ) from exc
    if parsed.strftime('%Y%m%d') != text:
        raise ValueError(f'{field_name} must be a valid YYYYMMDD calendar date')
    return text


def load_protocol_overlay(path: str | Path) -> ProtocolOverlay:
    payload = yaml.safe_load(Path(path).read_text(encoding='utf-8'))
    return ProtocolOverlay.model_validate(payload)


def load_default_drugbank_overlay() -> ProtocolOverlay:
    return load_protocol_overlay(DEFAULT_DRUGBANK_OVERLAY_PATH)


def _normalized_anchor(value: Any) -> str | None:
    return None if value is None else str(value)


def _assert_anchor(evaluation_id: str, field_name: str, expected: Any, actual: Any) -> None:
    if _normalized_anchor(expected) != _normalized_anchor(actual):
        raise ValueError(
            f'protocol overlay anchor drift for PwC evaluation {evaluation_id}: '
            f'{field_name} expected {expected!r}, got {actual!r}'
        )


def _source_metrics(row: dict[str, Any]) -> dict[str, Any]:
    raw = row.get('metrics')
    if isinstance(raw, dict):
        metrics = raw
    else:
        try:
            metrics = json.loads(raw) if raw else {}
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f'PwC evaluation {row.get("id")} has invalid metrics JSON'
            ) from exc
    if not isinstance(metrics, dict):
        raise ValueError(
            f'PwC evaluation {row.get("id")} metrics must decode to an object'
        )
    if any(not isinstance(name, str) for name in metrics):
        raise ValueError(
            f'PwC evaluation {row.get("id")} metric names must be strings'
        )
    return metrics


def source_metrics_sha256(metrics: dict[str, Any]) -> str:
    payload = json.dumps(
        metrics,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
        allow_nan=False,
    )
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def _source_evaluation_id(row: dict[str, Any]) -> str:
    value = row.get('id')
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError('PwC source evaluation id must be non-empty')
    return str(value)


def build_qualification_index(
    overlay: ProtocolOverlay,
    evaluations: Iterable[dict[str, Any]],
    dump_version: str,
) -> dict[tuple[str, str], ProtocolOverlayEntry]:
    current_dump_version = _validated_dump_version(dump_version, 'current dump_version')
    rows: dict[str, dict[str, Any]] = {}
    for row in evaluations:
        evaluation_id = _source_evaluation_id(row)
        if evaluation_id in rows:
            raise ValueError(f'duplicate PwC evaluation id in source: {evaluation_id}')
        rows[evaluation_id] = row

    index: dict[tuple[str, str], ProtocolOverlayEntry] = {}
    for entry in overlay.entries:
        evaluation_id = str(entry.pwc_evaluation_id)
        row = rows.get(evaluation_id)
        if row is None:
            raise ValueError(
                f'protocol overlay references missing PwC evaluation {evaluation_id}'
            )
        if current_dump_version != entry.verified_against_dump_version:
            raise ValueError(
                f'protocol overlay for PwC evaluation {evaluation_id} is pinned '
                f'to dump {entry.verified_against_dump_version}, not current dump '
                f'{current_dump_version}; re-review is required'
            )
        anchors = entry.anchors
        for field_name in ('paper_id', 'dataset_id', 'task_id', 'model_name'):
            _assert_anchor(
                evaluation_id,
                field_name,
                getattr(anchors, field_name),
                row.get(field_name),
            )
        source_metrics = _source_metrics(row)
        actual_metrics_sha256 = source_metrics_sha256(source_metrics)
        if actual_metrics_sha256 != entry.source_metrics_sha256:
            raise ValueError(
                f'protocol overlay metrics payload drift for PwC evaluation '
                f'{evaluation_id}: expected {entry.source_metrics_sha256}, got '
                f'{actual_metrics_sha256}'
            )
        missing = sorted(set(entry.metrics) - set(source_metrics))
        if missing:
            raise ValueError(
                f'protocol overlay for PwC evaluation {evaluation_id} selects '
                f'missing metric(s): {missing}'
            )
        for metric_name in entry.metrics:
            key = (evaluation_id, metric_name)
            if key in index:
                raise ValueError(f'PwC source score cell is qualified more than once: {key}')
            index[key] = entry
    return index


def _qualified_result(result, entry: ProtocolOverlayEntry, dump_version: str):
    qualification = entry.qualification
    metric_details = dict(result.metric_config.additional_details or {})
    metric_details.update(
        {
            'protocol_id': qualification.protocol_id,
            'candidate_label_space': qualification.candidate_label_space,
            'protocol_task_type': qualification.task_type,
        }
    )
    metric_config = result.metric_config.model_copy(update={'additional_details': metric_details})
    score_details = dict(result.score_details.details or {})
    additions = {
        'protocol_study_id': qualification.study_id,
        'protocol_dataset_id': qualification.dataset_id,
        'protocol_task_id': qualification.task_id,
        'protocol_collection_slug': qualification.collection_slug,
        'protocol_id': qualification.protocol_id,
        'protocol_condition_id': qualification.condition_id,
        'protocol_task_type': qualification.task_type,
        'protocol_candidate_label_space': qualification.candidate_label_space,
        'protocol_novelty': json.dumps(qualification.novelty, sort_keys=True, separators=(',', ':')),
        'protocol_evidence_url': entry.evidence.source_url,
        'protocol_evidence_locator': entry.evidence.source_locator,
        'protocol_verification_note': entry.evidence.verification_note,
        'protocol_verified_against_dump_version': entry.verified_against_dump_version,
        'protocol_source_metrics_sha256': entry.source_metrics_sha256,
        'protocol_applied_to_dump_version': dump_version,
        'pwc_paper_id': _normalized_anchor(entry.anchors.paper_id),
        'pwc_dataset_id': _normalized_anchor(entry.anchors.dataset_id),
        'pwc_task_id': _normalized_anchor(entry.anchors.task_id),
    }
    score_details.update({key: value for key, value in additions.items() if value is not None})
    score = result.score_details.model_copy(update={'details': score_details})
    return result.model_copy(
        update={
            'evaluation_name': qualification.evaluation_name(),
            'metric_config': metric_config,
            'score_details': score,
        }
    )


def qualify_conversion(
    conversion: SourceConversionResult[generic.LogBundle],
    evaluations: Iterable[dict[str, Any]],
    overlay: ProtocolOverlay,
    dump_version: str,
) -> SourceConversionResult[generic.LogBundle]:
    if not overlay.entries:
        return conversion
    rows = list(evaluations)
    index = build_qualification_index(overlay, rows, dump_version)
    if not index:
        return conversion
    seen: set[tuple[str, str]] = set()
    bundles: list[generic.LogBundle] = []
    for bundle in conversion.records:
        results = []
        for result in bundle.log.evaluation_results:
            details = result.score_details.details or {}
            evaluation_id = details.get('pwc_evaluation_id')
            metric_name = result.metric_config.metric_name
            key = (str(evaluation_id), metric_name)
            entry = index.get(key)
            if entry is None:
                results.append(result)
                continue
            if key in seen:
                raise ValueError(f'PwC source score cell emitted twice: {key}')
            seen.add(key)
            results.append(_qualified_result(result, entry, dump_version))
        log = bundle.log.model_copy(update={'evaluation_results': results})
        bundles.append(generic.LogBundle(log=log, developer=bundle.developer, model=bundle.model))
    missing = sorted(set(index) - seen)
    if missing:
        raise ValueError(
            'qualified PwC source score cell(s) did not survive generic '
            f'conversion: {missing}'
        )
    return SourceConversionResult(
        source_name=conversion.source_name,
        total_records=conversion.total_records,
        records=bundles,
        failures=conversion.failures,
        exclusions=conversion.exclusions,
    )


def build_logs(
    evaluations: Iterable[dict[str, Any]],
    datasets_by_id: dict[Any, dict[str, Any]],
    tasks_by_id: dict[Any, dict[str, Any]],
    resolver: generic.MetricResolver,
    metric_ranges: dict[str, tuple[float, float]],
    metric_meta: dict[str, dict[str, Any]],
    papers_by_id: dict[Any, dict[str, Any]],
    dump_version: str,
    retrieved_ts: str,
    *,
    overlay: ProtocolOverlay,
    source_bucket: str | None = None,
    dump_file: str | None = None,
    group_scales: dict[tuple[Any, str], generic.GroupScale] | None = None,
) -> SourceConversionResult[generic.LogBundle]:
    rows = list(evaluations)
    conversion = generic.build_logs(
        rows,
        datasets_by_id,
        tasks_by_id,
        resolver,
        metric_ranges,
        metric_meta,
        papers_by_id,
        dump_version,
        retrieved_ts,
        source_bucket=source_bucket,
        dump_file=dump_file,
        group_scales=group_scales,
    )
    return qualify_conversion(conversion, rows, overlay, dump_version)
