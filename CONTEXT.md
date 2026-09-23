# PDF Compressor

A local command-line tool that reduces a PDF Document's file size while respecting an explicit Compression Profile.

## Language

**PDF Document**:
The input file being compressed — a single file passed to the tool, or one member of a Batch Job. May be password-protected, in which case Compression decrypts, recompresses, and re-encrypts the output with the same password.
_Avoid_: file, doc

**Compression**:
The operation of reducing a PDF Document's file size per its Compression Profile, always performed locally — no PDF Document content is transmitted off-device. Never produces an output larger than the input: if recompression doesn't shrink the file, the original is kept unchanged and reported as a no-gain result.
_Avoid_: optimization, shrinking

**Compression Profile**:
The quality target controlling how aggressively content is recompressed: **Lossless** (strips only redundant data — duplicate objects, unused fonts, metadata — zero pixel/text degradation), **Visually Lossless** (default; lossy recompression, e.g. image re-encoding and DPI downsampling, tuned to be imperceptible at normal viewing/printing size), or **Custom** (user-specified parameters overriding the Visually Lossless defaults).
_Avoid_: quality setting, compression level

**Content Profile**:
Per-object classification of a PDF Document's content — **Raster** (image-based, e.g. scanned pages) vs **Vector/Text** (native digital content, e.g. text runs and vector graphics) — used to decide which Compression technique applies to each object. A single PDF Document may mix both.
_Avoid_: content type

**Non-Content Features**:
Form fields (AcroForms), annotations, and bookmarks/outlines belonging to a PDF Document. Always preserved untouched by Compression — these are functional document features, not compressible waste.
_Avoid_: metadata (metadata is itself compressible/strippable under a Lossless Compression Profile — don't conflate the two)

**Batch Job**:
A Compression run over multiple PDF Documents (a directory) in a single CLI invocation.
_Avoid_: bulk job, batch process
