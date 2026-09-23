"""Compression Profile definitions.

See CONTEXT.md: Compression Profile.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_VISUAL_LOSSLESS_DPI = 150
DEFAULT_VISUAL_LOSSLESS_JPEG_QUALITY = 80


@dataclass(frozen=True)
class CompressionProfile:
    """A resolved Compression Profile.

    `target_dpi` and `jpeg_quality` are `None` for the Lossless profile,
    where no image is ever recompressed.
    """

    name: str
    target_dpi: int | None
    jpeg_quality: int | None

    @property
    def downsamples_images(self) -> bool:
        return self.target_dpi is not None


LOSSLESS = CompressionProfile(name="lossless", target_dpi=None, jpeg_quality=None)
VISUALLY_LOSSLESS = CompressionProfile(
    name="visual",
    target_dpi=DEFAULT_VISUAL_LOSSLESS_DPI,
    jpeg_quality=DEFAULT_VISUAL_LOSSLESS_JPEG_QUALITY,
)


def resolve_profile(
    name: str, *, dpi: int | None = None, jpeg_quality: int | None = None
) -> CompressionProfile:
    """Resolve a `--profile` value (plus optional Custom overrides) into a
    `CompressionProfile`.
    """
    if name == "lossless":
        return LOSSLESS
    if name == "visual":
        return VISUALLY_LOSSLESS
    if name == "custom":
        return CompressionProfile(
            name="custom",
            target_dpi=dpi or DEFAULT_VISUAL_LOSSLESS_DPI,
            jpeg_quality=jpeg_quality or DEFAULT_VISUAL_LOSSLESS_JPEG_QUALITY,
        )
    raise ValueError(f"unknown compression profile: {name!r}")
