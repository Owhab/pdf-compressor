from __future__ import annotations

import pikepdf

from pdf_compressor.core import compress_document
from pdf_compressor.profiles import LOSSLESS
from pdf_compressor.strip import strip_private_page_data


def _add_piece_info(pdf: pikepdf.Pdf, page: pikepdf.Page, payload_size: int = 200_000) -> None:
    private = pdf.make_stream(b"X" * payload_size)
    page.PieceInfo = pikepdf.Dictionary(
        Illustrator=pikepdf.Dictionary(Private=pikepdf.Dictionary(AIPDFPrivateData1=private))
    )
    page.Thumb = pdf.make_stream(b"Y" * 1000)


def test_strip_private_page_data_removes_piece_info_and_thumb(make_text_pdf):
    input_path = make_text_pdf()
    with pikepdf.open(input_path, allow_overwriting_input=True) as pdf:
        page = pdf.pages[0]
        _add_piece_info(pdf, page)
        assert "/PieceInfo" in page
        assert "/Thumb" in page

        cleaned = strip_private_page_data(pdf)

        assert cleaned == 1
        assert "/PieceInfo" not in page
        assert "/Thumb" not in page


def test_compress_document_strips_piece_info_even_under_lossless(make_text_pdf, tmp_path):
    input_path = make_text_pdf()
    with pikepdf.open(input_path, allow_overwriting_input=True) as pdf:
        _add_piece_info(pdf, pdf.pages[0])
        pdf.save(input_path)

    output_path = tmp_path / "text.compressed.pdf"
    result = compress_document(input_path, output_path, LOSSLESS)

    assert result.kept_original is False
    assert result.compressed_size < result.original_size
    with pikepdf.open(result.output_path) as pdf:
        assert "/PieceInfo" not in pdf.pages[0]
