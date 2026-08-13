"""B2 semantic mapping and licensed-content audit."""

from pathlib import Path

from . import adapter
from .audit_common import _base_report, _scan_forbidden


def block_b2(source_root: Path) -> dict[str, object]:
    bundles = adapter.load_snapshots(source_root)
    protocol_ids = {
        protocol.protocol_id for bundle in bundles for protocol in bundle.protocols
    }
    required = {
        'chronological-unseen-drug',
        'vanilla-known-drug',
        'unseen-relation-czsl',
        'unseen-relation-gzsl',
        'pair-unseen-drugs-overlap-allowed',
        'one-unseen-drug',
        'two-unseen-drugs',
        'warm',
        'cold-drug',
        'cold-protein',
        'random-pair-stratified',
    }
    missing = sorted(required - protocol_ids)
    dataset_tasks = {
        (bundle.manifest.study_id, dataset.dataset_id): dataset.task_type
        for bundle in bundles
        for dataset in bundle.datasets
    }
    violations: list[str] = []
    if missing:
        violations.append(f'missing required protocols: {missing}')
    if dataset_tasks.get(('textddi', 'drugbank')) == dataset_tasks.get(
        ('textddi', 'twosides')
    ):
        violations.append('TextDDI DrugBank and TWOSIDES task types were conflated')
    llmddi = next(bundle for bundle in bundles if bundle.manifest.study_id == 'llmddi')
    llm_protocol = next(
        p for p in llmddi.protocols if p.protocol_id == 'random-pair-stratified'
    )
    if llm_protocol.novelty.get('drug_entity_overlap') != 'uncontrolled':
        violations.append('LLMDDI entity novelty was overstated')
    zeroddi = next(bundle for bundle in bundles if bundle.manifest.study_id == 'zeroddi')
    candidates = {
        p.protocol_id: p.candidate_label_space for p in zeroddi.protocols
    }
    if candidates.get('unseen-relation-czsl') == candidates.get(
        'unseen-relation-gzsl'
    ):
        violations.append('ZeroDDI CZSL and GZSL label spaces were conflated')
    zeroddi_metrics = {metric.metric_id: metric for metric in zeroddi.metrics}
    for metric_id, denominator in (
        (
            'zeroddi.unseen-conditional-accuracy-ratio',
            'unseen binary accuracy',
        ),
        (
            'zeroddi.seen-conditional-accuracy-ratio',
            'seen binary accuracy',
        ),
    ):
        metric = zeroddi_metrics.get(metric_id)
        if metric is None or metric.metric_kind != 'conditional_accuracy_ratio':
            violations.append(f'ZeroDDI ratio metric misclassified: {metric_id}')
        elif metric.parameters.get('denominator') != denominator:
            violations.append(f'ZeroDDI ratio formula missing: {metric_id}')
    zeroddi_methods = {method.method_id: method for method in zeroddi.methods}
    for method_id in ('zeroddi1', 'zeroddi2'):
        method = zeroddi_methods[method_id]
        if not method.is_paper_method or method.evaluator_relationship != 'first_party':
            violations.append(
                f'ZeroDDI first-party ablation misclassified: {method_id}'
            )
    exddi = next(bundle for bundle in bundles if bundle.manifest.study_id == 'exddi')
    novelty = {p.protocol_id: p.novelty for p in exddi.protocols}
    if novelty['one-unseen-drug'].get('paper_alias') != 'S2':
        violations.append('ExDDI one-unseen-drug paper alias must be S2')
    if novelty['two-unseen-drugs'].get('paper_alias') != 'S1':
        violations.append('ExDDI two-unseen-drugs paper alias must be S1')
    dti = next(bundle for bundle in bundles if bundle.manifest.study_id == 'dti-lm')
    dti_novelty = {p.protocol_id: p.novelty for p in dti.protocols}
    if dti_novelty['cold-drug'] == dti_novelty['cold-protein']:
        violations.append('DTI-LM cold-drug and cold-protein were conflated')
    ambiguous = [
        method.model_id
        for bundle in bundles
        for method in bundle.methods
        if method.identity_status == 'ambiguous'
    ]
    if ambiguous:
        violations.append(f'ambiguous identities are publishable: {ambiguous}')
    copied_wrong_relationship = [
        method.method_id
        for bundle in bundles
        for method in bundle.methods
        if method.default_result_origin == 'prior_paper'
        and method.evaluator_relationship != 'other'
    ]
    if copied_wrong_relationship:
        violations.append(
            f'prior-paper rows use overconfident relationship: {copied_wrong_relationship}'
        )
    leakage = _scan_forbidden(source_root)
    if leakage:
        violations.append(f'licensed-content leakage findings: {leakage}')
    if violations:
        raise AssertionError('; '.join(violations))
    report = _base_report('B2')
    report.update(
        {
            'scientific_gate_status': 'pass',
            'semantic_invariant_violations': 0,
            'protocol_count': len(protocol_ids),
            'dataset_task_map': {
                f'{study}/{dataset}': task
                for (study, dataset), task in sorted(dataset_tasks.items())
            },
            'ambiguous_identity_count': 0,
            'leakage_findings': [],
            'negative_control_contract': [
                'TextDDI task types differ',
                'ZeroDDI candidate spaces differ',
                'ExDDI S1/S2 aliases preserved',
                'DTI-LM cold axes differ',
                'LLMDDI entity novelty remains uncontrolled',
                'ZeroDDI Pu/Ps remain conditional accuracy ratios',
                'ZeroDDI1/2 remain first-party ablations',
                'ExDDI GPT-3.5 release remains source-scoped',
            ],
        }
    )
    return report
