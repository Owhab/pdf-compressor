"""Raster (image) recompression.

See CONTEXT.md: Content Profile.
"""

from __future__ import annotations

import io
from dataclasses import dataclass

import pikepdf
from PIL import Image

# Bilevel line-art (stencil scans of text pages) is typically already
# CCITT-compressed; JPEG re-encoding would both bloat it and blur the text,
# so it's left untouched by every profile that downsamples images.
_SKIP_MODES = {"1"}


@dataclass
class RasterCompressionStats:
    images_seen: int = 0
    images_downsampled: int = 0


def _page_width_inches(page: pikepdf.Page) -> float:
    """The page's MediaBox width, in inches.

    Used as a conservative stand-in for "how wide is this image displayed":
    assuming full-page width can only *underestimate* an image's true
    effective DPI (a smaller real placement would mean a higher true DPI),
    which biases the downsample decision toward keeping more detail, never
    less. See docs/adr/0002-full-page-width-dpi-heuristic.md.
    """
    x0, y0, x1, y1 = (float(v) for v in page.mediabox)
    return abs(x1 - x0) / 72.0


def compress_page_images(
    pdf: pikepdf.Pdf, page: pikepdf.Page, target_dpi: int, jpeg_quality: int
) -> RasterCompressionStats:
    """Downsample and re-encode this page's raster images that exceed
    `target_dpi` at an assumed full-page-width placement.

    Mutates image XObjects in place. Images this function can't confidently
    handle (undecodable streams, bilevel line art) are left untouched.
    """
    stats = RasterCompressionStats()
    width_in = _page_width_inches(page)
    if width_in <= 0:
        return stats

    for xobj in page.get_images(recursive=True).values():
        stats.images_seen += 1
        pdfimage = pikepdf.PdfImage(xobj)

        if pdfimage.image_mask:
            continue

        effective_dpi = pdfimage.width / width_in
        if effective_dpi <= target_dpi:
            continue

        try:
            pil_image = pdfimage.as_pil_image()
        except Exception:
            continue

        if pil_image.mode in _SKIP_MODES:
            continue

        if _downsample_and_replace(pdf, xobj, pil_image, width_in, target_dpi, jpeg_quality):
            stats.images_downsampled += 1

    return stats


def _downsample_and_replace(
    pdf: pikepdf.Pdf,
    xobj: pikepdf.Object,
    pil_image: Image.Image,
    width_in: float,
    target_dpi: int,
    jpeg_quality: int,
) -> bool:
    """Resize `pil_image` to `target_dpi` and write it back into `xobj` as a
    JPEG. Returns whether the replacement happened (skipped if it wouldn't
    actually shrink this image's stream).
    """
    alpha = None
    color = pil_image
    if pil_image.mode == "RGBA":
        alpha = pil_image.getchannel("A")
        color = pil_image.convert("RGB")
    elif pil_image.mode == "LA":
        alpha = pil_image.getchannel("A")
        color = pil_image.convert("L")
    elif pil_image.mode not in ("RGB", "L"):
        color = pil_image.convert("RGB")

    target_width = max(1, round(target_dpi * width_in))
    target_height = max(1, round(color.height * target_width / color.width))
    color = color.resize((target_width, target_height), Image.LANCZOS)

    color_buffer = io.BytesIO()
    color.save(color_buffer, format="JPEG", quality=jpeg_quality, optimize=True)
    color_bytes = color_buffer.getvalue()
    if len(color_bytes) >= len(xobj.read_raw_bytes()):
        return False

    xobj.write(color_bytes, filter=pikepdf.Name("/DCTDecode"))
    xobj.Width = target_width
    xobj.Height = target_height
    xobj.BitsPerComponent = 8
    xobj.ColorSpace = pikepdf.Name("/DeviceRGB" if color.mode == "RGB" else "/DeviceGray")
    for stale_key in ("/Decode", "/Indexed", "/Mask"):
        if stale_key in xobj:
            del xobj[stale_key]

    if alpha is not None:
        alpha = alpha.resize((target_width, target_height), Image.LANCZOS)
        alpha_buffer = io.BytesIO()
        alpha.save(alpha_buffer, format="JPEG", quality=jpeg_quality, optimize=True)
        xobj.SMask = pdf.make_stream(
            alpha_buffer.getvalue(),
            Type=pikepdf.Name("/XObject"),
            Subtype=pikepdf.Name("/Image"),
            Width=target_width,
            Height=target_height,
            BitsPerComponent=8,
            ColorSpace=pikepdf.Name("/DeviceGray"),
            Filter=pikepdf.Name("/DCTDecode"),
        )
    elif "/SMask" in xobj:
        del xobj.SMask

    return True
