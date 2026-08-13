"""Catalog and source-verification ledger models."""

from __future__ import annotations

from collections import Counter
from typing import Literal

from pydantic import Field, field_validator, model_validator

from .source_base import StrictModel, _validate_id, _validate_relative_path


class CatalogEntry(StrictModel):
    study_id: str
    snapshot_id: str
    enabled: bool = True
    manifest: str
    bundle_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')

    @field_validator('study_id', 'snapshot_id')
    @classmethod
    def validate_ids(cls, value: str, info):
        return _validate_id(value, info.field_name)

    @field_validator('manifest')
    @classmethod
    def validate_manifest_path(cls, value: str):
        return _validate_relative_path(value, 'manifest')


class CatalogTotals(StrictModel):
    expected_results: int = Field(ge=1)
    expected_logs: int = Field(ge=1)


class Catalog(StrictModel):
    schema_version: Literal[1]
    snapshots: list[CatalogEntry]
    totals: CatalogTotals
    anchors_file: str
    anchors_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')

    @field_validator('anchors_file')
    @classmethod
    def validate_anchors_path(cls, value: str):
        return _validate_relative_path(value, 'anchors_file')

    @model_validator(mode='after')
    def unique_entries(self):
        for attr in ('study_id', 'snapshot_id'):
            values = [getattr(item, attr) for item in self.snapshots]
            duplicates = [v for v, count in Counter(values).items() if count > 1]
            if duplicates:
                raise ValueError(f'duplicate catalog {attr}: {duplicates}')
        return self


class Anchor(StrictModel):
    snapshot_id: str
    dataset_id: str
    method_id: str
    condition_id: str
    protocol_id: str
    metric_id: str
    expected_score: float
    source_locator: str


class AnchorLedger(StrictModel):
    schema_version: Literal[1]
    verification_status: Literal[
        'single_reviewer_primary_source_check', 'independently_verified'
    ]
    independent_review_complete: bool
    independent_reviewer: str | None = None
    independent_review_date: str | None = None
    independent_review_notes: str | None = None
    anchors: list[Anchor] = Field(min_length=1)

    @model_validator(mode='after')
    def consistent_assurance(self):
        independently_verified = (
            self.verification_status == 'independently_verified'
        )
        if independently_verified != self.independent_review_complete:
            raise ValueError(
                'independent_review_complete must agree with verification_status'
            )
        review_fields = (
            self.independent_reviewer,
            self.independent_review_date,
            self.independent_review_notes,
        )
        if self.independent_review_complete and not all(review_fields):
            raise ValueError(
                'independent verification requires reviewer, date, and notes'
            )
        if not self.independent_review_complete and any(review_fields):
            raise ValueError(
                'independent review metadata cannot be set before completion'
            )
        return self
