"""Shared strict source-bundle validation primitives."""

from __future__ import annotations

import re
from pathlib import PurePosixPath

from pydantic import BaseModel, ConfigDict

_ID_RE = re.compile(r'^[a-z0-9][a-z0-9.-]*$')


def _validate_id(value: str, label: str) -> str:
    if not _ID_RE.fullmatch(value):
        raise ValueError(f'{label} must be a lowercase slug, got {value!r}')
    return value


def _validate_relative_path(value: str, label: str) -> str:
    path = PurePosixPath(value)
    if path.is_absolute() or '..' in path.parts or not path.parts:
        raise ValueError(f'{label} must be a safe relative path')
    return value


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

