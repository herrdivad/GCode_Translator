"""Tests for .gx BMP extraction (BUG-4) and the BMP locator."""
from gcode_translator.Binary_GCode_Translator import (
    extract_binary_picture_from_gx,
    _locate_embedded_bmp,
)
from conftest import BINARY_GX, TEXT_GX, REFERENCE_BMP, requires


@requires(BINARY_GX)
def test_locate_embedded_bmp_reads_offset_and_size():
    header = BINARY_GX.read_bytes()[:4096]
    assert _locate_embedded_bmp(header) == (58, 14454)


@requires(BINARY_GX, REFERENCE_BMP)
def test_autodetect_matches_reference_bmp():
    data = extract_binary_picture_from_gx(str(BINARY_GX))
    assert data[:2] == b"BM"
    assert data == REFERENCE_BMP.read_bytes()


@requires(BINARY_GX)
def test_autodetect_matches_legacy_fixed_offsets():
    auto = extract_binary_picture_from_gx(str(BINARY_GX))
    fixed = extract_binary_picture_from_gx(str(BINARY_GX), skip=58, count=14454)
    assert auto == fixed


@requires(TEXT_GX)
def test_text_gx_without_bmp_returns_none():
    assert extract_binary_picture_from_gx(str(TEXT_GX)) is None


@requires(BINARY_GX)
def test_writes_file_only_when_output_path_given(tmp_path):
    out = tmp_path / "preview.bmp"
    data = extract_binary_picture_from_gx(str(BINARY_GX), str(out))
    assert out.exists()
    assert out.read_bytes() == data
