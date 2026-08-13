"""Convert frozen paper tables into aggregate Every Eval Ever records."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .conversion import build_logs
from .publication import export_logs
from .source_schema import (
    Catalog,
    load_catalog as _load_catalog,
    load_enabled_snapshots,
    load_snapshot as _load_snapshot,
    SnapshotBundle,
)

PACKAGE_ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE_ROOT = PACKAGE_ROOT / 'sources'
DEFAULT_OUTPUT_ROOT = Path('data')


def load_catalog(source_root: Path | None = None) -> Catalog:
    return _load_catalog(source_root or DEFAULT_SOURCE_ROOT)


def load_snapshot(
    snapshot_id: str, source_root: Path | None = None
) -> SnapshotBundle:
    root = source_root or DEFAULT_SOURCE_ROOT
    catalog = _load_catalog(root)
    matches = [item for item in catalog.snapshots if item.snapshot_id == snapshot_id]
    if len(matches) != 1:
        raise ValueError(f'unknown or duplicate snapshot_id: {snapshot_id!r}')
    return _load_snapshot(root, matches[0])


def load_snapshots(source_root: Path | None = None) -> list[SnapshotBundle]:
    return load_enabled_snapshots(source_root or DEFAULT_SOURCE_ROOT)


def audit_sources(bundles: Sequence[SnapshotBundle]) -> dict[str, object]:
    snapshots = []
    for bundle in bundles:
        snapshots.append(
            {
                'study_id': bundle.manifest.study_id,
                'snapshot_id': bundle.manifest.snapshot_id,
                'result_count': len(bundle.results),
                'expected_results': bundle.manifest.expected_results,
                'log_count': len(
                    {
                        (row.dataset_id, row.method_id, row.condition_id)
                        for row in bundle.results
                    }
                ),
                'expected_logs': bundle.manifest.expected_logs,
                'bundle_sha256': bundle.entry.bundle_sha256,
                'source_document_sha256_status': (
                    'recorded'
                    if bundle.manifest.source_document_sha256
                    else 'not_recorded'
                ),
                'paper_version': bundle.manifest.paper_version,
                'version_warning': bundle.manifest.version_warning,
            }
        )
    return {
        'status': 'pass',
        'snapshot_count': len(bundles),
        'result_count': sum(len(bundle.results) for bundle in bundles),
        'log_count': sum(bundle.manifest.expected_logs for bundle in bundles),
        'snapshots': snapshots,
        'assurance_note': (
            'Bundle hashes and schema checks establish internal integrity only. '
            'They do not independently verify table transcription.'
        ),
    }


def write_audit(report: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + '\n',
        encoding='utf-8',
    )


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument('--output-dir', type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument('--study', action='append', default=[])
    parser.add_argument('--dataset', action='append', default=[])
    parser.add_argument('--snapshot', action='append', default=[])
    parser.add_argument('--replace', action='store_true')
    parser.add_argument('--audit-only', action='store_true')
    parser.add_argument('--audit-output', type=Path)
    parser.add_argument('--list-snapshots', action='store_true')
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> int:
    selection_requested = bool(args.study or args.dataset or args.snapshot)
    if args.audit_output and not args.audit_only:
        raise ValueError('--audit-output requires --audit-only')
    if args.audit_only and selection_requested:
        raise ValueError('--audit-only audits the full frozen source universe')
    if args.list_snapshots and (selection_requested or args.audit_only):
        raise ValueError('--list-snapshots cannot be combined with audit or filters')
    bundles = load_enabled_snapshots(args.source_root)
    if args.list_snapshots:
        for bundle in bundles:
            print(bundle.manifest.snapshot_id)
        return 0
    report = audit_sources(bundles)
    if args.audit_only:
        if args.audit_output:
            write_audit(report, args.audit_output)
        else:
            print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    built = build_logs(
        bundles,
        studies=set(args.study) or None,
        datasets=set(args.dataset) or None,
        snapshots=set(args.snapshot) or None,
    )
    paths = export_logs(built, args.output_dir, replace=args.replace)
    print(
        f'Wrote {len(paths)} logs with '
        f'{sum(len(item.log.evaluation_results) for item in built)} results.'
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(parse_args(argv))
    except Exception as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
