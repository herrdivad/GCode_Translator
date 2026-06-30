"""Shared fixtures for the gcode_translator test-suite."""
from pathlib import Path

import pytest

from gcode_translator.GCode_Translator import GCodeTranslator

EXFILES = Path(__file__).resolve().parent.parent / "exFiles"

# Small real-world files used for end-to-end checks (kept tiny so tests stay fast).
SMALL_GCODE = EXFILES / "MainConnectorCover_0.4n_0.2mm_PLA_MINIIS_16m(1)_small.gcode"
BINARY_GX = EXFILES / "modern_Flashforge_Ninetales_binaryPreview.gx"
TEXT_GX = EXFILES / "modern_Flashforge_Ninetales.gx"
REFERENCE_BMP = EXFILES / "modern_Flashforge_Ninetales_binaryPreview.bmp"

# Full real-world files used for integration tests (different slicers).
PRUSA_GCODE = EXFILES / "MainConnectorCover_0.4n_0.2mm_PLA_MINIIS_16m(1).gcode"  # PrusaSlicer, ~26k lines, fast
NECRO_GCODE = EXFILES / "4color_necroDragon_PLA_0.2_3h39m58s.gcode"             # AnycubicSlicer, large (slow)


def requires(*paths):
    """Return a marker that *skips* (never fails) a test when any required
    fixture file is missing — e.g. when a user checked out the repo without the
    large sample files in exFiles/.
    """
    missing = [p.name for p in paths if not p.exists()]
    return pytest.mark.skipif(
        bool(missing),
        reason="missing sample file(s) in exFiles/: " + ", ".join(missing),
    )


@pytest.fixture
def mapping():
    """A small, deterministic command mapping (independent of marlin_mapping.json)."""
    return {
        "G1": "Linear Move",
        "G28": "Auto Home",
        "M104": "Set Hotend Temperature",
        "M140": "Set Bed Temperature",
    }


@pytest.fixture
def translator():
    return GCodeTranslator()
