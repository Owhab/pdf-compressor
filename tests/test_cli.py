from __future__ import annotations

from pdf_compressor.cli import main


def test_cli_single_file_writes_compressed_sibling(make_pdf_with_image, capsys):
    input_path = make_pdf_with_image("scan.pdf", pixel_size=(2550, 3300))

    exit_code = main([str(input_path)])

    assert exit_code == 0
    output_path = input_path.with_name("scan.compressed.pdf")
    assert output_path.exists()
    assert "reduction" in capsys.readouterr().out


def test_cli_in_place_overwrites_input(make_pdf_with_image):
    input_path = make_pdf_with_image("scan.pdf", pixel_size=(2550, 3300))
    original_size = input_path.stat().st_size

    exit_code = main([str(input_path), "--in-place"])

    assert exit_code == 0
    assert input_path.stat().st_size < original_size
    assert not input_path.with_name("scan.compressed.pdf").exists()


def test_cli_rejects_dpi_without_custom_profile(make_pdf_with_image):
    input_path = make_pdf_with_image("scan.pdf", pixel_size=(2550, 3300))

    import pytest

    with pytest.raises(SystemExit):
        main([str(input_path), "--dpi", "100"])


def test_cli_wrong_password_exits_nonzero(make_pdf_with_image, capsys):
    input_path = make_pdf_with_image("secret.pdf", pixel_size=(2550, 3300), password="hunter2")

    exit_code = main([str(input_path), "--password", "wrong"])

    assert exit_code == 1
    assert "wrong password" in capsys.readouterr().err


def test_cli_batch_on_directory(make_pdf_with_image, tmp_path):
    make_pdf_with_image("docs/scan.pdf", pixel_size=(2550, 3300))

    exit_code = main([str(tmp_path / "docs")])

    assert exit_code == 0
    assert (tmp_path / "compressed" / "docs" / "scan.pdf").exists()
