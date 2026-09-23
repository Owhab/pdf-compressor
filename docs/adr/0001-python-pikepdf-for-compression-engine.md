# Use Python + pikepdf as the compression engine

We considered Rust (`lopdf`/`mupdf-rs`), Node/TS (`pdf-lib`), and Go for the CLI, but picked Python with `pikepdf` (wraps QPDF) for structural rewriting plus Pillow/mupdf for image re-encoding. Python has by far the most mature PDF-compression prior art and library support for exactly this problem — stream recompression, font subsetting, image downsampling — which matters more here than Rust's single-binary distribution story or a JS-only stack.
