# pdf-compress

Local command-line tool that reduces a PDF's file size without compromising document quality. Everything runs on your machine — no PDF content is ever uploaded anywhere.

## Install

Requires Python 3.10+.

```sh
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

This installs the `pdf-compress` command into `.venv/bin/`. Either activate the venv (`source .venv/bin/activate`) or call it as `.venv/bin/pdf-compress`.

## Quick start

```sh
pdf-compress report.pdf
```

Writes `report.compressed.pdf` next to the original. The original is never touched or deleted.

```
report.pdf: 4.2MB -> 1.1MB (74% reduction)
```

## Compression profiles

`--profile` controls how aggressively content is recompressed. Default is `visual`.

| Profile | Behavior |
|---|---|
| `lossless` | Strips redundant data only (duplicate objects, unused resources, recompresses streams). Zero pixel/text degradation. Best for text-heavy PDFs; limited gains on scanned pages. |
| `visual` (default) | Downsamples raster images to 150 DPI and re-encodes at JPEG quality 80 — imperceptible at normal viewing/printing size. Best gains on scanned/image-heavy PDFs. |
| `custom` | Same as `visual` but with your own `--dpi` / `--jpeg-quality`. |

```sh
pdf-compress scan.pdf --profile lossless
pdf-compress scan.pdf --profile custom --dpi 200 --jpeg-quality 60
```

`--dpi` / `--jpeg-quality` are only valid with `--profile custom`.

Every profile, including `lossless`, also strips application-private page data (e.g. Adobe Illustrator's `/PieceInfo` round-trip editing data) — it's inert for viewing/printing/reading, so this isn't a quality trade-off. On real-world Illustrator-exported PDFs this alone can be the majority of the file size.

The tool never produces a file bigger than the input. If recompression doesn't actually shrink the file, nothing is written and the original is reported as kept:

```
notes.pdf: 0% reduction, original kept
```

## Rasterize (last resort for vector-bloated PDFs)

Some PDFs store text as outlined vector paths instead of real fonts (common from certain typesetting/tracing pipelines). That content is already tightly compressed and there's no redundant data to strip, so normal compression barely helps. `--rasterize` renders every page (all content, vector and raster alike) to a single image at the profile's target DPI:

```sh
pdf-compress scan.pdf --rasterize --profile visual
```

This trades away text selectability/searchability for size — use it only when normal compression isn't enough. Not compatible with `--profile lossless` (rasterizing is inherently lossy). A warning is printed before processing.

## Batch (a whole folder)

Pass a directory instead of a file. It recurses into subdirectories and mirrors the structure into a sibling `compressed/` folder.

```sh
pdf-compress ./invoices/
```

```
invoices/2024/jan.pdf: 3.1MB -> 0.8MB (74% reduction)
invoices/2024/feb.pdf: 2.9MB -> 0.7MB (76% reduction)
skipping non-PDF file: invoices/2024/notes.txt

Batch Job: 2 compressed, 0 failed (75% overall reduction)
```

Output lands in `../compressed/invoices/...`. A single corrupt or unreadable PDF is logged and skipped — it doesn't abort the rest of the batch. Exit code is `1` if any file failed, `0` otherwise.

## Output location

| Flag | Single file | Directory (batch) |
|---|---|---|
| (default) | `<name>.compressed.pdf` next to the input | mirrored into `compressed/` next to the input directory |
| `-o PATH` | write to `PATH` instead | not supported |
| `--in-place` | overwrite the input | overwrite each file in place |

## Password-protected PDFs

If the PDF is encrypted, you'll be prompted for the password (or pass `--password`). The output is re-encrypted with the same password.

```sh
pdf-compress contract.pdf
Password for contract.pdf:
```

## What's preserved

Form fields, annotations, and bookmarks are always left untouched — compression never modifies them, only the underlying content streams and images. Bilevel scanned line-art (already CCITT-compressed) is left as-is rather than re-encoded as JPEG, since JPEG would both bloat it and blur the text.

## Reference

- `CONTEXT.md` — domain glossary (Compression, Compression Profile, Content Profile, Batch Job, Rasterization, etc.)
- `docs/adr/` — why Python+pikepdf, why the DPI-estimation heuristic works, why PyMuPDF for rasterization, why `/PieceInfo` gets stripped
- `pdf-compress --help` — full flag reference

## Tests

```sh
.venv/bin/pytest
```
