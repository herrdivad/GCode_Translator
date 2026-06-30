"""Tests for GCodeTranslator.explain_gcode_line and GCodeLine key/value derivation."""
import pytest


def explain(translator, mapping, line):
    return translator.explain_gcode_line(line, mapping)


# --- known commands (mapping hit) -------------------------------------------------

def test_known_command(translator, mapping):
    g = explain(translator, mapping, "G1 X10 Y10 E2.5")
    assert g.is_command
    assert g.cmd == "G1"
    assert g.explanation == "Linear Move"
    assert g.dict_key == "G1: Linear Move"
    assert g.dict_value == "X10 Y10 E2.5"


def test_known_command_without_params(translator, mapping):
    g = explain(translator, mapping, "G28")
    assert g.dict_key == "G28: Auto Home"
    assert g.dict_value == "True"


def test_known_command_with_inline_comment_keeps_params_as_value(translator, mapping):
    g = explain(translator, mapping, "G1 X10 ; travel move")
    assert g.dict_key == "G1: Linear Move"
    assert g.dict_value == "X10"  # comment is not part of the value for known commands


# --- BUG-9: inline comment splitting + Special/Unknown semantics ------------------

def test_special_command_comment_glued_to_token(translator, mapping):
    """'M84; disable motors' -> clean cmd, Special command, comment is the value."""
    g = explain(translator, mapping, "M84; disable motors")
    assert g.cmd == "M84"
    assert g.explanation is None
    assert g.dict_key == "M84: Special command"
    assert g.dict_value == "disable motors"


def test_special_command_with_space_before_semicolon_is_identical(translator, mapping):
    glued = explain(translator, mapping, "M84; disable motors")
    spaced = explain(translator, mapping, "M84 ; disable motors")
    assert (spaced.cmd, spaced.dict_key, spaced.dict_value) == \
           (glued.cmd, glued.dict_key, glued.dict_value)


def test_unknown_command_without_explanation(translator, mapping):
    g = explain(translator, mapping, "SET_VELOCITY_LIMIT ACCEL=5000")
    assert g.cmd == "SET_VELOCITY_LIMIT"
    assert g.dict_key == "SET_VELOCITY_LIMIT: Unknown command"
    assert g.dict_value == "ACCEL=5000"


def test_special_command_prefers_explanation_when_params_present(translator, mapping):
    g = explain(translator, mapping, "M998 S1 ; custom thing")
    assert g.dict_key == "M998: Special command"
    assert g.dict_value == "custom thing"


# --- FEAT-1: metadata pairs -------------------------------------------------------

def test_metadata_equals_pair(translator, mapping):
    g = explain(translator, mapping, "; bed_temperature = 60")
    assert g.is_metadata
    assert g.meta_key == "bed_temperature"
    assert g.meta_value == "60"


def test_metadata_colon_pair(translator, mapping):
    g = explain(translator, mapping, "; Filament used: 1.2m")
    assert g.is_metadata
    assert g.meta_key == "Filament used"
    assert g.meta_value == "1.2m"


def test_empty_value_is_not_metadata(translator, mapping):
    g = explain(translator, mapping, "; modifier_phrase = ")
    assert not g.is_metadata
    assert g.is_comment


def test_single_letter_key_is_not_metadata(translator, mapping):
    """Per-layer axis markers like ';Z:0.2' must not be captured."""
    g = explain(translator, mapping, ";Z:0.2")
    assert not g.is_metadata


def test_prose_comment_is_not_metadata(translator, mapping):
    g = explain(translator, mapping, "; This is just a note")
    assert not g.is_metadata
    assert g.is_comment


# --- BUG-5: '=' settings bypass the blacklist, ':' noise stays out ----------------

@pytest.mark.parametrize("line,key,value", [
    ("; layer_height = 0.2", "layer_height", "0.2"),
    ("; first_layer_temperature = 215", "first_layer_temperature", "215"),
    ("; total_layers = 285", "total_layers", "285"),
])
def test_layer_equals_settings_are_captured(translator, mapping, line, key, value):
    g = explain(translator, mapping, line)
    assert g.is_metadata
    assert (g.meta_key, g.meta_value) == (key, value)


@pytest.mark.parametrize("line", [
    ";LAYER:5",
    ";HEIGHT:0.2",
    "; end of layer_num: 1, T: 3",
])
def test_layer_colon_noise_is_rejected(translator, mapping, line):
    g = explain(translator, mapping, line)
    assert not g.is_metadata


# --- is_valid_comment -------------------------------------------------------------

def test_is_valid_comment_accepts_real_comment(translator):
    assert translator.is_valid_comment("; a real comment", ["thumbnail"])


def test_is_valid_comment_rejects_blacklisted(translator):
    assert not translator.is_valid_comment(";LAYER:5", ["layer"])
