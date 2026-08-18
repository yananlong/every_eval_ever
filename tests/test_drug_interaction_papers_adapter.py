"""Offline tests for the drug-interaction paper-results adapter."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from every_eval_ever.adapters.drug_interaction_papers import adapter, audit
from every_eval_ever.adapters.drug_interaction_papers.source_schema import (
    bundle_digest,
)
from every_eval_ever.eval_types import EvaluationLog


@pytest.fixture(scope='module')
def bundles():
    return adapter.load_snapshots()


def test_complete_source_universe(bundles):
    assert len(bundles) == 5
    assert sum(len(bundle.results) for bundle in bundles) == 548
    assert sum(bundle.manifest.expected_logs for bundle in bundles) == 99
    assert {bundle.manifest.study_id for bundle in bundles} == {
        'llmddi', 'textddi', 'zeroddi', 'exddi', 'dti-lm'
    }


def test_anchor_cells_are_frozen():
    report = audit.block_b1(adapter.DEFAULT_SOURCE_ROOT)
    assert report['technical_status'] == 'pass'
    assert report['anchor_count'] == 7
    assert report['independent_review_complete'] is False
    assert report['scientific_gate_status'] == 'blocked'


def test_semantic_protocols_and_licensing():
    report = audit.block_b2(adapter.DEFAULT_SOURCE_ROOT)
    assert report['semantic_invariant_violations'] == 0
    assert report['ambiguous_identity_count'] == 0
    assert report['leakage_findings'] == []
    tasks = report['dataset_task_map']
    assert tasks['textddi/drugbank'] == 'ddi_event_multiclass_classification'
    assert tasks['textddi/twosides'] == 'ddi_event_multilabel_classification'


def test_build_logs_exact_counts_and_unique_ids(bundles):
    built = adapter.build_logs(bundles)
    assert len(built) == 99
    results = [r for item in built for r in item.log.evaluation_results]
    assert len(results) == 548
    assert len({item.log.evaluation_id for item in built}) == 99
    assert len({r.evaluation_result_id for r in results}) == 548
    for item in built:
        EvaluationLog.model_validate(item.log.model_dump(mode='json'))


def test_reported_scales_are_not_rescaled(bundles):
    built = adapter.build_logs(bundles)
    by_id = {
        result.evaluation_result_id: result
        for item in built
        for result in item.log.evaluation_results
    }
    textddi = by_id[
        'textddi-emnlp-2023/drugbank/textddi/zero-shot/'
        'chronological-unseen-drug/f1-macro'
    ]
    assert textddi.score_details.score == 52.5
    assert textddi.metric_config.metric_unit == 'percent'
    assert textddi.metric_config.max_score == 100.0
    exddi = by_id[
        'exddi-arxiv-2409.05592-v2/ddinter/exddi-mts/default/'
        'two-unseen-drugs/rouge-l'
    ]
    assert exddi.score_details.score == 0.3294
    assert exddi.metric_config.metric_unit == 'proportion'


def test_repeated_run_variation_is_not_mislabeled_as_per_sample_uncertainty(
    bundles,
):
    built = adapter.build_logs(bundles, studies={'textddi'})
    result = next(
        r
        for item in built
        for r in item.log.evaluation_results
        if r.evaluation_result_id.endswith(
            'drugbank/textddi/zero-shot/chronological-unseen-drug/f1-macro'
        )
    )
    assert result.score_details.uncertainty is None
    assert result.score_details.details['reported_standard_deviation'] == '0.7'


def test_llmddi_snapshot_is_explicitly_preprint_versioned(bundles):
    bundle = next(b for b in bundles if b.manifest.study_id == 'llmddi')
    assert bundle.manifest.snapshot_id == 'llmddi-arxiv-2502.06890-v1'
    assert 'arXiv' in bundle.manifest.paper_version
    assert 'journal' in bundle.manifest.version_warning
    built = adapter.build_logs([bundle])
    assert all(
        'version_warning' in item.log.source_metadata.additional_details
        for item in built
    )


def test_filters_fail_on_unknown_and_preserve_explicit_scope(bundles):
    with pytest.raises(ValueError, match='unknown study'):
        adapter.build_logs(bundles, studies={'missing'})
    text = adapter.build_logs(bundles, studies={'textddi'}, datasets={'twosides'})
    assert len(text) == 20
    assert {item.collection_slug for item in text} == {'textddi-twosides'}


def test_export_is_logically_deterministic(tmp_path, bundles):
    built = adapter.build_logs(bundles)
    first = tmp_path / 'first'
    second = tmp_path / 'second'
    adapter.export_logs(built, first)
    adapter.export_logs(built, second)

    def read(root):
        return {
            log.evaluation_id: log.model_dump(mode='json', exclude_none=True)
            for path in root.rglob('*.json')
            for log in [EvaluationLog.model_validate_json(path.read_text())]
        }

    assert read(first) == read(second)
    assert len(list(first.rglob('*.json'))) == 99


def test_nonempty_destination_fails_without_mutation(tmp_path, bundles):
    built = adapter.build_logs(bundles, studies={'zeroddi'})
    occupied = tmp_path / 'zeroddi-drugbank'
    occupied.mkdir()
    sentinel = occupied / 'sentinel.txt'
    sentinel.write_text('original')
    with pytest.raises(FileExistsError):
        adapter.export_logs(built, tmp_path)
    assert sentinel.read_text() == 'original'


def test_replace_rolls_back_after_install_failure(tmp_path, bundles):
    built = adapter.build_logs(bundles, studies={'textddi'})
    prior = tmp_path / 'textddi-drugbank'
    prior.mkdir()
    sentinel = prior / 'sentinel.txt'
    sentinel.write_text('original')

    def fail(_path, count):
        if count == 1:
            raise OSError('injected')

    with pytest.raises(OSError, match='injected'):
        adapter.export_logs(
            built, tmp_path, replace=True, _after_install=fail
        )
    assert sentinel.read_text() == 'original'
    assert not (tmp_path / 'textddi-twosides').exists()


def test_digest_mismatch_fails_closed(tmp_path):
    source = tmp_path / 'sources'
    shutil.copytree(adapter.DEFAULT_SOURCE_ROOT, source)
    result_path = next(
        path for path in sorted((source / 'textddi').glob('results-*.csv'))
        if '52.5,52.5' in path.read_text(encoding='utf-8')
    )
    result_path.write_text(result_path.read_text().replace('52.5,52.5', '52.6,52.5', 1))
    with pytest.raises(ValueError, match='digest mismatch'):
        adapter.load_snapshots(source)


def test_duplicate_result_fails_even_with_refreshed_digest(tmp_path):
    source = tmp_path / 'sources'
    shutil.copytree(adapter.DEFAULT_SOURCE_ROOT, source)
    result_path = sorted((source / 'zeroddi').glob('results-*.csv'))[0]
    rows = result_path.read_text().splitlines()
    result_path.write_text('\n'.join(rows + [rows[1]]) + '\n')
    catalog_path = source / 'catalog.yaml'
    catalog = yaml.safe_load(catalog_path.read_text())
    for entry in catalog['snapshots']:
        if entry['study_id'] == 'zeroddi':
            entry['bundle_sha256'] = bundle_digest(source / 'zeroddi')
    catalog_path.write_text(yaml.safe_dump(catalog, sort_keys=False))
    with pytest.raises(ValueError, match='table counts differ|duplicate'):
        adapter.load_snapshots(source)


def test_all_experiment_audit_blocks_execute():
    reports = {
        'B1': audit.block_b1(adapter.DEFAULT_SOURCE_ROOT),
        'B2': audit.block_b2(adapter.DEFAULT_SOURCE_ROOT),
        'B3': audit.block_b3(adapter.DEFAULT_SOURCE_ROOT),
        'B4': audit.block_b4(adapter.DEFAULT_SOURCE_ROOT),
        'B5': audit.block_b5(adapter.DEFAULT_SOURCE_ROOT),
    }
    assert all(report['technical_status'] == 'pass' for report in reports.values())
    assert reports['B5']['scientific_gate_status'] == 'blocked'


def test_retrieval_and_repository_provenance_are_not_laundered(bundles):
    assert {bundle.manifest.retrieved_timestamp for bundle in bundles} == {
        '1786041600'
    }
    for bundle in bundles:
        assert bundle.manifest.retrieved_timestamp != str(
            bundle.manifest.publication_date
        )
        if bundle.manifest.repository_url:
            assert bundle.manifest.repository_commit is not None
            assert len(bundle.manifest.repository_commit) == 40
            assert bundle.manifest.repository_role.startswith('Supplementary')


def test_zeroddi_conditional_ratio_semantics_and_ablation_provenance(bundles):
    bundle = next(item for item in bundles if item.manifest.study_id == 'zeroddi')
    metrics = {item.metric_id: item for item in bundle.metrics}
    pu = metrics['zeroddi.unseen-conditional-accuracy-ratio']
    ps = metrics['zeroddi.seen-conditional-accuracy-ratio']
    assert pu.metric_kind == ps.metric_kind == 'conditional_accuracy_ratio'
    assert pu.parameters['denominator'] == 'unseen binary accuracy'
    assert ps.parameters['denominator'] == 'seen binary accuracy'
    methods = {item.method_id: item for item in bundle.methods}
    for method_id in ('zeroddi1', 'zeroddi2'):
        method = methods[method_id]
        assert method.is_paper_method is True
        assert method.evaluator_relationship == 'first_party'
        assert method.developer == 'wzy-Sarah'


def test_exddi_api_model_identity_remains_source_scoped(bundles):
    bundle = next(item for item in bundles if item.manifest.study_id == 'exddi')
    method = next(item for item in bundle.methods if item.method_id == 'exddi-ic')
    assert method.model_id == 'exddi-source/gpt-3.5-turbo'
    assert method.details['exact_release'] == 'not_reported'


def test_package_data_includes_frozen_sources_and_plan():
    root = Path(__file__).resolve().parents[1]
    pyproject = (root / 'pyproject.toml').read_text(encoding='utf-8')
    for pattern in (
        'adapters/drug_interaction_papers/**/*.yaml',
        'adapters/drug_interaction_papers/**/*.csv',
        'adapters/drug_interaction_papers/**/*.json',
        'adapters/**/*.md',
    ):
        assert pattern in pyproject


def test_cli_rejects_ignored_option_combinations(tmp_path):
    with pytest.raises(ValueError, match='requires --audit-only'):
        adapter.run(
            adapter.parse_args(
                ['--audit-output', str(tmp_path / 'audit.json')]
            )
        )
    with pytest.raises(ValueError, match='full frozen source universe'):
        adapter.run(adapter.parse_args(['--audit-only', '--study', 'textddi']))


def test_source_page_mismatch_fails_with_refreshed_digest(tmp_path):
    source = tmp_path / 'sources'
    shutil.copytree(adapter.DEFAULT_SOURCE_ROOT, source)
    result_path = sorted((source / 'zeroddi').glob('results-*.csv'))[0]
    result_path.write_text(
        result_path.read_text(encoding='utf-8').replace(
            ',Table 1,5,3DGT-DDI,', ',Table 1,6,3DGT-DDI,', 1
        ),
        encoding='utf-8',
    )
    catalog_path = source / 'catalog.yaml'
    catalog = yaml.safe_load(catalog_path.read_text(encoding='utf-8'))
    for entry in catalog['snapshots']:
        if entry['study_id'] == 'zeroddi':
            entry['bundle_sha256'] = bundle_digest(source / 'zeroddi')
    catalog_path.write_text(
        yaml.safe_dump(catalog, sort_keys=False), encoding='utf-8'
    )
    with pytest.raises(ValueError, match='source page differs'):
        adapter.load_snapshots(source)


def test_module_entrypoint_has_no_runpy_warning():
    import os
    import subprocess
    import sys

    env = dict(os.environ)
    env['PYTHONPATH'] = str(Path(__file__).parents[1])
    result = subprocess.run(
        [
            sys.executable,
            '-W',
            'error::RuntimeWarning',
            '-m',
            'every_eval_ever.adapters.drug_interaction_papers.adapter',
            '--list-snapshots',
        ],
        cwd=Path(__file__).parents[1],
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert 'llmddi-arxiv-2502.06890-v1' in result.stdout


def test_negative_control_evidence_is_deterministic():
    first = audit.block_b4(adapter.DEFAULT_SOURCE_ROOT)
    second = audit.block_b4(adapter.DEFAULT_SOURCE_ROOT)
    assert first == second
    assert '<TMP>' in str(first['outcomes'])
    assert '/tmp/tmp' not in str(first['outcomes'])
