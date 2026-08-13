"""Manifest, method, dataset, protocol, and metric models."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .source_base import StrictModel, _validate_id

class Condition(StrictModel):
    condition_id: str
    display_name: str
    details: dict[str, str] = Field(default_factory=dict)

    @field_validator('condition_id')
    @classmethod
    def validate_condition_id(cls, value: str):
        return _validate_id(value, 'condition_id')


class SourceTable(StrictModel):
    table_id: str
    page: int | str
    expected_results: int = Field(ge=1)


class Manifest(StrictModel):
    schema_version: Literal[1]
    study_id: str
    snapshot_id: str
    title: str
    paper_url: str
    paper_version: str
    publication_date: str
    retrieved_timestamp: str
    source_organization: str
    repository_url: str | None = None
    repository_commit: str | None = None
    repository_role: str | None = None
    source_document_sha256: str | None = None
    conditions: list[Condition]
    source_tables: list[SourceTable]
    expected_results: int = Field(ge=1)
    expected_logs: int = Field(ge=1)
    version_warning: str | None = None

    @field_validator('study_id', 'snapshot_id')
    @classmethod
    def validate_ids(cls, value: str, info):
        return _validate_id(value, info.field_name)

    @field_validator('repository_commit')
    @classmethod
    def validate_repository_commit(cls, value: str | None):
        if value is not None and (
            len(value) != 40 or any(c not in '0123456789abcdef' for c in value)
        ):
            raise ValueError('repository_commit must be a lowercase Git SHA')
        return value

    @field_validator('retrieved_timestamp')
    @classmethod
    def validate_retrieved_timestamp(cls, value: str):
        try:
            number = float(value)
        except ValueError as exc:
            raise ValueError('retrieved_timestamp must be Unix epoch seconds') from exc
        if not math.isfinite(number) or number <= 0:
            raise ValueError('retrieved_timestamp must be finite and positive')
        return value

    @field_validator('source_document_sha256')
    @classmethod
    def validate_document_sha(cls, value: str | None):
        if value is not None and (
            len(value) != 64 or any(c not in '0123456789abcdef' for c in value)
        ):
            raise ValueError('source_document_sha256 must be lowercase sha256')
        return value


class Method(StrictModel):
    method_id: str
    display_name: str
    model_id: str
    developer: str
    method_category: str
    evaluator_relationship: Literal[
        'first_party', 'third_party', 'collaborative', 'other'
    ]
    identity_status: Literal['verified', 'source_scoped', 'ambiguous']
    is_paper_method: bool
    default_result_origin: Literal['paper_run', 'prior_paper']
    details: dict[str, str] = Field(default_factory=dict)

    @field_validator('method_id')
    @classmethod
    def validate_method_id(cls, value: str):
        return _validate_id(value, 'method_id')

    @model_validator(mode='after')
    def valid_identity(self):
        if '/' not in self.model_id:
            raise ValueError('model_id must contain developer/model form')
        if self.model_id.split('/', 1)[0] != self.developer:
            raise ValueError('developer must match the model_id prefix')
        if self.identity_status == 'ambiguous':
            raise ValueError('ambiguous identities are not publishable')
        return self


class Dataset(StrictModel):
    dataset_id: str
    collection_slug: str
    display_name: str
    source_type: Literal['other', 'url']
    source_urls: list[str] = Field(min_length=1)
    dataset_version: str
    task_type: str
    details: dict[str, str] = Field(default_factory=dict)

    @field_validator('dataset_id', 'collection_slug')
    @classmethod
    def validate_ids(cls, value: str, info):
        return _validate_id(value, info.field_name)


class Protocol(StrictModel):
    protocol_id: str
    display_name: str
    task_type: str
    novelty: dict[str, str]
    candidate_label_space: str = 'reported_label_space'
    notes: str = ''

    @field_validator('protocol_id')
    @classmethod
    def validate_protocol_id(cls, value: str):
        return _validate_id(value, 'protocol_id')


class Metric(StrictModel):
    metric_id: str
    display_name: str
    metric_kind: str
    metric_unit: Literal['proportion', 'percent']
    lower_is_better: bool
    min_score: float
    max_score: float
    parameters: dict[str, str | int | float | bool | None] = Field(
        default_factory=dict
    )

    @field_validator('metric_id')
    @classmethod
    def validate_metric_id(cls, value: str):
        return _validate_id(value, 'metric_id')

    @model_validator(mode='after')
    def valid_bounds(self):
        if not math.isfinite(self.min_score) or not math.isfinite(self.max_score):
            raise ValueError('source metrics must have finite bounds')
        if self.min_score >= self.max_score:
            raise ValueError('metric min_score must be below max_score')
        return self
