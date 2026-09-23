"""Batch Job orchestration — Compression over every PDF Document under a directory.

See CONTEXT.md: Batch Job.
"""

from __future__ import annotations

import getpass
from collections.abc import Callable, Iterator
from pathlib import Path

import pikepdf

from .core import CompressionResult, compress_document
from .profiles import CompressionProfile


def iter_pdf_paths(root: Path) -> Iterator[Path]:
    """Yield every `.pdf` file under `root`, recursing into subdirectories.

    Prints a warning (rather than skipping silently) for any non-PDF file
    encountered.
    """
    for path in sorted(root.rglob("*")):
        if path.is_dir():
            continue
        if path.suffix.lower() != ".pdf":
            print(f"skipping non-PDF file: {path}")
            continue
        yield path


def _resolve_password(cli_password: str | None, pdf_path: Path) -> str | None:
    if cli_password is not None:
        return cli_password
    try:
        pikepdf.open(pdf_path).close()
        return None
    except pikepdf.PasswordError:
        return getpass.getpass(f"Password for {pdf_path}: ")
    except pikepdf.PdfError:
        return None  # let compress_document raise the real error


def compress_batch(
    root: Path,
    profile: CompressionProfile,
    *,
    in_place: bool,
    password: str | None,
    report: Callable[[CompressionResult], None],
) -> int:
    """Run Compression over every PDF Document under `root`.

    Output mirrors `root`'s directory structure into a sibling `compressed/`
    directory, unless `in_place` is set. A single PDF Document that fails
    (wrong password, corrupt file) is logged and skipped rather than
    aborting the rest of the Batch Job. Returns a process exit code: 0 if
    every PDF Document succeeded, 1 if any failed.
    """
    output_root = root if in_place else root.parent / "compressed" / root.name
    failures: list[Path] = []
    succeeded = 0
    total_original = 0
    total_compressed = 0

    for pdf_path in iter_pdf_paths(root):
        relative = pdf_path.relative_to(root)
        output_path = pdf_path if in_place else output_root / relative
        doc_password = _resolve_password(password, pdf_path)

        try:
            result = compress_document(pdf_path, output_path, profile, password=doc_password)
        except pikepdf.PasswordError:
            print(f"{pdf_path}: wrong password, skipped")
            failures.append(pdf_path)
            continue
        except pikepdf.PdfError as exc:
            print(f"{pdf_path}: not a valid PDF, skipped ({exc})")
            failures.append(pdf_path)
            continue

        report(result)
        succeeded += 1
        total_original += result.original_size
        total_compressed += result.compressed_size or result.original_size

    total_pct = (1 - total_compressed / total_original) * 100 if total_original else 0.0
    print(f"\nBatch Job: {succeeded} compressed, {len(failures)} failed ({total_pct:.0f}% overall reduction)")
    return 1 if failures else 0
