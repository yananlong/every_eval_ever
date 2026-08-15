"""Offline tests for reviewed PwC DrugBank protocol qualification."""

import json
from dataclasses import replace

import pytest

from every_eval_ever.adapters.paperswithcode import adapter, protocol_overlay

DUMP_VERSION = '20260716'
RETRIEVED_TS = '1784160000.0'
METRICS = ('AUROC', 'Accuracy', 'F1 score')


def _evaluations():
    common = {
        'task_id': 'ddi-task',
        'dataset_id': 'drugbank-id',
        'created_at': '2026-07-16 03:15:11+00',
        'is_open': 't',
        'external': 'f',
        'harness': None,
    }
    return [
        {
            **common,
            'id': 'drugbank-method-alpha',
            'paper_id': 'alpha-paper',
            'model_name': 'Method Alpha',
            'hf_model_url': 'https://huggingface.co/example-org/method-alpha',
            'evaluated_on': '2024-03-25',
            'metrics': json.dumps(
                {'AUROC': '99.49', 'Accuracy': '98.21', 'F1 score': '97.79'}
            ),
        },
        {
            **common,
            'id': 'drugbank-method-beta',
            'paper_id': 'beta-paper',
            'model_name': 'Method Beta',
            'hf_model_url': 'https://huggingface.co/example-org/method-beta',
            'evaluated_on': '2021-11-07',
            'metrics': json.dumps(
                {'AUROC': '98.95', 'Accuracy': '96.33', 'F1 score': '96.38'}
            ),
        },
    ]


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
    return {'ddi-task': {'id': 'ddi-task', 'slug': 'drug-drug-interaction-extraction'}}


def _papers():
    return {
        'alpha-paper': {
            'title': 'Synthetic Method Alpha Paper',
            'arxiv_id': None,
            'source_url': 'https://example.org/method-alpha',
        },
        'beta-paper': {
            'title': 'Synthetic Method Beta Paper',
            'arxiv_id': None,
            'source_url': 'https://example.org/method-beta',
        },
    }


def _ranges():
    return {
        'AUROC': (98.95, 99.49),
        'Accuracy': (96.33, 98.21),
        'F1 score': (96.38, 97.79),
    }


def _meta():
    return {
        'AUROC': {'full_name': 'Area Under the ROC Curve', 'scale': '0-100'},
        'Accuracy': {'full_name': 'Accuracy', 'scale': '0-100'},
        'F1 score': {'full_name': 'F1 score', 'scale': '0-100'},
    }


def _resolver():
    return adapter.MetricResolver(
        pwc_directions={name: 'higher_is_better' for name in METRICS}
    )


def _group_scales(evaluations, resolver):
    values = {
        ('drugbank-id', metric): [
            float(json.loads(row['metrics'])[metric]) for row in evaluations
        ]
        for metric in METRICS
    }
    return adapter.build_group_scales(values, resolver)


def _generic_conversion():
    evaluations = _evaluations()
    resolver = _resolver()
    conversion = adapter.build_logs(
        evaluations,
        _datasets(),
        _tasks(),
        resolver,
        _ranges(),
        _meta(),
        _papers(),
        DUMP_VERSION,
        RETRIEVED_TS,
        group_scales=_group_scales(evaluations, resolver),
    )
    assert conversion.failures == []
    return conversion, evaluations


def _novelty(**overrides):
    base = {
        'drug_entity_overlap': 'none-in-both-test-drugs',
        'target_entity_overlap': 'not-applicable',
        'relation_class_overlap': 'shared',
        'pair_overlap': 'none',
        'temporal_ordering': 'not-reported',
        'negative_sampling': 'paper-defined',
        'split_preprocessing': 'paper-defined',
    }
    return {**base, **overrides}


def _fingerprint(evaluation_id):
    row = next((row for row in _evaluations() if row['id'] == evaluation_id), None)
    if row is None:
        return '0' * 64
    return protocol_overlay.source_metrics_sha256(json.loads(row['metrics']))


def _entry(
    evaluation_id='drugbank-method-alpha',
    paper_id='alpha-paper',
    model_name='Method Alpha',
    protocol_id='one-unseen-drug',
    *,
    study_id='alpha-study',
    metrics=None,
    novelty=None,
):
    return {
        'pwc_evaluation_id': evaluation_id,
        'verified_against_dump_version': DUMP_VERSION,
        'anchors': {
            'paper_id': paper_id,
            'dataset_id': 'drugbank-id',
            'task_id': 'ddi-task',
            'model_name': model_name,
        },
        'source_metrics_sha256': _fingerprint(evaluation_id),
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
            'source_locator': 'Synthetic table / split definition',
            'verification_note': 'Synthetic fixture explicitly defines the split.',
        },
        'metrics': list(metrics or METRICS),
    }


def _overlay(*entries):
    return protocol_overlay.ProtocolOverlay.model_validate(
        {'schema_version': 1, 'entries': list(entries)}
    )


def _by_id(conversion):
    grouped = {}
    for bundle in conversion.records:
        for result in bundle.log.evaluation_results:
            key = result.score_details.details['pwc_evaluation_id']
            grouped.setdefault(key, []).append(result)
    return grouped


def test_empty_overlay_is_literal_noop_even_for_unusable_source_context():
    conversion, evaluations = _generic_conversion()
    duplicate_rows = [*evaluations, dict(evaluations[0])]
    assert (
        protocol_overlay.qualify_conversion(
            conversion, duplicate_rows, _overlay(), 'not-a-date'
        )
        is conversion
    )


def test_packaged_default_overlay_is_empty():
    overlay = protocol_overlay.load_default_drugbank_overlay()
    assert overlay.schema_version == 1 and overlay.entries == []


def test_synthetic_protocols_preserve_score_identity_and_provenance():
    conversion, evaluations = _generic_conversion()
    overlay = _overlay(
        _entry(novelty=_novelty(drug_entity_overlap='one-test-drug-unseen')),
        _entry(
            'drugbank-method-beta',
            'beta-paper',
            'Method Beta',
            'two-unseen-drugs',
            study_id='beta-study',
        ),
    )
    qualified = protocol_overlay.qualify_conversion(
        conversion, evaluations, overlay, DUMP_VERSION
    )
    generic = _by_id(conversion)
    by_id = _by_id(qualified)
    assert {r.evaluation_name for r in by_id['drugbank-method-alpha']} == {
        'alpha-study-drugbank.one-unseen-drug'
    }
    assert {r.evaluation_name for r in by_id['drugbank-method-beta']} == {
        'beta-study-drugbank.two-unseen-drugs'
    }
    for evaluation_id, results in by_id.items():
        assert [r.evaluation_result_id for r in results] == [
            r.evaluation_result_id for r in generic[evaluation_id]
        ]
        assert [r.score_details.score for r in results] == [
            r.score_details.score for r in generic[evaluation_id]
        ]
    assert all(
        bundle.log.source_metadata.source_name == 'Papers with Code'
        for bundle in qualified.records
    )
    sample = by_id['drugbank-method-alpha'][0]
    assert sample.score_details.details['protocol_source_metrics_sha256'] == (
        _fingerprint('drugbank-method-alpha')
    )


def test_build_logs_wrapper_applies_overlay():
    evaluations = _evaluations()
    resolver = _resolver()
    conversion = protocol_overlay.build_logs(
        evaluations,
        _datasets(),
        _tasks(),
        resolver,
        _ranges(),
        _meta(),
        _papers(),
        DUMP_VERSION,
        RETRIEVED_TS,
        overlay=_overlay(_entry(metrics=['AUROC'])),
        group_scales=_group_scales(evaluations, resolver),
    )
    by_metric = {
        result.metric_config.metric_name: result.evaluation_name
        for result in _by_id(conversion)['drugbank-method-alpha']
    }
    assert by_metric['AUROC'] == 'alpha-study-drugbank.one-unseen-drug'
    assert by_metric['Accuracy'].startswith('paperswithcode.')


def test_anchor_drift_is_rejected_when_overlay_is_applied():
    conversion, evaluations = _generic_conversion()
    with pytest.raises(ValueError, match='anchor drift'):
        protocol_overlay.qualify_conversion(
            conversion,
            evaluations,
            _overlay(_entry(paper_id='wrong')),
            DUMP_VERSION,
        )


@pytest.mark.parametrize(
    ('mutator', 'match'),
    [
        (
            lambda e: e.__setitem__('verified_against_dump_version', '20260229'),
            'valid YYYYMMDD calendar date',
        ),
        (
            lambda e: e['evidence'].__setitem__('source_url', 'example.org/paper'),
            r'absolute HTTP\(S\) URL',
        ),
        (
            lambda e: e.__setitem__('source_metrics_sha256', 'ABC'),
            'lowercase 64-character SHA-256',
        ),
        (
            lambda e: e.__setitem__('pwc_evaluation_id', '   '),
            'PwC evaluation id must be non-empty',
        ),
        (
            lambda e: e['anchors'].__setitem__('model_name', '   '),
            'protocol overlay anchors must be non-empty',
        ),
        (
            lambda e: e['qualification'].__setitem__('dataset_id', 'other-dataset'),
            'must target normalized dataset_id drugbank',
        ),
    ],
)
def test_invalid_review_metadata_is_rejected(mutator, match):
    entry = _entry()
    mutator(entry)
    with pytest.raises(ValueError, match=match):
        _overlay(entry)


def test_missing_source_evaluation_id_fails_closed():
    conversion, evaluations = _generic_conversion()
    broken = [dict(row) for row in evaluations]
    broken[0]['id'] = None
    with pytest.raises(ValueError, match='PwC source evaluation id must be non-empty'):
        protocol_overlay.qualify_conversion(
            conversion, broken, _overlay(_entry()), DUMP_VERSION
        )


def test_missing_row_and_metric_fail_closed():
    conversion, evaluations = _generic_conversion()
    with pytest.raises(ValueError, match='references missing PwC evaluation'):
        protocol_overlay.qualify_conversion(
            conversion,
            evaluations,
            _overlay(_entry('missing-evaluation')),
            DUMP_VERSION,
        )
    with pytest.raises(ValueError, match=r'selects missing metric\(s\)'):
        protocol_overlay.qualify_conversion(
            conversion,
            evaluations,
            _overlay(_entry(metrics=['Not reported'])),
            DUMP_VERSION,
        )


def test_explicit_metric_scope_is_required():
    entry = _entry()
    del entry['metrics']
    with pytest.raises(ValueError, match='metrics'):
        _overlay(entry)


def test_malformed_or_different_current_dump_requires_review():
    conversion, evaluations = _generic_conversion()
    overlay = _overlay(_entry())
    with pytest.raises(ValueError, match='current dump_version'):
        protocol_overlay.qualify_conversion(
            conversion, evaluations, overlay, 'pwc-latest'
        )
    with pytest.raises(ValueError, match='re-review is required'):
        protocol_overlay.qualify_conversion(
            conversion, evaluations, overlay, '20260717'
        )


def test_source_metrics_payload_drift_fails_closed():
    conversion, evaluations = _generic_conversion()
    drifted = [dict(row) for row in evaluations]
    drifted[0]['metrics'] = json.dumps(
        {'AUROC': '99.50', 'Accuracy': '98.21', 'F1 score': '97.79'}
    )
    with pytest.raises(ValueError, match='metrics payload drift'):
        protocol_overlay.qualify_conversion(
            conversion, drifted, _overlay(_entry()), DUMP_VERSION
        )


def test_missing_qualified_cell_after_generic_conversion_fails_closed():
    conversion, evaluations = _generic_conversion()
    stripped_records = []
    for bundle in conversion.records:
        results = [
            result
            for result in bundle.log.evaluation_results
            if not (
                result.score_details.details.get('pwc_evaluation_id')
                == 'drugbank-method-alpha'
                and result.metric_config.metric_name == 'AUROC'
            )
        ]
        stripped_records.append(
            replace(
                bundle,
                log=bundle.log.model_copy(update={'evaluation_results': results}),
            )
        )
    stripped = replace(conversion, records=stripped_records)
    with pytest.raises(ValueError, match='did not survive generic conversion'):
        protocol_overlay.qualify_conversion(
            stripped,
            evaluations,
            _overlay(_entry(metrics=['AUROC'])),
            DUMP_VERSION,
        )


def test_disjoint_metric_scopes_are_allowed_but_overlap_is_rejected():
    conversion, evaluations = _generic_conversion()
    overlay = _overlay(
        _entry(metrics=['AUROC']),
        _entry(protocol_id='two-unseen-drugs', metrics=['Accuracy', 'F1 score']),
    )
    qualified = protocol_overlay.qualify_conversion(
        conversion, evaluations, overlay, DUMP_VERSION
    )
    by_metric = {
        result.metric_config.metric_name: result.evaluation_name
        for result in _by_id(qualified)['drugbank-method-alpha']
    }
    assert by_metric['AUROC'].endswith('.one-unseen-drug')
    assert by_metric['Accuracy'].endswith('.two-unseen-drugs')

    with pytest.raises(ValueError, match='overlapping metric selectors'):
        _overlay(
            _entry(metrics=['AUROC', 'Accuracy']),
            _entry(protocol_id='two-unseen-drugs', metrics=['Accuracy']),
        )


def test_opaque_source_split_token_is_rejected():
    with pytest.raises(ValueError, match='opaque source split tokens'):
        _overlay(_entry(protocol_id='CS2'))
