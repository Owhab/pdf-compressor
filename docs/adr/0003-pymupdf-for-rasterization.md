# Use PyMuPDF to render pages for Rasterization

We needed a way to render a full PDF page (vector, text, and raster content combined) to a raster image for the opt-in `--rasterize` path. Considered `pdf2image`/`pdftoppm` (wraps Poppler, requires a system binary we can't guarantee is installed) and Ghostscript (heavier system dependency, same problem) against PyMuPDF (`pymupdf`, pip-installable, renders directly via its bundled MuPDF, no external binary).

Picked PyMuPDF for the pip-only install and page-accurate rendering. Trade-off worth flagging: PyMuPDF is AGPL-licensed (with a commercial license available from Artifex). For this tool's current scope — a local personal CLI, not redistributed as a SaaS or closed-source product — that's not a blocker, but it would need revisiting before any commercial or closed-source distribution of this tool.
