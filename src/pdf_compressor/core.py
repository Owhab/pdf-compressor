"""Compression orchestration for a single PDF Document.

See CONTEXT.md: Compression, PDF Document.
"""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pikepdf

from .profiles import CompressionProfile
from .raster import compress_page_images
from .rasterize import rasterize_document
from .strip import strip_private_page_data


@dataclass
class CompressionResult:
    input_path: Path
    output_path: Path | None
    original_size: int
    compressed_size: int | None
    kept_original: bool
    images_downsampled: int = 0
    pages_rasterized: int = 0

    @property
    def reduction_ratio(self) -> float:
        if self.kept_original or not self.compressed_size:
            return 0.0
        return 1 - (self.compressed_size / self.original_size)


def compress_document(
    input_path: Path,
    output_path: Path,
    profile: CompressionProfile,
    *,
    password: str | None = None,
    rasterize: bool = False,
) -> CompressionResult:
    """Compress a single PDF Document per `profile`.

    Never leaves `output_path` populated with a file bigger than the input:
    if the recompressed PDF isn't smaller, nothing is written and
    `kept_original` is True on the result.

    `rasterize=True` is an explicit, opt-in Rasterization pass: every page's
    content (vector, text, and raster alike) is rendered to a single image
    at `profile.target_dpi` and the original content is discarded. This
    trades away text selectability/searchability for size, so it's never
    triggered implicitly — and it's incompatible with the Lossless profile
    (which has no target DPI to rasterize at).

    Raises `pikepdf.PasswordError` if the document is encrypted and
    `password` is wrong or missing, and `pikepdf.PdfError` if the input
    doesn't parse as a valid PDF.
    """
    if rasterize and not profile.downsamples_images:
        raise ValueError("rasterize requires a profile with a target DPI (visual or custom)")

    original_size = input_path.stat().st_size
    images_downsampled = 0
    pages_rasterized = 0

    with pikepdf.open(input_path, password=password or "") as pdf:
        if rasterize:
            pages_rasterized = rasterize_document(
                pdf, input_path, profile.target_dpi, profile.jpeg_quality, password=password
            )
        elif profile.downsamples_images:
            for page in pdf.pages:
                stats = compress_page_images(pdf, page, profile.target_dpi, profile.jpeg_quality)
                images_downsampled += stats.images_downsampled

        strip_private_page_data(pdf)

        for page in pdf.pages:
            page.remove_unreferenced_resources()

        save_kwargs: dict = dict(
            compress_streams=True,
            object_stream_mode=pikepdf.ObjectStreamMode.generate,
        )
        if pdf.is_encrypted:
            save_kwargs["encryption"] = pikepdf.Encryption(owner=password or "", user=password or "")

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        pdf.save(tmp_path, **save_kwargs)

    compressed_size = tmp_path.stat().st_size
    if compressed_size >= original_size:
        tmp_path.unlink()
        return CompressionResult(
            input_path=input_path,
            output_path=None,
            original_size=original_size,
            compressed_size=None,
            kept_original=True,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(tmp_path), str(output_path))
    return CompressionResult(
        input_path=input_path,
        output_path=output_path,
        original_size=original_size,
        compressed_size=compressed_size,
        kept_original=False,
        images_downsampled=images_downsampled,
        pages_rasterized=pages_rasterized,
    )
