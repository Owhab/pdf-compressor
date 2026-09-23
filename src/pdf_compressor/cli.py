"""Command-line entrypoint. See AGENTS.md / CONTEXT.md for background."""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

import pikepdf

from .batch import compress_batch
from .core import CompressionResult, compress_document
from .profiles import resolve_profile


def _default_output_path(input_path: Path) -> Path:
    return input_path.with_name(f"{input_path.stem}.compressed.pdf")


def _report_result(result: CompressionResult) -> None:
    if result.kept_original:
        print(f"{result.input_path}: 0% reduction, original kept")
        return
    before = result.original_size / 1_000_000
    after = (result.compressed_size or 0) / 1_000_000
    pct = result.reduction_ratio * 100
    print(f"{result.input_path}: {before:.1f}MB -> {after:.1f}MB ({pct:.0f}% reduction)")


def _resolve_password(cli_password: str | None, pdf_path: Path) -> str | None:
    if cli_password is not None:
        return cli_password
    try:
        pikepdf.open(pdf_path).close()
        return None
    except pikepdf.PasswordError:
        return getpass.getpass(f"Password for {pdf_path}: ")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdf-compress",
        description="Compress PDF file size without compromising document quality.",
    )
    parser.add_argument("input", type=Path, help="A PDF file, or a directory to compress as a Batch Job")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output path (single file only)")
    parser.add_argument("--profile", choices=["lossless", "visual", "custom"], default="visual")
    parser.add_argument("--dpi", type=int, default=None, help="Target DPI (only with --profile custom)")
    parser.add_argument("--jpeg-quality", type=int, default=None, help="JPEG quality 1-95 (only with --profile custom)")
    parser.add_argument("--in-place", action="store_true", help="Overwrite the input instead of writing a new file")
    parser.add_argument("--password", default=None, help="Password for an encrypted PDF Document (prompted if omitted and needed)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.profile != "custom" and (args.dpi is not None or args.jpeg_quality is not None):
        parser.error("--dpi/--jpeg-quality only apply with --profile custom")

    profile = resolve_profile(args.profile, dpi=args.dpi, jpeg_quality=args.jpeg_quality)

    if args.input.is_dir():
        if args.output is not None:
            parser.error("-o/--output isn't supported for a directory input; batch output goes to compressed/")
        return compress_batch(
            args.input, profile, in_place=args.in_place, password=args.password, report=_report_result
        )

    if not args.input.is_file():
        print(f"{args.input}: not a file or directory", file=sys.stderr)
        return 1

    output_path = args.input if args.in_place else (args.output or _default_output_path(args.input))
    password = _resolve_password(args.password, args.input)

    try:
        result = compress_document(args.input, output_path, profile, password=password)
    except pikepdf.PasswordError:
        print(f"{args.input}: wrong password", file=sys.stderr)
        return 1
    except pikepdf.PdfError as exc:
        print(f"{args.input}: not a valid PDF ({exc})", file=sys.stderr)
        return 1

    _report_result(result)
    return 0


if __name__ == "__main__":
    sys.exit(main())
