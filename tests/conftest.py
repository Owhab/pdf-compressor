from __future__ import annotations

import io
from pathlib import Path

import pikepdf
import pytest
from PIL import Image


def _make_pdf_with_image(
    path: Path,
    *,
    pixel_size: tuple[int, int],
    page_size_pt: tuple[float, float] = (612.0, 792.0),
    password: str | None = None,
) -> None:
    """Build a one-page PDF whose page is `page_size_pt` (PDF points,
    default US Letter) with a single JPEG image XObject drawn to fill the
    entire page, at `pixel_size` pixel dimensions.
    """
    img = Image.new("RGB", pixel_size, color=(120, 140, 160))
    for x in range(0, pixel_size[0], 10):
        for y in range(0, pixel_size[1], 10):
            img.putpixel((x, y), (255, 0, 0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=95)
    jpeg_bytes = buf.getvalue()

    pdf = pikepdf.Pdf.new()
    page_width, page_height = page_size_pt
    page = pdf.add_blank_page(page_size=(page_width, page_height))
    stream = pdf.make_stream(
        jpeg_bytes,
        Type=pikepdf.Name("/XObject"),
        Subtype=pikepdf.Name("/Image"),
        Width=pixel_size[0],
        Height=pixel_size[1],
        BitsPerComponent=8,
        ColorSpace=pikepdf.Name("/DeviceRGB"),
        Filter=pikepdf.Name("/DCTDecode"),
    )
    page.Resources = pikepdf.Dictionary(XObject=pikepdf.Dictionary(Im0=stream))
    content = f"q {page_width} 0 0 {page_height} 0 0 cm /Im0 Do Q".encode()
    page.Contents = pdf.make_stream(content)

    save_kwargs = {}
    if password is not None:
        save_kwargs["encryption"] = pikepdf.Encryption(owner=password, user=password)
    pdf.save(path, **save_kwargs)
    pdf.close()


def _make_text_pdf(path: Path) -> None:
    """Build a one-page PDF with only vector/text content (no images)."""
    pdf = pikepdf.Pdf.new()
    page = pdf.add_blank_page(page_size=(612, 792))
    content = b"BT /F1 24 Tf 72 700 Td (Hello, PDF Compressor) Tj ET"
    page.Contents = pdf.make_stream(content)
    page.Resources = pikepdf.Dictionary(
        Font=pikepdf.Dictionary(
            F1=pdf.make_indirect(
                pikepdf.Dictionary(
                    Type=pikepdf.Name("/Font"),
                    Subtype=pikepdf.Name("/Type1"),
                    BaseFont=pikepdf.Name("/Helvetica"),
                )
            )
        )
    )
    pdf.save(path)
    pdf.close()


@pytest.fixture
def make_pdf_with_image(tmp_path):
    def _factory(name: str = "input.pdf", pixel_size=(1700, 2200), password=None) -> Path:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        _make_pdf_with_image(path, pixel_size=pixel_size, password=password)
        return path

    return _factory


@pytest.fixture
def make_text_pdf(tmp_path):
    def _factory(name: str = "text.pdf") -> Path:
        path = tmp_path / name
        _make_text_pdf(path)
        return path

    return _factory
