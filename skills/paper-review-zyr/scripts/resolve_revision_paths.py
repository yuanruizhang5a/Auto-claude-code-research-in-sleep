#!/usr/bin/env python3
"""Resolve copy-on-write LaTeX paths for paper-review-zyr."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


REVISION_LINEAGE = re.compile(r"(?:_r[1-9][0-9]*)+$")
REVISION_NUMBER = re.compile(r"_r([1-9][0-9]*)")


def revision_path(source: Path) -> Path:
    """Return the first unused `_rN` sibling following the source lineage."""
    source = source.expanduser().resolve(strict=False)
    if source.suffix.lower() != ".tex":
        raise ValueError(f"expected a .tex path, got: {source}")

    stem = source.stem
    lineage = REVISION_LINEAGE.search(stem)
    if lineage:
        base = stem[: lineage.start()]
        numbers = [int(value) for value in REVISION_NUMBER.findall(lineage.group())]
        next_number = numbers[-1] + 1
    else:
        base = stem
        next_number = 1

    while True:
        candidate = source.with_name(f"{base}_r{next_number}{source.suffix}")
        if not candidate.exists():
            return candidate
        next_number += 1


def resolve_paths(paper: Path, review: Path, overwirte: bool) -> dict[str, object]:
    """Resolve source and output paths without creating or modifying files."""
    source_paper = paper.expanduser().resolve(strict=False)
    source_review = review.expanduser().resolve(strict=False)
    if source_paper.suffix.lower() != ".tex":
        raise ValueError(f"expected PAPER to be a .tex path, got: {source_paper}")
    if source_review.suffix.lower() != ".tex":
        raise ValueError(f"expected REVIEW to be a .tex path, got: {source_review}")

    return {
        "source_tex": str(source_paper),
        "output_tex": str(source_paper if overwirte else revision_path(source_paper)),
        "review_tex": str(source_review),
        "output_review_tex": str(
            source_review if overwirte else revision_path(source_review)
        ),
        "overwirte": overwirte,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve paper-review-zyr source and `_rN` output paths."
    )
    parser.add_argument("--paper", required=True, type=Path, help="source PAPER .tex")
    parser.add_argument("--review", required=True, type=Path, help="source REVIEW .tex")
    parser.add_argument(
        "--overwirte",
        action="store_true",
        help="return the source paths as outputs instead of `_rN` paths",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = resolve_paths(args.paper, args.review, args.overwirte)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
