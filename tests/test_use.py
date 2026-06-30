"""End-to-end tests for use(): library API (LIB-1), previews (LIB-2), .gx (BUG-8)."""
import pytest

from gcode_translator.GCode_Translator import use
from conftest import SMALL_GCODE, BINARY_GX, requires

PNG_MAGIC = b"\x89PNG"


@requires(SMALL_GCODE)
def test_returns_three_dicts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = use(str(SMALL_GCODE))
    assert isinstance(result, list) and len(result) == 3
    assert all(isinstance(d, dict) for d in result)


@requires(SMALL_GCODE)
def test_library_mode_writes_no_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    use(str(SMALL_GCODE))
    assert list(tmp_path.iterdir()) == []  # no output.txt / preview.png


@requires(SMALL_GCODE)
def test_library_mode_is_silent_on_stdout(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    use(str(SMALL_GCODE))
    assert capsys.readouterr().out == ""


# These two need no sample file at all (they use tmp_path), so they always run.
def test_invalid_path_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        use(str(tmp_path / "does_not_exist.gcode"))


def test_unsupported_extension_raises(tmp_path):
    bogus = tmp_path / "data.txt"
    bogus.write_text("G1 X10\n")
    with pytest.raises(ValueError):
        use(str(bogus))


def test_invalid_aggregation_raises(tmp_path):
    bogus = tmp_path / "x.gcode"
    bogus.write_text("G1 X10\n")
    with pytest.raises(ValueError):
        use(str(bogus), aggregation="bogus")


@requires(SMALL_GCODE)
def test_output_txt_written_when_path_given(tmp_path):
    out = tmp_path / "out.txt"
    use(str(SMALL_GCODE), output_txt_path=str(out))
    assert out.exists() and out.stat().st_size > 0


@requires(SMALL_GCODE)
def test_return_preview_yields_bytes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result, previews = use(str(SMALL_GCODE), return_preview=True)
    assert isinstance(result, list)
    assert previews and previews[0][:4] == PNG_MAGIC


@requires(SMALL_GCODE)
def test_return_preview_writes_no_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    use(str(SMALL_GCODE), return_preview=True)
    assert list(tmp_path.iterdir()) == []


@requires(SMALL_GCODE)
def test_preview_written_when_path_given(tmp_path):
    out = tmp_path / "thumb.png"
    use(str(SMALL_GCODE), preview_path=str(out))
    assert out.exists() and out.read_bytes()[:4] == PNG_MAGIC


@requires(BINARY_GX)
def test_gx_silent_mode_writes_no_bmp(tmp_path, monkeypatch):
    """BUG-8: a .gx in pure library mode must not leak preview_gx.bmp."""
    monkeypatch.chdir(tmp_path)
    use(str(BINARY_GX))
    assert not (tmp_path / "preview_gx.bmp").exists()


@requires(BINARY_GX)
def test_gx_return_preview_gives_bmp(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _, previews = use(str(BINARY_GX), return_preview=True)
    assert previews and previews[0][:2] == b"BM"
