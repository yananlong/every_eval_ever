"""Build and validate logical EEE logs from source bundles."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable, Sequence

from every_eval_ever.eval_types import EvaluationLog
from every_eval_ever.helpers import SCHEMA_VERSION

from .modeling import (BuiltLog, _eval_library, _indexes, _model_info, _result, _source_metadata)
from .source_schema import ResultCell, SnapshotBundle

def build_logs(
    bundles: Sequence[SnapshotBundle],
    *,
    studies: set[str] | None = None,
    datasets: set[str] | None = None,
    snapshots: set[str] | None = None,
) -> list[BuiltLog]:
    available_studies = {bundle.manifest.study_id for bundle in bundles}
    available_snapshots = {bundle.manifest.snapshot_id for bundle in bundles}
    available_datasets = {
        dataset.dataset_id for bundle in bundles for dataset in bundle.datasets
    }
    for selected, available, label in (
        (studies, available_studies, 'study'),
        (datasets, available_datasets, 'dataset'),
        (snapshots, available_snapshots, 'snapshot'),
    ):
        if selected:
            unknown = selected - available
            if unknown:
                raise ValueError(f'unknown {label} filter(s): {sorted(unknown)}')

    built: list[BuiltLog] = []
    logical_ids: set[str] = set()
    for bundle in bundles:
        if studies and bundle.manifest.study_id not in studies:
            continue
        if snapshots and bundle.manifest.snapshot_id not in snapshots:
            continue
        methods, dataset_map, protocols, metrics, conditions = _indexes(bundle)
        grouped: dict[tuple[str, str, str], list[ResultCell]] = defaultdict(list)
        for row in bundle.results:
            if datasets and row.dataset_id not in datasets:
                continue
            grouped[(row.dataset_id, row.method_id, row.condition_id)].append(row)

        for (dataset_id, method_id, condition_id), rows in sorted(grouped.items()):
            dataset = dataset_map[dataset_id]
            method = methods[method_id]
            condition = conditions[condition_id]
            eval_results = [
                _result(
                    bundle,
                    row,
                    dataset,
                    protocols[row.protocol_id],
                    metrics[row.metric_id],
                    {
                        'condition_id': condition.condition_id,
                        'condition_name': condition.display_name,
                        **condition.details,
                    },
                )
                for row in sorted(
                    rows, key=lambda item: (item.protocol_id, item.metric_id)
                )
            ]
            evaluation_id = (
                f'drug-interaction-papers/{bundle.manifest.snapshot_id}/'
                f'{dataset_id}/{method_id}/{condition_id}'
            )
            if evaluation_id in logical_ids:
                raise ValueError(f'duplicate evaluation_id: {evaluation_id}')
            logical_ids.add(evaluation_id)
            log = EvaluationLog(
                schema_version=SCHEMA_VERSION,
                evaluation_id=evaluation_id,
                retrieved_timestamp=bundle.manifest.retrieved_timestamp,
                source_metadata=_source_metadata(bundle, method),
                eval_library=_eval_library(bundle),
                model_info=_model_info(method),
                evaluation_results=eval_results,
            )
            model_name = method.model_id.split('/', 1)[1].replace('/', '_')
            built.append(
                BuiltLog(
                    log=log,
                    collection_slug=dataset.collection_slug,
                    developer=method.model_id.split('/', 1)[0],
                    model_name=model_name,
                )
            )
    return built


def semantic_records(built: Iterable[BuiltLog]) -> dict[str, dict[str, object]]:
    """Return deterministic content keyed by logical evaluation identity."""
    records: dict[str, dict[str, object]] = {}
    for item in built:
        payload = item.log.model_dump(mode='json', exclude_none=True)
        key = item.log.evaluation_id
        if key in records:
            raise ValueError(f'duplicate semantic record {key}')
        records[key] = payload
    return records


def validate_built_logs(built: Sequence[BuiltLog]) -> None:
    if not built:
        raise ValueError('selection produced no evaluation logs')
    result_ids: set[str] = set()
    for item in built:
        reparsed = EvaluationLog.model_validate(
            item.log.model_dump(mode='json', exclude_none=True)
        )
        if reparsed.evaluation_id != item.log.evaluation_id:
            raise ValueError('evaluation_id changed during schema round trip')
        for result in item.log.evaluation_results:
            rid = result.evaluation_result_id
            if rid is None or rid in result_ids:
                raise ValueError(f'missing or duplicate evaluation_result_id: {rid}')
            result_ids.add(rid)

