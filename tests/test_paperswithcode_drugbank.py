"""Regression coverage for the generic Papers with Code DrugBank table.

This fixture covers one aggregate PwC table: three model rows, each with AUROC,
Accuracy, and F1 score. It deliberately does **not** claim that this is complete
DrugBank benchmark coverage or assign transductive/inductive/OOD semantics that
the generic PwC row does not encode. DrugBank is dataset provenance here; split
semantics require a protocol-qualified leaderboard/source.
"""

from __future__ import annotations

import json

import pytest

from every_eval_ever.adapters.paperswithcode import adapter

DUMP_VERSION = '20260716'
RETRIEVED_TS = '1784160000.0'


def _dataset():
    return {
        'drugbank-id': {
            'id': 'drugbank-id',
            'name': 'DrugBank',
            'slug': 'drugbank',
            'hf_url': None,
            'url': 'https://go.drugbank.com',
            'homepage': 'https://go.drugbank.com',
            'paper_url': None,
            'license_name': 'Unknown',
            'license_url': None,
        }
    }


def _tasks():
    return {
        'ddi-task': {
            'id': 'ddi-task',
            'slug': 'drug-drug-interaction-extraction',
        }
    }


def _evaluations():
    # Protocol is intentionally absent. The generic PwC table is useful aggregate
    # evidence, but a dataset/task label is not enough to infer transductive,
    # one-/two-unseen-drug, scaffold-OOD, or other split semantics.
    common = {
        'task_id': 'ddi-task',
        'dataset_id': 'drugbank-id',
        'created_at': '2026-07-16 03:15:11+00',
        'hf_model_url': None,
        'is_open': 't',
        'external': 'f',
        'harness': None,
    }
    return [
        {
            **common,
            'id': 'drugbank-cadgl',
            'paper_id': 'cadgl-paper',
            'model_name': 'Ours (CADGL)',
            'evaluated_on': '2024-03-25',
            'metrics': json.dumps(
                {'AUROC': '99.49', 'Accuracy': '98.21', 'F1 score': '97.79'}
            ),
        },
        {
            **common,
            'id': 'drugbank-ssi-ddi',
            'paper_id': 'ssi-paper',
            'model_name': 'SSI-DDI',
            'evaluated_on': '2021-11-07',
            'metrics': json.dumps(
                {'AUROC': '98.95', 'Accuracy': '96.33', 'F1 score': '96.38'}
            ),
        },
        {
            **common,
            'id': 'drugbank-mhca-ddi',
            'paper_id': 'mhca-paper',
            'model_name': 'MHCA-DDI',
            'evaluated_on': '2019-05-02',
            'metrics': json.dumps(
                {'AUROC': '86.33', 'Accuracy': '78.51', 'F1 score': '83.31'}
            ),
        },
    ]


def _papers():
    return {
        'cadgl-paper': {
            'title': 'CADGL: Context-Aware Deep Graph Learning for Predicting Drug-Drug Interactions',
            'arxiv_id': '2403.17210',
            'source_url': 'https://arxiv.org/abs/2403.17210',
        },
        'ssi-paper': {
            'title': 'SSI-DDI: Substructure-Substructure Interactions for Drug-Drug Interaction Prediction',
            'arxiv_id': None,
            'source_url': 'https://academic.oup.com/bib/article/22/6/bbab133/6265181',
        },
        'mhca-paper': {
            'title': 'Drug-Drug Adverse Effect Prediction with Graph Co-Attention',
            'arxiv_id': '1905.00534',
            'source_url': 'https://arxiv.org/abs/1905.00534',
        },
    }


def _metric_ranges():
    return {
        'AUROC': (86.33, 99.49),
        'Accuracy': (78.51, 98.21),
        'F1 score': (83.31, 97.79),
    }


def _metric_meta():
    return {
        'AUROC': {'full_name': 'Area Under the ROC Curve', 'scale': '0-100'},
        'Accuracy': {'full_name': 'Accuracy', 'scale': '0-100'},
        'F1 score': {'full_name': 'F1 score', 'scale': '0-100'},
    }


def _convert():
    evaluations = _evaluations()
    resolver = adapter.MetricResolver(
        pwc_directions={
            'AUROC': 'higher_is_better',
            'Accuracy': 'higher_is_better',
            'F1 score': 'higher_is_better',
        }
    )
    group_values = {
        ('drugbank-id', metric): [
            float(json.loads(row['metrics'])[metric]) for row in evaluations
        ]
        for metric in ('AUROC', 'Accuracy', 'F1 score')
    }
    group_scales = adapter.build_group_scales(group_values, resolver)
    conversion = adapter.build_logs(
        evaluations,
        _dataset(),
        _tasks(),
        resolver,
        _metric_ranges(),
        _metric_meta(),
        _papers(),
        DUMP_VERSION,
        RETRIEVED_TS,
        group_scales=group_scales,
    )
    return conversion, resolver


def test_generic_drugbank_pwc_table_is_three_aggregate_logs_nine_scores():
    conversion, resolver = _convert()
    assert conversion.total_records == 3
    assert conversion.failures == []
    assert conversion.exclusions == []
    assert len(conversion.records) == 3

    results = [
        result
        for bundle in conversion.records
        for result in bundle.log.evaluation_results
    ]
    assert len(results) == 9
    assert {result.metric_config.metric_id for result in results} == {
        'auroc',
        'accuracy',
        'f1',
    }
    assert resolver.unresolved == {}
    assert resolver.scale_anomalies == {}

    for bundle in conversion.records:
        assert bundle.log.source_metadata.source_type.value == 'documentation'
        assert {r.source_data.dataset_name for r in bundle.log.evaluation_results} == {
            'DrugBank'
        }
        assert all(
            r.source_data.source_type == 'url'
            for r in bundle.log.evaluation_results
        )


def test_generic_drugbank_pwc_model_identities_are_not_placeholder_developers():
    conversion, _ = _convert()
    by_name = {bundle.log.model_info.name: bundle for bundle in conversion.records}
    assert by_name['Ours (CADGL)'].log.model_info.id == 'azminewasi/ours-cadgl'
    assert by_name['SSI-DDI'].log.model_info.id == 'kanz76/ssi-ddi'
    assert by_name['MHCA-DDI'].log.model_info.id == 'deac-et-al/mhca-ddi'
    assert {bundle.developer for bundle in conversion.records} == {
        'azminewasi',
        'kanz76',
        'deac-et-al',
    }


def test_generic_drugbank_pwc_percent_scores_are_canonicalized_without_losing_raw_values():
    conversion, _ = _convert()
    by_model_metric = {
        (bundle.log.model_info.name, result.metric_config.metric_id): result
        for bundle in conversion.records
        for result in bundle.log.evaluation_results
    }
    expected = {
        ('Ours (CADGL)', 'auroc'): (0.9949, '99.49'),
        ('Ours (CADGL)', 'accuracy'): (0.9821, '98.21'),
        ('Ours (CADGL)', 'f1'): (0.9779, '97.79'),
        ('SSI-DDI', 'auroc'): (0.9895, '98.95'),
        ('SSI-DDI', 'accuracy'): (0.9633, '96.33'),
        ('SSI-DDI', 'f1'): (0.9638, '96.38'),
        ('MHCA-DDI', 'auroc'): (0.8633, '86.33'),
        ('MHCA-DDI', 'accuracy'): (0.7851, '78.51'),
        ('MHCA-DDI', 'f1'): (0.8331, '83.31'),
    }
    assert set(by_model_metric) == set(expected)

    for key, (score, raw) in expected.items():
        result = by_model_metric[key]
        assert result.score_details.score == pytest.approx(score)
        assert result.score_details.details['raw_value'] == raw
        assert result.score_details.details['canonical_rescale_factor'] == '0.01'
        assert result.metric_config.metric_unit == 'proportion'
        assert (result.metric_config.min_score, result.metric_config.max_score) == (
            0.0,
            1.0,
        )
