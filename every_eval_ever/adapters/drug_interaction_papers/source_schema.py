"""Load and verify frozen drug-interaction source bundles."""

from __future__ import annotations

import csv
import hashlib
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from .source_catalog import AnchorLedger, Catalog, CatalogEntry
from .source_entities import Dataset, Manifest, Method, Metric, Protocol
from .source_results import ResultCell, SnapshotBundle


def load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding='utf-8'))
    except Exception as exc:
        raise ValueError(f'failed to load YAML {path}: {exc}') from exc


def bundle_digest(directory: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(directory.rglob('*')):
        if path.is_file():
            digest.update(path.relative_to(directory).as_posix().encode())
            digest.update(b'\0')
            digest.update(path.read_bytes())
            digest.update(b'\0')
    return digest.hexdigest()


def load_catalog(source_root: Path) -> Catalog:
    return Catalog.model_validate(load_yaml(source_root / 'catalog.yaml'))


def _load_rows(directory: Path) -> list[ResultCell]:
    paths = sorted(directory.glob('results-*.csv'))
    if not paths:
        raise ValueError(f'no result shards found in {directory}')
    rows: list[ResultCell] = []
    for path in paths:
        with path.open(newline='', encoding='utf-8') as handle:
            for line_number, raw in enumerate(csv.DictReader(handle), start=2):
                try:
                    rows.append(ResultCell.model_validate(raw))
                except Exception as exc:
                    raise ValueError(f'{path}:{line_number}: {exc}') from exc
    return rows


def load_snapshot(source_root: Path, entry: CatalogEntry) -> SnapshotBundle:
    directory = source_root / entry.study_id
    actual_digest = bundle_digest(directory)
    if actual_digest != entry.bundle_sha256:
        raise ValueError(
            f'{entry.snapshot_id}: bundle digest mismatch; '
            f'expected {entry.bundle_sha256}, got {actual_digest}'
        )
    manifest = Manifest.model_validate(load_yaml(source_root / entry.manifest))
    methods = [
        Method.model_validate(item)
        for item in load_yaml(directory / 'methods.yaml')['methods']
    ]
    datasets = [
        Dataset.model_validate(item)
        for item in load_yaml(directory / 'datasets.yaml')['datasets']
    ]
    protocols = [
        Protocol.model_validate(item)
        for item in load_yaml(directory / 'protocols.yaml')['protocols']
    ]
    metrics = [
        Metric.model_validate(item)
        for item in load_yaml(directory / 'metrics.yaml')['metrics']
    ]
    return SnapshotBundle(
        entry=entry,
        manifest=manifest,
        methods=methods,
        datasets=datasets,
        protocols=protocols,
        metrics=metrics,
        results=_load_rows(directory),
        source_dir=directory,
    )


def load_anchor_ledger(source_root: Path, catalog: Catalog) -> AnchorLedger:
    path = source_root / catalog.anchors_file
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != catalog.anchors_sha256:
        raise ValueError(
            f'anchor ledger digest mismatch: expected {catalog.anchors_sha256}, got {actual}'
        )
    return AnchorLedger.model_validate(load_yaml(path))


def validate_anchors(
    bundles: list[SnapshotBundle], ledger: AnchorLedger
) -> list[dict[str, object]]:
    cells = {}
    for bundle in bundles:
        for row in bundle.results:
            key = (
                bundle.manifest.snapshot_id, row.dataset_id, row.method_id,
                row.condition_id, row.protocol_id, row.metric_id,
            )
            cells[key] = row.score
    reports = []
    for anchor in ledger.anchors:
        key = (anchor.snapshot_id, anchor.dataset_id, anchor.method_id,
               anchor.condition_id, anchor.protocol_id, anchor.metric_id)
        actual = cells.get(key)
        if actual is None:
            raise ValueError(f'anchor cell not found: {key}')
        if actual != anchor.expected_score:
            raise ValueError(
                f'anchor mismatch {key}: expected {anchor.expected_score}, got {actual}'
            )
        reports.append({
            'key': '/'.join(key),
            'score': actual,
            'source_locator': anchor.source_locator,
        })
    return reports


def load_enabled_snapshots(source_root: Path) -> list[SnapshotBundle]:
    catalog = load_catalog(source_root)
    bundles = [
        load_snapshot(source_root, entry)
        for entry in catalog.snapshots
        if entry.enabled
    ]
    collection_slugs = [
        dataset.collection_slug
        for bundle in bundles
        for dataset in bundle.datasets
    ]
    duplicate_collections = [
        slug
        for slug, count in Counter(collection_slugs).items()
        if count > 1
    ]
    if duplicate_collections:
        raise ValueError(
            f'duplicate collection slugs across snapshots: '
            f'{duplicate_collections}'
        )
    result_count = sum(len(bundle.results) for bundle in bundles)
    log_count = sum(bundle.manifest.expected_logs for bundle in bundles)
    if result_count != catalog.totals.expected_results:
        raise ValueError('catalog expected_results does not match enabled bundles')
    if log_count != catalog.totals.expected_logs:
        raise ValueError('catalog expected_logs does not match enabled bundles')
    validate_anchors(bundles, load_anchor_ledger(source_root, catalog))

    return bundles
