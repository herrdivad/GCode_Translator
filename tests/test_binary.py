"""Tests for .gx BMP extraction (BUG-4), the BMP locator, and bgcode conversion (BUG-2)."""
import subprocess

import gcode_translator.Binary_GCode_Translator as B
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


# --- BUG-2: binary_gcode_to_gcode error handling (mocked, no real binary needed) ---

def _stub_binary(monkeypatch):
    """Make the binary lookup + chmod no-ops so only the conversion logic is tested."""
    monkeypatch.setattr(B.sys, "platform", "linux")
    monkeypatch.setattr(B, "get_bgcode_executable_path", lambda: "bgcode-dummy")
    monkeypatch.setattr(B, "make_executable", lambda path: None)


def test_bgcode_non_linux_returns_none(monkeypatch):
    monkeypatch.setattr(B.sys, "platform", "win32")
    assert B.binary_gcode_to_gcode("model.bgcode") is None


def test_bgcode_conversion_failure_returns_none(tmp_path, monkeypatch):
    _stub_binary(monkeypatch)

    def boom(*args, **kwargs):
        raise subprocess.CalledProcessError(1, "bgcode")
    monkeypatch.setattr(B.subprocess, "run", boom)

    src = tmp_path / "model.bgcode"
    src.write_bytes(b"\x00")
    assert B.binary_gcode_to_gcode(str(src)) is None


def test_bgcode_missing_output_returns_none(tmp_path, monkeypatch):
    _stub_binary(monkeypatch)
    monkeypatch.setattr(B.subprocess, "run", lambda *a, **k: None)  # "succeeds", writes nothing

    src = tmp_path / "model.bgcode"
    src.write_bytes(b"\x00")
    assert B.binary_gcode_to_gcode(str(src)) is None  # .gcode was never created


def test_bgcode_success_returns_output_path(tmp_path, monkeypatch):
    _stub_binary(monkeypatch)
    out = tmp_path / "model.gcode"

    def fake_run(*args, **kwargs):
        out.write_text("G1 X1\n")  # simulate the binary producing the .gcode
    monkeypatch.setattr(B.subprocess, "run", fake_run)

    src = tmp_path / "model.bgcode"
    src.write_bytes(b"\x00")
    assert B.binary_gcode_to_gcode(str(src)) == str(out)
