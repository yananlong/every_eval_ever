"""B1 source-freeze and transcription-integrity audit."""

from pathlib import Path

from . import adapter
from .audit_common import _base_report
from .source_schema import load_anchor_ledger, load_catalog, validate_anchors


def block_b1(source_root: Path) -> dict[str, object]:
    bundles = adapter.load_snapshots(source_root)
    catalog = load_catalog(source_root)
    ledger = load_anchor_ledger(source_root, catalog)
    anchors = validate_anchors(bundles, ledger)
    retrieval_timestamps = {
        bundle.manifest.retrieved_timestamp for bundle in bundles
    }
    if retrieval_timestamps != {'1786041600'}:
        raise AssertionError(
            f'unexpected source freeze timestamps: {retrieval_timestamps}'
        )
    unpinned_repositories = [
        bundle.manifest.snapshot_id
        for bundle in bundles
        if bundle.manifest.repository_url
        and not bundle.manifest.repository_commit
    ]
    if unpinned_repositories:
        raise AssertionError(
            f'unpinned supplementary repositories: {unpinned_repositories}'
        )
    report = _base_report('B1')
    report.update(adapter.audit_sources(bundles))
    report.update(
        {
            'technical_status': 'pass',
            'anchor_count': len(anchors),
            'anchors': anchors,
            'verification_status': ledger.verification_status,
            'independent_review_complete': ledger.independent_review_complete,
            'scientific_gate_status': (
                'pass' if ledger.independent_review_complete else 'blocked'
            ),
            'scientific_gate_reason': (
                'Independent primary-source cell review remains pending.'
                if not ledger.independent_review_complete
                else 'Independent source review recorded.'
            ),
            'retrieved_timestamp': next(iter(retrieval_timestamps)),
            'unpinned_repository_count': 0,
        }
    )
    return report
