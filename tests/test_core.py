from __future__ import annotations

import pikepdf
import pytest

from pdf_compressor.core import compress_document
from pdf_compressor.profiles import LOSSLESS, VISUALLY_LOSSLESS, resolve_profile


def test_visually_lossless_shrinks_large_scanned_page(make_pdf_with_image, tmp_path):
    # 2550x3300 at a US-Letter page is 300 DPI: well above the 150 DPI default.
    input_path = make_pdf_with_image("scan.pdf", pixel_size=(2550, 3300))
    output_path = tmp_path / "scan.compressed.pdf"

    result = compress_document(input_path, output_path, VISUALLY_LOSSLESS)

    assert result.kept_original is False
    assert result.compressed_size < result.original_size
    assert result.images_downsampled == 1
    assert output_path.exists()

    with pikepdf.open(output_path) as pdf:
        image = next(iter(pdf.pages[0].get_images().values()))
        pdfimage = pikepdf.PdfImage(image)
        # 150 DPI * 8.5in page width, give or take rounding.
        assert 1270 <= pdfimage.width <= 1280


def test_lossless_never_downsamples(make_pdf_with_image, tmp_path):
    input_path = make_pdf_with_image("scan.pdf", pixel_size=(2550, 3300))
    output_path = tmp_path / "scan.compressed.pdf"

    result = compress_document(input_path, output_path, LOSSLESS)

    assert result.images_downsampled == 0
    if not result.kept_original:
        with pikepdf.open(output_path) as pdf:
            image = next(iter(pdf.pages[0].get_images().values()))
            assert pikepdf.PdfImage(image).width == 2550


def test_no_gain_keeps_original(make_text_pdf, tmp_path):
    # A tiny text-only PDF has nothing for either profile to usefully shrink.
    input_path = make_text_pdf()
    output_path = tmp_path / "text.compressed.pdf"

    result = compress_document(input_path, output_path, VISUALLY_LOSSLESS)

    assert result.kept_original is True
    assert result.output_path is None
    assert result.compressed_size is None
    assert result.reduction_ratio == 0.0
    assert not output_path.exists()
    assert input_path.exists()  # original untouched


def test_encrypted_pdf_round_trips_with_same_password(make_pdf_with_image, tmp_path):
    input_path = make_pdf_with_image("secret.pdf", pixel_size=(2550, 3300), password="hunter2")
    output_path = tmp_path / "secret.compressed.pdf"

    with pytest.raises(pikepdf.PasswordError):
        pikepdf.open(input_path)

    result = compress_document(input_path, output_path, VISUALLY_LOSSLESS, password="hunter2")

    assert result.output_path is not None
    with pytest.raises(pikepdf.PasswordError):
        pikepdf.open(output_path)
    with pikepdf.open(output_path, password="hunter2") as pdf:
        assert len(pdf.pages) == 1


def test_wrong_password_raises(make_pdf_with_image, tmp_path):
    input_path = make_pdf_with_image("secret.pdf", pixel_size=(2550, 3300), password="hunter2")
    output_path = tmp_path / "secret.compressed.pdf"

    with pytest.raises(pikepdf.PasswordError):
        compress_document(input_path, output_path, VISUALLY_LOSSLESS, password="wrong")


def test_custom_dpi_overrides_default(make_pdf_with_image, tmp_path):
    input_path = make_pdf_with_image("scan.pdf", pixel_size=(2550, 3300))
    output_path = tmp_path / "scan.compressed.pdf"
    profile = resolve_profile("custom", dpi=75, jpeg_quality=50)

    result = compress_document(input_path, output_path, profile)

    assert result.images_downsampled == 1
    with pikepdf.open(output_path) as pdf:
        image = next(iter(pdf.pages[0].get_images().values()))
        pdfimage = pikepdf.PdfImage(image)
        assert 630 <= pdfimage.width <= 640  # 75 DPI * 8.5in
