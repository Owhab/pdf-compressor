"""Local, quality-preserving PDF compression.

See CONTEXT.md at the repo root for the domain vocabulary (Compression,
Compression Profile, Content Profile, Batch Job) used throughout this
package.
"""

from .core import CompressionResult, compress_document
from .profiles import LOSSLESS, VISUALLY_LOSSLESS, CompressionProfile, resolve_profile

__all__ = [
    "CompressionProfile",
    "CompressionResult",
    "LOSSLESS",
    "VISUALLY_LOSSLESS",
    "compress_document",
    "resolve_profile",
]
