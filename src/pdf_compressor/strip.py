"""Stripping of application-private, non-rendering page data.

See CONTEXT.md: Compression Profile (Lossless).
"""

from __future__ import annotations

import pikepdf

# Keys the PDF spec marks as private to the originating application and
# never consulted by renderers or viewers. Safe to drop under every
# Compression Profile, including Lossless. /PieceInfo is how Adobe
# Illustrator (and other apps) embed a full round-trip copy of their
# native editing data inside the PDF — on real-world PDFs exported with
# "Preserve Illustrator Editing Capabilities" this has been observed to be
# the majority of the file's size while being entirely inert for viewing,
# printing, or reading.
_STRIPPABLE_PAGE_KEYS = ("/PieceInfo", "/Thumb")


def strip_private_page_data(pdf: pikepdf.Pdf) -> int:
    """Remove application-private data and legacy page thumbnails from
    every page. Returns the number of pages that had something removed.
    """
    cleaned = 0
    for page in pdf.pages:
        removed = False
        for key in _STRIPPABLE_PAGE_KEYS:
            if key in page:
                del page[key]
                removed = True
        if removed:
            cleaned += 1
    return cleaned
