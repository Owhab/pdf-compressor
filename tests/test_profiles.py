from pdf_compressor.profiles import LOSSLESS, VISUALLY_LOSSLESS, resolve_profile


def test_lossless_does_not_downsample():
    assert LOSSLESS.downsamples_images is False


def test_visually_lossless_defaults():
    assert VISUALLY_LOSSLESS.target_dpi == 150
    assert VISUALLY_LOSSLESS.jpeg_quality == 80
    assert VISUALLY_LOSSLESS.downsamples_images is True


def test_custom_profile_uses_given_params():
    profile = resolve_profile("custom", dpi=200, jpeg_quality=60)
    assert profile.target_dpi == 200
    assert profile.jpeg_quality == 60


def test_custom_profile_falls_back_to_visual_defaults():
    profile = resolve_profile("custom")
    assert profile.target_dpi == VISUALLY_LOSSLESS.target_dpi
    assert profile.jpeg_quality == VISUALLY_LOSSLESS.jpeg_quality


def test_unknown_profile_raises():
    import pytest

    with pytest.raises(ValueError):
        resolve_profile("nonsense")
