"""B5 datastore release dry-run audit."""

import hashlib
import json
import re
import tempfile
from pathlib import Path

from . import adapter
from .audit_common import _base_report, _read_output, _scan_forbidden
from .audit_sources import block_b1


def block_b5(source_root: Path) -> dict[str, object]:
    bundles = adapter.load_snapshots(source_root)
    built = adapter.build_logs(bundles)
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / 'data'
        adapter.export_logs(built, root)
        records = _read_output(root)
        paths = sorted(root.rglob('*.json'))
        bad_paths = []
        for path in paths:
            parts = path.relative_to(root).parts
            if len(parts) != 4 or not re.fullmatch(
                r'[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\.json',
                parts[-1],
            ):
                bad_paths.append(str(path))
        leakage = _scan_forbidden(root)
        collection_counts = {}
        for path in paths:
            collection = path.relative_to(root).parts[0]
            collection_counts[collection] = collection_counts.get(collection, 0) + 1
        digest = hashlib.sha256(
            json.dumps(records, sort_keys=True, separators=(',', ':')).encode()
        ).hexdigest()
    if bad_paths or leakage or len(records) != 99:
        raise AssertionError(
            f'release audit failed bad_paths={bad_paths} leakage={leakage} '
            f'records={len(records)}'
        )
    b1 = block_b1(source_root)
    report = _base_report('B5')
    report.update(
        {
            'scientific_gate_status': (
                'pass' if b1['independent_review_complete'] else 'blocked'
            ),
            'scientific_gate_reason': (
                'Independent source review remains pending.'
                if not b1['independent_review_complete']
                else 'All release gates satisfied.'
            ),
            'log_count': len(records),
            'path_violation_count': 0,
            'leakage_findings': [],
            'duplicate_logical_id_count': 0,
            'collection_counts': collection_counts,
            'semantic_output_sha256': digest,
        }
    )
    return report
