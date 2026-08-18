"""B4 fail-closed and atomicity negative controls."""

import tempfile
from pathlib import Path
from typing import Callable

import yaml

from . import adapter
from .audit_common import (
    _base_report,
    _copy_sources,
    _expect_failure,
    _refresh_bundle_digest,
)


def _result_file(directory: Path, needle: str) -> Path:
    for path in sorted(directory.glob('results-*.csv')):
        if needle in path.read_text(encoding='utf-8'):
            return path
    raise AssertionError(f'no result shard contains {needle!r} in {directory}')
def block_b4(source_root: Path) -> dict[str, object]:
    outcomes = []
    with tempfile.TemporaryDirectory() as temp:
        temp_root = Path(temp)

        def expect(name: str, function: Callable[[], object]) -> dict[str, str]:
            return _expect_failure(
                name, function, redact_roots=(temp_root,)
            )
        # Byte mutation without catalog update: digest gate.
        mutated = _copy_sources(source_root, temp_root / 'digest')
        results = _result_file(mutated / 'textddi', '52.5,52.5')
        results.write_text(
            results.read_text(encoding='utf-8').replace('52.5,52.5', '52.6,52.5', 1),
            encoding='utf-8',
        )
        outcomes.append(
            expect('bundle_digest_mismatch', lambda: adapter.load_snapshots(mutated))
        )

        # Duplicate logical result with updated digest: semantic source gate.
        duplicated = _copy_sources(source_root, temp_root / 'duplicate')
        path = sorted((duplicated / 'zeroddi').glob('results-*.csv'))[0]
        lines = path.read_text(encoding='utf-8').splitlines()
        path.write_text('\n'.join(lines + [lines[1]]) + '\n', encoding='utf-8')
        _refresh_bundle_digest(duplicated, 'zeroddi')
        outcomes.append(
            expect(
                'duplicate_logical_cell',
                lambda: adapter.load_snapshots(duplicated),
            )
        )

        malformed = _copy_sources(source_root, temp_root / 'malformed')
        path = _result_file(malformed / 'dti-lm', ',0.951,0.951,')
        path.write_text(
            path.read_text(encoding='utf-8').replace(
                ',0.951,0.951,', ',not-a-number,0.951,', 1
            ),
            encoding='utf-8',
        )
        _refresh_bundle_digest(malformed, 'dti-lm')
        outcomes.append(
            expect(
                'malformed_numeric_score',
                lambda: adapter.load_snapshots(malformed),
            )
        )

        unknown_method = _copy_sources(source_root, temp_root / 'unknown-method')
        path = _result_file(unknown_method / 'textddi', 'drugbank,mlp,')
        path.write_text(
            path.read_text(encoding='utf-8').replace(
                'drugbank,mlp,', 'drugbank,missing-method,', 1
            ),
            encoding='utf-8',
        )
        _refresh_bundle_digest(unknown_method, 'textddi')
        outcomes.append(
            expect(
                'unknown_method_foreign_key',
                lambda: adapter.load_snapshots(unknown_method),
            )
        )

        path_traversal = _copy_sources(source_root, temp_root / 'path-traversal')
        catalog_path = path_traversal / 'catalog.yaml'
        raw_catalog = yaml.safe_load(catalog_path.read_text(encoding='utf-8'))
        raw_catalog['snapshots'][0]['manifest'] = '../../outside.yaml'
        catalog_path.write_text(
            yaml.safe_dump(raw_catalog, sort_keys=False), encoding='utf-8'
        )
        outcomes.append(
            expect(
                'catalog_path_traversal',
                lambda: adapter.load_snapshots(path_traversal),
            )
        )

        bundles = adapter.load_snapshots(source_root)
        outcomes.append(
            expect(
                'unknown_filter',
                lambda: adapter.build_logs(bundles, studies={'not-a-study'}),
            )
        )
        empty_selection = adapter.build_logs(
            bundles, studies={'textddi'}, datasets={'bindingdb'}
        )
        outcomes.append(
            expect(
                'empty_filter_intersection',
                lambda: adapter.validate_built_logs(empty_selection),
            )
        )
        built = adapter.build_logs(bundles, studies={'zeroddi'})

        # Non-empty destination without replace must remain unchanged.
        output = temp_root / 'occupied'
        occupied = output / built[0].collection_slug
        occupied.mkdir(parents=True)
        sentinel = occupied / 'sentinel.txt'
        sentinel.write_text('keep', encoding='utf-8')
        outcomes.append(
            expect(
                'nonempty_destination_without_replace',
                lambda: adapter.export_logs(built, output),
            )
        )
        if sentinel.read_text(encoding='utf-8') != 'keep':
            raise AssertionError('non-replace failure mutated prior output')

        # Failure after first collection install must roll back every prior dir.
        multi = adapter.build_logs(bundles, studies={'textddi'})
        rollback_root = temp_root / 'rollback'
        prior = rollback_root / 'textddi-drugbank'
        prior.mkdir(parents=True)
        (prior / 'sentinel.txt').write_text('original', encoding='utf-8')

        def fail_after_first(_path: Path, count: int) -> None:
            if count == 1:
                raise OSError('injected install failure')

        outcomes.append(
            expect(
                'install_failure_rollback',
                lambda: adapter.export_logs(
                    multi,
                    rollback_root,
                    replace=True,
                    _after_install=fail_after_first,
                ),
            )
        )
        if (prior / 'sentinel.txt').read_text(encoding='utf-8') != 'original':
            raise AssertionError('rollback did not restore prior output')
        if (rollback_root / 'textddi-twosides').exists():
            raise AssertionError('rollback left a partial second collection')

    report = _base_report('B4')
    report.update(
        {
            'scientific_gate_status': 'pass',
            'negative_control_count': len(outcomes),
            'accepted_negative_controls': 0,
            'outcomes': outcomes,
            'prior_output_mutations': 0,
            'partial_publications': 0,
        }
    )
    return report
