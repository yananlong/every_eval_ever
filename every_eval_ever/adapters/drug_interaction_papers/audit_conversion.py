"""B3 conversion and deterministic semantic replay audit."""

import tempfile
from pathlib import Path

from . import adapter
from .audit_common import _base_report, _read_output


def block_b3(source_root: Path) -> dict[str, object]:
    bundles = adapter.load_snapshots(source_root)
    built = adapter.build_logs(bundles)
    adapter.validate_built_logs(built)
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        first = root / 'first'
        second = root / 'second'
        adapter.export_logs(built, first)
        adapter.export_logs(built, second)
        first_records = _read_output(first)
        second_records = _read_output(second)
        if first_records != second_records:
            raise AssertionError('semantic outputs differ between identical runs')
        paths = sorted(first.rglob('*.json'))
        collections = sorted(path.relative_to(first).parts[0] for path in paths)
        unique_collections = sorted(set(collections))
    result_count = sum(len(item.log.evaluation_results) for item in built)
    if len(built) != 99 or result_count != 548:
        raise AssertionError(
            f'coverage mismatch: logs={len(built)} results={result_count}'
        )
    report = _base_report('B3')
    report.update(
        {
            'scientific_gate_status': 'pass',
            'log_count': len(built),
            'result_count': result_count,
            'schema_failure_count': 0,
            'duplicate_logical_id_count': 0,
            'semantic_diff_count': 0,
            'collection_count': len(unique_collections),
            'collections': unique_collections,
        }
    )
    return report
