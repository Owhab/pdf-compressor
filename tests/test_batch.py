from __future__ import annotations

from pdf_compressor.batch import compress_batch, iter_pdf_paths
from pdf_compressor.profiles import VISUALLY_LOSSLESS


def _results_collector():
    results = []
    return results, results.append


def test_iter_pdf_paths_recurses_and_warns_on_non_pdf(make_pdf_with_image, tmp_path, capsys):
    (tmp_path / "sub").mkdir()
    make_pdf_with_image("a.pdf", pixel_size=(400, 400))
    (tmp_path / "sub" / "b.pdf").write_bytes((tmp_path / "a.pdf").read_bytes())
    (tmp_path / "notes.txt").write_text("not a pdf")

    found = sorted(p.name for p in iter_pdf_paths(tmp_path))

    assert found == ["a.pdf", "b.pdf"]
    assert "skipping non-PDF file" in capsys.readouterr().out


def test_compress_batch_mirrors_directory_into_compressed_dir(make_pdf_with_image, tmp_path):
    make_pdf_with_image("docs/sub/scan.pdf", pixel_size=(2550, 3300))
    root = tmp_path / "docs"

    results, report = _results_collector()
    exit_code = compress_batch(root, VISUALLY_LOSSLESS, in_place=False, password=None, report=report)

    assert exit_code == 0
    assert len(results) == 1
    expected_output = tmp_path / "compressed" / "docs" / "sub" / "scan.pdf"
    assert expected_output.exists()
    assert root.exists()  # original untouched


def test_compress_batch_in_place_overwrites(make_pdf_with_image, tmp_path):
    big = make_pdf_with_image("docs/scan.pdf", pixel_size=(2550, 3300))
    root = tmp_path / "docs"
    original_size = big.stat().st_size

    results, report = _results_collector()
    compress_batch(root, VISUALLY_LOSSLESS, in_place=True, password=None, report=report)

    assert big.exists()
    assert big.stat().st_size < original_size
    assert not (tmp_path / "compressed").exists()


def test_compress_batch_skips_corrupt_file_and_continues(make_pdf_with_image, tmp_path):
    make_pdf_with_image("docs/good.pdf", pixel_size=(2550, 3300))
    root = tmp_path / "docs"
    (root / "broken.pdf").write_bytes(b"not a real pdf")

    results, report = _results_collector()
    exit_code = compress_batch(root, VISUALLY_LOSSLESS, in_place=False, password=None, report=report)

    assert exit_code == 1  # one failure
    assert len(results) == 1  # but good.pdf still succeeded
