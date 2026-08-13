"""EEE field mapping for frozen drug-interaction paper results."""

from __future__ import annotations

import json
from dataclasses import dataclass

from every_eval_ever.eval_types import (
    EvalLibrary, EvaluationLog, EvaluationResult, EvaluatorRelationship,
    GenerationConfig, MetricConfig, ModelInfo, ScoreDetails, ScoreType,
    SourceDataPrivate, SourceDataUrl, SourceMetadata, SourceType,
)

from .source_schema import Dataset, Method, Metric, Protocol, ResultCell, SnapshotBundle

EVAL_LIBRARY_NAME = 'paper-reported-results'

@dataclass(frozen=True)
class BuiltLog:
    log: EvaluationLog
    collection_slug: str
    developer: str
    model_name: str


def _string_map(values: dict[str, object]) -> dict[str, str]:
    return {
        str(key): ('true' if value is True else 'false' if value is False else str(value))
        for key, value in values.items()
        if value is not None
    }
def _indexes(bundle: SnapshotBundle):
    return (
        {item.method_id: item for item in bundle.methods},
        {item.dataset_id: item for item in bundle.datasets},
        {item.protocol_id: item for item in bundle.protocols},
        {item.metric_id: item for item in bundle.metrics},
        {item.condition_id: item for item in bundle.manifest.conditions},
    )


def _source_data(bundle: SnapshotBundle, dataset: Dataset):
    details = _string_map(
        {
            'study_id': bundle.manifest.study_id,
            'source_snapshot_id': bundle.manifest.snapshot_id,
            'dataset_version': dataset.dataset_version,
            'task_type': dataset.task_type,
            **dataset.details,
        }
    )
    if dataset.source_type == 'url':
        return SourceDataUrl(
            dataset_name=dataset.display_name,
            source_type='url',
            url=dataset.source_urls,
            additional_details=details,
        )
    return SourceDataPrivate(
        dataset_name=dataset.display_name,
        source_type='other',
        additional_details=details,
    )


def _metric_config(metric: Metric, protocol: Protocol) -> MetricConfig:
    return MetricConfig(
        evaluation_description=(
            f'{metric.display_name} for {protocol.display_name}. '
            'Value and unit are preserved from the cited paper table.'
        ),
        metric_id=metric.metric_id,
        metric_name=metric.display_name,
        metric_kind=metric.metric_kind,
        metric_unit=metric.metric_unit,
        metric_parameters=metric.parameters or None,
        lower_is_better=metric.lower_is_better,
        score_type=ScoreType.continuous,
        min_score=metric.min_score,
        max_score=metric.max_score,
        additional_details={
            'protocol_id': protocol.protocol_id,
            'candidate_label_space': protocol.candidate_label_space,
        },
    )


def _result(
    bundle: SnapshotBundle,
    row: ResultCell,
    dataset: Dataset,
    protocol: Protocol,
    metric: Metric,
    condition_details: dict[str, str],
) -> EvaluationResult:
    details = {
        'source_snapshot_id': bundle.manifest.snapshot_id,
        'source_table': row.source_table,
        'source_page': row.source_page,
        'source_row': row.source_row,
        'source_column': row.source_column,
        'reported_value': row.reported_value,
        'result_origin': row.result_origin,
        'protocol_id': row.protocol_id,
        'condition_id': row.condition_id,
        'task_type': protocol.task_type,
        'novelty': json.dumps(protocol.novelty, sort_keys=True),
    }
    if row.reported_std is not None:
        # The papers report variation across seeds or folds, while EEE's typed
        # standard_deviation field is documented for per-sample scores. Preserve
        # the value verbatim rather than laundering it into the wrong semantic.
        details['reported_standard_deviation'] = row.reported_std
        details['reported_standard_deviation_basis'] = (
            'paper-defined repeated runs or folds; see source table caption'
        )
    if row.notes:
        details['source_notes'] = row.notes

    return EvaluationResult(
        evaluation_result_id=(
            f'{bundle.manifest.snapshot_id}/{row.dataset_id}/{row.method_id}/'
            f'{row.condition_id}/{row.protocol_id}/{row.metric_id}'
        ),
        evaluation_name=f'{dataset.collection_slug}.{row.protocol_id}',
        source_data=_source_data(bundle, dataset),
        metric_config=_metric_config(metric, protocol),
        score_details=ScoreDetails(score=row.score, details=details),
        generation_config=GenerationConfig(
            additional_details=_string_map(condition_details)
        ),
    )


def _model_info(method: Method) -> ModelInfo:
    details = {
        'method_category': method.method_category,
        'identity_status': method.identity_status,
        'is_paper_method': 'true' if method.is_paper_method else 'false',
        'deployment_type': 'unknown',
        'model_availability': 'unknown',
        **_string_map(method.details),
    }
    return ModelInfo(
        name=method.display_name,
        id=method.model_id,
        developer=method.developer,
        inference_platform='unknown',
        additional_details=details,
    )


def _source_metadata(bundle: SnapshotBundle, method: Method) -> SourceMetadata:
    details = {
        'study_id': bundle.manifest.study_id,
        'source_snapshot_id': bundle.manifest.snapshot_id,
        'paper_url': bundle.manifest.paper_url,
        'paper_version': bundle.manifest.paper_version,
        'publication_date': bundle.manifest.publication_date,
        'source_document_sha256': bundle.manifest.source_document_sha256
        or 'not_recorded',
        'bundle_sha256': bundle.entry.bundle_sha256,
        'identity_status': method.identity_status,
    }
    if bundle.manifest.repository_url:
        details['repository_url'] = bundle.manifest.repository_url
    if bundle.manifest.repository_commit:
        details['repository_commit'] = bundle.manifest.repository_commit
    if bundle.manifest.repository_role:
        details['repository_role'] = bundle.manifest.repository_role
    if bundle.manifest.version_warning:
        details['version_warning'] = bundle.manifest.version_warning
    return SourceMetadata(
        source_name=f'{bundle.manifest.title} ({bundle.manifest.paper_version})',
        source_type=SourceType.documentation,
        source_organization_name=bundle.manifest.source_organization,
        source_organization_url=bundle.manifest.paper_url,
        evaluator_relationship=EvaluatorRelationship(
            method.evaluator_relationship
        ),
        additional_details=details,
    )


def _eval_library(bundle: SnapshotBundle) -> EvalLibrary:
    return EvalLibrary(
        name=EVAL_LIBRARY_NAME,
        version='unknown',
        additional_details={
            'source_kind': 'paper_table',
            'source_snapshot_id': bundle.manifest.snapshot_id,
            'not_a_rerun': 'true',
        },
    )
