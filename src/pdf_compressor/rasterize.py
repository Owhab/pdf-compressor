"""Explicit, opt-in page rasterization.

See CONTEXT.md: Rasterization. Only runs when the CLI is given
`--rasterize`; never triggered automatically, since it trades away text
selectability/searchability for size and that's not a call this tool
makes on a user's behalf.
"""

from __future__ import annotations

import io
from pathlib import Path

import pikepdf
import pymupdf
from PIL import Image


def rasterize_document(
    pdf: pikepdf.Pdf,
    source_path: Path,
    target_dpi: int,
    jpeg_quality: int,
    *,
    password: str | None = None,
) -> int:
    """Replace every page's content with a single full-page raster image
    rendered at `target_dpi`, discarding all vector/text content on that
    page. Returns the number of pages rasterized.
    """
    with pymupdf.open(source_path) as doc:
        if doc.needs_pass:
            doc.authenticate(password or "")
        for index, page in enumerate(pdf.pages):
            _rasterize_page(pdf, page, doc[index], target_dpi, jpeg_quality)
    return len(pdf.pages)


def _rasterize_page(
    pdf: pikepdf.Pdf,
    page: pikepdf.Page,
    source_page: pymupdf.Page,
    target_dpi: int,
    jpeg_quality: int,
) -> None:
    pixmap = source_page.get_pixmap(dpi=target_dpi)
    mode = "RGB" if pixmap.n >= 3 else "L"
    img = Image.frombytes(mode, (pixmap.width, pixmap.height), pixmap.samples)

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=jpeg_quality, optimize=True)

    x0, y0, x1, y1 = (float(v) for v in page.mediabox)
    page_width, page_height = abs(x1 - x0), abs(y1 - y0)

    image_stream = pdf.make_stream(
        buffer.getvalue(),
        Type=pikepdf.Name("/XObject"),
        Subtype=pikepdf.Name("/Image"),
        Width=pixmap.width,
        Height=pixmap.height,
        BitsPerComponent=8,
        ColorSpace=pikepdf.Name("/DeviceRGB" if mode == "RGB" else "/DeviceGray"),
        Filter=pikepdf.Name("/DCTDecode"),
    )
    page.Resources = pikepdf.Dictionary(XObject=pikepdf.Dictionary(Im0=image_stream))
    content = f"q {page_width} 0 0 {page_height} 0 0 cm /Im0 Do Q".encode()
    page.Contents = pdf.make_stream(content)
