"""Atomic publication of validated adapter output."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Sequence

from every_eval_ever.eval_types import EvaluationLog
from every_eval_ever.helpers import EvaluationLogOutput, save_evaluation_logs

from .conversion import semantic_records, validate_built_logs
from .modeling import BuiltLog


def _read_staged_logs(root: Path) -> dict[str, dict[str, object]]:
    records: dict[str, dict[str, object]] = {}
    for path in sorted(root.rglob('*.json')):
        log = EvaluationLog.model_validate_json(path.read_text(encoding='utf-8'))
        if log.evaluation_id in records:
            raise ValueError(f'duplicate staged evaluation_id {log.evaluation_id}')
        records[log.evaluation_id] = log.model_dump(mode='json', exclude_none=True)
    return records


def export_logs(
    built: Sequence[BuiltLog],
    output_root: Path,
    *,
    replace: bool = False,
    _after_install=None,
) -> list[Path]:
    validate_built_logs(built)
    output_root = output_root.resolve()
    output_root.parent.mkdir(parents=True, exist_ok=True)
    collections = sorted({item.collection_slug for item in built})
    for collection in collections:
        final = output_root / collection
        if final.exists() and any(final.iterdir()) and not replace:
            raise FileExistsError(
                f'{final} is non-empty; pass --replace to replace adapter-owned output'
            )

    stage_root = Path(
        tempfile.mkdtemp(prefix='.drug-interaction-papers-stage-', dir=output_root.parent)
    )
    backup_root = Path(
        tempfile.mkdtemp(prefix='.drug-interaction-papers-backup-', dir=output_root.parent)
    )
    written: list[Path] = []
    moved_finals: list[tuple[Path, Path]] = []
    installed: list[Path] = []
    try:
        outputs = [
            EvaluationLogOutput(
                eval_log=item.log,
                base_dir=stage_root / item.collection_slug,
                developer=item.developer,
                model_name=item.model_name,
            )
            for item in built
        ]
        written.extend(save_evaluation_logs(outputs))
        staged = _read_staged_logs(stage_root)
        expected = semantic_records(built)
        if staged != expected:
            raise ValueError('staged output differs from in-memory semantic records')

        output_root.mkdir(parents=True, exist_ok=True)
        for collection in collections:
            final = output_root / collection
            staged_collection = stage_root / collection
            if final.exists():
                backup = backup_root / collection
                final.rename(backup)
                moved_finals.append((final, backup))
            staged_collection.rename(final)
            installed.append(final)
            if _after_install is not None:
                _after_install(final, len(installed))
    except Exception:
        for final in reversed(installed):
            if final.exists():
                shutil.rmtree(final)
        for final, backup in reversed(moved_finals):
            if backup.exists():
                backup.rename(final)
        raise
    finally:
        shutil.rmtree(stage_root, ignore_errors=True)
        shutil.rmtree(backup_root, ignore_errors=True)
    return [output_root / path.relative_to(stage_root) for path in written]
