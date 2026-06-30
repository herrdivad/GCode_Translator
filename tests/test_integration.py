"""Integration tests that run real (rich) exFiles end-to-end through use().

These nail down the behaviour that was verified by hand during development:
FEAT-1 metadata extraction, BUG-5 ('layer' settings), BUG-9 (Special/Unknown),
and that per-layer noise never leaks into the result dict — across two different
slicers (PrusaSlicer and AnycubicSlicer).
"""
import pytest

from gcode_translator.GCode_Translator import use
from conftest import PRUSA_GCODE, NECRO_GCODE, requires


@requires(PRUSA_GCODE)
def test_prusaslicer_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    g, m, other = use(str(PRUSA_GCODE))

    # FEAT-1: declarative metadata is captured into other_dict.
    assert other["temperature"] == "220"
    assert other["bed_temperature"] == "60"
    assert other["nozzle_diameter"] == "0.4"
    # BUG-5: a setting whose key contains the blacklisted word "layer" still gets in.
    assert other["layer_height"] == "0.2"

    # Real commands are translated via the mapping.
    assert any(k.startswith("G1:") for k in g)
    assert any(k.startswith("M104:") for k in m)

    # No per-layer marker leaked into the dict.
    assert "LAYER" not in other
    assert "Z" not in other
    assert not any("layer_num" in k.lower() for k in other)

    # Library mode stays side-effect free.
    assert list(tmp_path.iterdir()) == []


@pytest.mark.slow
@requires(NECRO_GCODE)
def test_anycubicslicer_4color_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    g, m, other = use(str(NECRO_GCODE))

    # FEAT-1: multi-material / printer metadata.
    assert other["printer_model"] == "Anycubic Kobra S1"
    assert other["filament_type"] == "PLA;PLA;PLA;PLA"
    assert other["nozzle_temperature"] == "230,230,230,230"

    # BUG-5: many 'layer' settings captured (e.g. first_layer_temperature, total_layers).
    assert len([k for k in other if "layer" in k.lower()]) >= 50
    assert other["total_layers"] == "328"

    # BUG-9: unknown command WITH an inline explanation -> Special command, comment is the value.
    assert m["M84: Special command"] == "disable motors"
    # BUG-9: unknown command WITHOUT explanation -> Unknown command.
    assert any(k.endswith(": Unknown command") for k in other)

    # No per-layer noise leaked.
    assert "LAYER" not in other
    assert "Z" not in other
