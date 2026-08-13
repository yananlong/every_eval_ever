"""Offline tests for reviewed protocol qualification of PwC DrugBank rows."""

from __future__ import annotations

import json

import pytest

from every_eval_ever.adapters.paperswithcode import adapter, protocol_overlay

DUMP_VERSION = '20260716'
RETRIEVED_TS = '1784160000.0'


def _datasets():
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
    ]


def _papers():
    return {
        'cadgl-paper': {
            'title': 'CADGL',
            'arxiv_id': '2403.17210',
            'source_url': 'https://arxiv.org/abs/2403.17210',
        },
        'ssi-paper': {
            'title': 'SSI-DDI',
            'arxiv_id': None,
            'source_url': 'https://academic.oup.com/bib/article/22/6/bbab133/6265181',
        },
    }


def _metric_ranges():
    return {
        'AUROC': (98.95, 99.49),
        'Accuracy': (96.33, 98.21),
        'F1 score': (96.38, 97.79),
    }


def _metric_meta():
    return {
        'AUROC': {'full_name': 'Area Under the ROC Curve', 'scale': '0-100'},
        'Accuracy': {'full_name': 'Accuracy', 'scale': '0-100'},
        'F1 score': {'full_name': 'F1 score', 'scale': '0-100'},
    }


def _resolver():
    return adapter.MetricResolver(
        pwc_directions={
            'AUROC': 'higher_is_better',
            'Accuracy': 'higher_is_better',
            'F1 score': 'higher_is_better',
        }
    )


def _generic_conversion():
    evaluations = _evaluations()
    resolver = _resolver()
    group_values = {
        ('drugbank-id', metric): [
            float(json.loads(row['metrics'])[metric]) for row in evaluations
        ]
        for metric in ('AUROC', 'Accuracy', 'F1 score')
    }
    conversion = adapter.build_logs(
        evaluations,
        _datasets(),
        _tasks(),
        resolver,
        _metric_ranges(),
        _metric_meta(),
        _papers(),
        DUMP_VERSION,
        RETRIEVED_TS,
        group_scales=adapter.build_group_scales(group_values, resolver),
    )
    assert conversion.failures == []
    return conversion, evaluations


def _novelty(**overrides):
    values = {
        'drug_entity_overlap': 'none-in-both-test-drugs',
        'target_entity_overlap': 'not-applicable',
        'relation_class_overlap': 'shared',
        'pair_overlap': 'none',
        'temporal_ordering': 'not-reported',
        'negative_sampling': 'paper-defined',
        'split_preprocessing': 'paper-defined',
    }
    return {**values, **overrides}


def _entry(
    evaluation_id,
    paper_id,
    model_name,
    protocol_id,
    *,
    study_id='example-study',
    metrics=None,
    novelty=None,
):
    payload = {
        'pwc_evaluation_id': evaluation_id,
        'verified_against_dump_version': DUMP_VERSION,
        'anchors': {
            'paper_id': paper_id,
            'dataset_id': 'drugbank-id',
            'task_id': 'ddi-task',
            'model_name': model_name,
        },
        'qualification': {
            'study_id': study_id,
            'dataset_id': 'drugbank',
            'task_id': 'ddi-event-multiclass',
            'collection_slug': f'{study_id}-drugbank',
            'protocol_id': protocol_id,
            'task_type': 'ddi-event-multiclass',
            'candidate_label_space': 'reported-relation-labels',
            'novelty': novelty or _novelty(),
        },
        'evidence': {
            'source_url': 'https://example.org/paper',
            'source_locator': 'Table 2 / split definition',
            'verification_note': 'Primary source explicitly defines the split.',
        },
    }
    if metrics is not None:
        payload['metrics'] = metrics
    return payload


def _overlay(*entries):
    return protocol_overlay.ProtocolOverlay.model_validate(
        {'schema_version': 1, 'entries': list(entries)}
    )


def _results_by_pwc_id(conversion):
    grouped = {}
    for bundle in conversion.records:
        for result in bundle.log.evaluation_results:
            grouped.setdefault(
                result.score_details.details['pwc_evaluation_id'], []
            ).append(result)
    return grouped


def test_empty_overlay_preserves_generic_conversion_unchanged():
    conversion, evaluations = _generic_conversion()
    qualified = protocol_overlay.qualify_conversion(
        conversion,
        evaluations,
        _overlay(),
        DUMP_VERSION,
    )
    assert qualified is conversion
    assert {
        result.evaluation_name
        for bundle in qualified.records
        for result in bundle.log.evaluation_results
    } == {'paperswithcode.drug_drug_interaction_extraction.drugbank'}


def test_empty_overlay_is_noop_before_source_row_validation():
    conversion, evaluations = _generic_conversion()
    duplicate_rows = [*evaluations, dict(evaluations[0])]
    assert (
        protocol_overlay.qualify_conversion(
            conversion,
            duplicate_rows,
            _overlay(),
            DUMP_VERSION,
        )
        is conversion
    )


def test_packaged_default_overlay_is_reviewed_empty_manifest():
    overlay = protocol_overlay.load_default_drugbank_overlay()
    assert overlay.schema_version == 1
    assert overlay.entries == []


def test_reviewed_unseen_drug_protocols_get_distinct_semantic_identities():
    conversion, evaluations = _generic_conversion()
    overlay = _overlay(
        _entry(
            'drugbank-cadgl',
            'cadgl-paper',
            'Ours (CADGL)',
            'one-unseen-drug',
            study_id='cadgl',
            novelty=_novelty(drug_entity_overlap='one-test-drug-unseen'),
        ),
        _entry(
            'drugbank-ssi-ddi',
            'ssi-paper',
            'SSI-DDI',
            'two-unseen-drugs',
            study_id='ssi-ddi',
        ),
    )
    qualified = protocol_overlay.qualify_conversion(
        conversion, evaluations, overlay, DUMP_VERSION
    )
    by_id = _results_by_pwc_id(qualified)

    assert {r.evaluation_name for r in by_id['drugbank-cadgl']} == {
        'cadgl-drugbank.one-unseen-drug'
    }
    assert {r.evaluation_name for r in by_id['drugbank-ssi-ddi']} == {
        'ssi-ddi-drugbank.two-unseen-drugs'
    }

    generic_by_id = _results_by_pwc_id(conversion)
    for evaluation_id in by_id:
        assert [r.evaluation_result_id for r in by_id[evaluation_id]] == [
            r.evaluation_result_id for r in generic_by_id[evaluation_id]
        ]
        assert [r.score_details.score for r in by_id[evaluation_id]] == [
            r.score_details.score for r in generic_by_id[evaluation_id]
        ]

    for bundle in qualified.records:
        assert bundle.log.source_metadata.source_name == 'Papers with Code'
    sample = by_id['drugbank-cadgl'][0]
    assert sample.score_details.details['protocol_evidence_url'] == (
        'https://example.org/paper'
    )
    assert sample.score_details.details['protocol_collection_slug'] == (
        'cadgl-drugbank'
    )
    assert sample.metric_config.additional_details['protocol_id'] == (
        'one-unseen-drug'
    )


def test_anchor_drift_fails_closed():
    conversion, evaluations = _generic_conversion()
    overlay = _overlay(
        _entry(
            'drugbank-cadgl',
            'wrong-paper',
            'Ours (CADGL)',
            'one-unseen-drug',
        )
    )
    with pytest.raises(ValueError, match='anchor drift'):
        protocol_overlay.qualify_conversion(
            conversion, evaluations, overlay, DUMP_VERSION
        )


def test_missing_overlay_source_row_fails_closed():
    conversion, evaluations = _generic_conversion()
    overlay = _overlay(
        _entry(
            'missing-evaluation',
            'cadgl-paper',
            'Ours (CADGL)',
            'one-unseen-drug',
        )
    )
    with pytest.raises(ValueError, match='references missing PwC evaluation'):
        protocol_overlay.qualify_conversion(
            conversion, evaluations, overlay, DUMP_VERSION
        )


def test_missing_metric_selector_fails_closed():
    conversion, evaluations = _generic_conversion()
    overlay = _overlay(
        _entry(
            'drugbank-cadgl',
            'cadgl-paper',
            'Ours (CADGL)',
            'one-unseen-drug',
            metrics=['Not reported'],
        )
    )
    with pytest.raises(ValueError, match=r'selects missing metric\(s\)'):
        protocol_overlay.qualify_conversion(
            conversion, evaluations, overlay, DUMP_VERSION
        )


def test_overlay_verified_against_newer_dump_fails_closed():
    conversion, evaluations = _generic_conversion()
    entry = _entry(
        'drugbank-cadgl',
        'cadgl-paper',
        'Ours (CADGL)',
        'one-unseen-drug',
    )
    entry['verified_against_dump_version'] = '20260717'
    overlay = _overlay(entry)
    with pytest.raises(ValueError, match='verified against newer dump'):
        protocol_overlay.qualify_conversion(
            conversion, evaluations, overlay, DUMP_VERSION
        )


def test_disjoint_metric_scopes_can_map_one_source_row_to_distinct_protocols():
    conversion, evaluations = _generic_conversion()
    overlay = _overlay(
        _entry(
            'drugbank-cadgl',
            'cadgl-paper',
            'Ours (CADGL)',
            'one-unseen-drug',
            study_id='cadgl',
            metrics=['AUROC'],
        ),
        _entry(
            'drugbank-cadgl',
            'cadgl-paper',
            'Ours (CADGL)',
            'two-unseen-drugs',
            study_id='cadgl',
            metrics=['Accuracy', 'F1 score'],
        ),
    )
    qualified = protocol_overlay.qualify_conversion(
        conversion, evaluations, overlay, DUMP_VERSION
    )
    by_metric = {
        result.metric_config.metric_name: result.evaluation_name
        for result in _results_by_pwc_id(qualified)['drugbank-cadgl']
    }
    assert by_metric == {
        'AUROC': 'cadgl-drugbank.one-unseen-drug',
        'Accuracy': 'cadgl-drugbank.two-unseen-drugs',
        'F1 score': 'cadgl-drugbank.two-unseen-drugs',
    }


def test_overlapping_metric_scoped_overlays_are_rejected():
    first = _entry(
        'drugbank-cadgl',
        'cadgl-paper',
        'Ours (CADGL)',
        'one-unseen-drug',
        metrics=['AUROC', 'Accuracy'],
    )
    second = _entry(
        'drugbank-cadgl',
        'cadgl-paper',
        'Ours (CADGL)',
        'two-unseen-drugs',
        metrics=['Accuracy', 'F1 score'],
    )
    with pytest.raises(ValueError, match='overlapping metric selectors'):
        _overlay(first, second)


def test_opaque_paper_split_tokens_are_not_normalized_protocol_ids():
    with pytest.raises(ValueError, match='opaque source split tokens'):
        _overlay(
            _entry(
                'drugbank-cadgl',
                'cadgl-paper',
                'Ours (CADGL)',
                'CS2',
            )
        )
