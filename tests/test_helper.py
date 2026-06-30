"""Tests for helper.add_to_dict_smart (the aggregation primitive)."""
from gcode_translator.helper import add_to_dict_smart


def test_first_value_is_stored_as_string():
    d = {}
    add_to_dict_smart(d, "M104", "S210")
    assert d == {"M104": "S210"}


def test_second_value_turns_into_list():
    d = {}
    add_to_dict_smart(d, "M104", "S210")
    add_to_dict_smart(d, "M104", "S230")
    assert d == {"M104": ["S210", "S230"]}


def test_third_value_is_appended():
    d = {"M104": ["S210", "S230"]}
    add_to_dict_smart(d, "M104", "S240")
    assert d["M104"] == ["S210", "S230", "S240"]


def test_duplicates_are_kept():
    d = {}
    add_to_dict_smart(d, "G1", "X1")
    add_to_dict_smart(d, "G1", "X1")
    assert d["G1"] == ["X1", "X1"]
