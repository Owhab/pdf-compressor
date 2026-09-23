from __future__ import annotations

import pikepdf
import pytest

from pdf_compressor.core import compress_document
from pdf_compressor.profiles import LOSSLESS, VISUALLY_LOSSLESS


def test_rasterize_replaces_bloated_vector_content_with_a_smaller_image(make_bloated_vector_pdf, tmp_path):
    input_path = make_bloated_vector_pdf()
    output_path = tmp_path / "bloated.compressed.pdf"

    result = compress_document(input_path, output_path, VISUALLY_LOSSLESS, rasterize=True)

    assert result.pages_rasterized == 1
    assert result.kept_original is False
    assert result.compressed_size < result.original_size
    assert result.output_path is not None

    with pikepdf.open(result.output_path) as pdf:
        page = pdf.pages[0]
        images = list(page.get_images().values())
        assert len(images) == 1
        content = page.Contents.read_bytes()
        assert b" rg " not in content  # the original per-shape fill operators are gone
        assert b"/Im0 Do" in content


def test_rasterize_replaces_page_content_with_an_image(make_text_pdf, tmp_path):
    """Structural check, independent of whether the result is smaller: the
    text/Font content is gone and a single image XObject stands in for it.
    """
    input_path = make_text_pdf()
    output_path = tmp_path / "text.rasterized.pdf"

    with pikepdf.open(input_path) as pdf:
        from pdf_compressor.rasterize import rasterize_document

        rasterize_document(pdf, input_path, 150, 80)
        pdf.save(output_path)

    with pikepdf.open(output_path) as pdf:
        page = pdf.pages[0]
        assert "/Font" not in page.get("/Resources", {})
        images = list(page.get_images().values())
        assert len(images) == 1
        content = page.Contents.read_bytes()
        assert b"Tj" not in content
        assert b"/Im0 Do" in content


def test_rasterize_requires_target_dpi(make_text_pdf, tmp_path):
    input_path = make_text_pdf()
    output_path = tmp_path / "text.compressed.pdf"

    with pytest.raises(ValueError):
        compress_document(input_path, output_path, LOSSLESS, rasterize=True)


def test_rasterize_respects_password(make_pdf_with_image, tmp_path):
    input_path = make_pdf_with_image("secret.pdf", pixel_size=(1000, 1200), password="hunter2")
    output_path = tmp_path / "secret.compressed.pdf"

    result = compress_document(
        input_path, output_path, VISUALLY_LOSSLESS, password="hunter2", rasterize=True
    )

    assert result.pages_rasterized == 1
    with pikepdf.open(result.output_path, password="hunter2") as pdf:
        assert len(pdf.pages) == 1
