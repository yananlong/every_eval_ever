"""Result-cell and complete snapshot validation."""

from __future__ import annotations

import math
from collections import Counter
from pathlib import Path
from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from .source_base import StrictModel, _validate_id
from .source_catalog import CatalogEntry
from .source_entities import Dataset, Manifest, Method, Metric, Protocol


class ResultCell(StrictModel):
    dataset_id: str
    method_id: str
    condition_id: str
    protocol_id: str
    metric_id: str
    score: float
    reported_value: str = Field(min_length=1)
    reported_std: str | None = None
    source_table: str = Field(min_length=1)
    source_page: str = Field(min_length=1)
    source_row: str = Field(min_length=1)
    source_column: str = Field(min_length=1)
    result_origin: Literal['paper_run', 'prior_paper']
    notes: str = ''

    @field_validator(
        'dataset_id', 'method_id', 'condition_id', 'protocol_id', 'metric_id'
    )
    @classmethod
    def validate_ids(cls, value: str, info):
        return _validate_id(value, info.field_name)

    @field_validator('score')
    @classmethod
    def finite_score(cls, value: float):
        if not math.isfinite(value):
            raise ValueError('score must be finite')
        return value

    @field_validator('reported_std', mode='before')
    @classmethod
    def empty_std_to_none(cls, value: Any):
        return None if value in ('', None) else str(value)


class SnapshotBundle(StrictModel):
    entry: CatalogEntry
    manifest: Manifest
    methods: list[Method]
    datasets: list[Dataset]
    protocols: list[Protocol]
    metrics: list[Metric]
    results: list[ResultCell]
    source_dir: Path

    @model_validator(mode='after')
    def validate_bundle(self):
        if self.entry.study_id != self.manifest.study_id:
            raise ValueError('catalog and manifest study_id differ')
        if self.entry.snapshot_id != self.manifest.snapshot_id:
            raise ValueError('catalog and manifest snapshot_id differ')

        def index(items: list[Any], name: str) -> dict[str, Any]:
            attr = f'{name}_id'
            out: dict[str, Any] = {}
            for item in items:
                key = getattr(item, attr)
                if key in out:
                    raise ValueError(f'duplicate {name}_id: {key}')
                out[key] = item
            return out

        methods = index(self.methods, 'method')
        datasets = index(self.datasets, 'dataset')
        protocols = index(self.protocols, 'protocol')
        metrics = index(self.metrics, 'metric')
        conditions = {c.condition_id: c for c in self.manifest.conditions}
        if len(conditions) != len(self.manifest.conditions):
            raise ValueError('duplicate condition_id')
        table_counts = Counter(row.source_table for row in self.results)
        expected_tables = {
            table.table_id: table.expected_results
            for table in self.manifest.source_tables
        }
        if len(expected_tables) != len(self.manifest.source_tables):
            raise ValueError('duplicate source table_id')
        table_pages = {
            table.table_id: str(table.page)
            for table in self.manifest.source_tables
        }
        if table_counts != Counter(expected_tables):
            raise ValueError(
                f'table counts differ: actual={dict(table_counts)} '
                f'expected={expected_tables}'
            )

        keys: set[tuple[str, ...]] = set()
        for row in self.results:
            for value, mapping, label in (
                (row.method_id, methods, 'method'),
                (row.dataset_id, datasets, 'dataset'),
                (row.protocol_id, protocols, 'protocol'),
                (row.metric_id, metrics, 'metric'),
                (row.condition_id, conditions, 'condition'),
            ):
                if value not in mapping:
                    raise ValueError(f'unknown {label}_id {value!r}')
            metric = metrics[row.metric_id]
            method = methods[row.method_id]
            if row.result_origin != method.default_result_origin:
                raise ValueError(
                    f'result origin differs from method declaration for '
                    f'{row.method_id}: {row.result_origin} vs '
                    f'{method.default_result_origin}'
                )
            if row.result_origin == 'prior_paper' and (
                method.evaluator_relationship != 'other'
            ):
                raise ValueError(
                    f'prior-paper method {row.method_id} must use '
                    'evaluator_relationship=other'
                )
            if row.source_page != table_pages[row.source_table]:
                raise ValueError(
                    f'source page differs for {row.source_table}: '
                    f'{row.source_page!r} vs {table_pages[row.source_table]!r}'
                )
            if not metric.min_score <= row.score <= metric.max_score:
                raise ValueError(
                    f'score {row.score} outside {metric.metric_id} bounds '
                    f'[{metric.min_score}, {metric.max_score}]'
                )
            dataset = datasets[row.dataset_id]
            protocol = protocols[row.protocol_id]
            if dataset.task_type != protocol.task_type and not (
                protocol.task_type == 'ddi_event_classification'
                and dataset.task_type.startswith('ddi_event_')
            ):
                raise ValueError(
                    f'task mismatch: dataset={dataset.task_type}, '
                    f'protocol={protocol.task_type}'
                )
            key = (
                row.dataset_id,
                row.method_id,
                row.condition_id,
                row.protocol_id,
                row.metric_id,
            )
            if key in keys:
                raise ValueError(f'duplicate logical result key: {key}')
            keys.add(key)
        if len(self.results) != self.manifest.expected_results:
            raise ValueError(
                f'expected {self.manifest.expected_results} results, '
                f'found {len(self.results)}'
            )
        log_keys = {
            (row.dataset_id, row.method_id, row.condition_id)
            for row in self.results
        }
        if len(log_keys) != self.manifest.expected_logs:
            raise ValueError(
                f'expected {self.manifest.expected_logs} logs, '
                f'found {len(log_keys)}'
            )
        return self
