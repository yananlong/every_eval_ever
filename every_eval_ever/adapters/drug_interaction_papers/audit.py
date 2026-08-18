"""Run the canonical experiment-plan audit blocks."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence

from . import adapter
from .audit_common import EVIDENCE_ROOT, _write
from .audit_conversion import block_b3
from .audit_negative import block_b4
from .audit_release import block_b5
from .audit_semantics import block_b2
from .audit_sources import block_b1

BLOCKS = {
    'B1': block_b1,
    'B2': block_b2,
    'B3': block_b3,
    'B4': block_b4,
    'B5': block_b5,
}


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--block', choices=[*BLOCKS, 'all'], default='all')
    parser.add_argument('--source-root', type=Path, default=adapter.DEFAULT_SOURCE_ROOT)
    parser.add_argument('--output', type=Path)
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> int:
    selected = list(BLOCKS) if args.block == 'all' else [args.block]
    if args.output and len(selected) != 1:
        raise ValueError('--output is valid only for one selected block')
    reports = {}
    for block in selected:
        report = BLOCKS[block](args.source_root)
        reports[block] = report
        output = (
            args.output
            if args.output and len(selected) == 1
            else EVIDENCE_ROOT / f'{block}-{block_name(block)}.json'
        )
        _write(report, output)
        print(f'{block}: {report["technical_status"]} -> {output}')
    return 0


def block_name(block: str) -> str:
    return {
        'B1': 'source-audit',
        'B2': 'semantic-audit',
        'B3': 'conversion-audit',
        'B4': 'negative-control-audit',
        'B5': 'release-audit',
    }[block]


def main(argv: Sequence[str] | None = None) -> int:
    try:
        return run(parse_args(argv))
    except Exception as exc:
        print(f'ERROR: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
