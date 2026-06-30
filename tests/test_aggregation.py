"""Tests for dict aggregation: add_line_to_dict and sort_and_filter_dict."""


def feed(translator, mapping, lines):
    for line in lines:
        translator.add_line_to_dict(translator.explain_gcode_line(line, mapping))


def test_commands_split_into_g_m_other(translator, mapping):
    feed(translator, mapping, ["G1 X10", "M104 S210", "T0 ; change tool"])
    g, m, other = translator.sort_and_filter_dict()
    assert "G1: Linear Move" in g
    assert "M104: Set Hotend Temperature" in m
    assert "T0: Special command" in other  # neither G nor M


def test_metadata_always_lands_in_other_dict(translator, mapping):
    feed(translator, mapping, ["G1 X10", "; bed_temperature = 60", "; filament_type = PLA"])
    g, m, other = translator.sort_and_filter_dict()
    assert other["bed_temperature"] == "60"
    assert other["filament_type"] == "PLA"
    assert not g.get("bed_temperature")


def test_comments_and_blanks_are_not_aggregated(translator, mapping):
    feed(translator, mapping, ["; just a note", "", ";LAYER:5"])
    g, m, other = translator.sort_and_filter_dict()
    assert (g, m, other) == ({}, {}, {})


def test_repeated_command_becomes_list(translator, mapping):
    feed(translator, mapping, ["M104 S210", "M104 S230"])
    _, m, _ = translator.sort_and_filter_dict(lists_to_strings=False)
    assert m["M104: Set Hotend Temperature"] == ["S210", "S230"]


def test_lists_to_strings_flag(translator, mapping):
    feed(translator, mapping, ["M104 S210", "M104 S230"])
    _, m, _ = translator.sort_and_filter_dict(lists_to_strings=True)
    assert m["M104: Set Hotend Temperature"] == "['S210', 'S230']"


def test_no_filter_merges_commands_and_metadata(translator, mapping):
    feed(translator, mapping, ["G1 X10", "; bed_temperature = 60"])
    (merged,) = translator.sort_and_filter_dict(should_filter=False)
    assert "G1: Linear Move" in merged
    assert merged["bed_temperature"] == "60"


def test_sorting_is_numeric_within_prefix(translator, mapping):
    # G28 must sort after G1 (numeric), not lexicographically.
    feed(translator, mapping, ["G28", "G1 X1"])
    g, _, _ = translator.sort_and_filter_dict(should_sort=True)
    assert list(g.keys()) == ["G1: Linear Move", "G28: Auto Home"]


# --- FEAT-2: aggregation modes ----------------------------------------------------

def test_full_keeps_every_occurrence(translator, mapping):
    feed(translator, mapping, ["M104 S210", "M104 S210", "M104 S230"])
    _, m, _ = translator.sort_and_filter_dict(lists_to_strings=False, aggregation="full")
    assert m["M104: Set Hotend Temperature"] == ["S210", "S210", "S230"]


def test_compact_dedupes_to_unique_values(translator, mapping):
    feed(translator, mapping, ["M104 S210", "M104 S210", "M104 S230"])
    _, m, _ = translator.sort_and_filter_dict(lists_to_strings=False, aggregation="compact")
    assert m["M104: Set Hotend Temperature"] == ["S210", "S230"]


def test_compact_single_unique_value_is_scalar(translator, mapping):
    feed(translator, mapping, ["M104 S210", "M104 S210"])
    _, m, _ = translator.sort_and_filter_dict(lists_to_strings=False, aggregation="compact")
    assert m["M104: Set Hotend Temperature"] == "S210"


def test_compact_movement_becomes_axis_ranges(translator, mapping):
    feed(translator, mapping, ["G1 X10 Y5 F1800", "G1 X20 Y2", "G1 X15 Y8"])
    g, _, _ = translator.sort_and_filter_dict(lists_to_strings=False, aggregation="compact")
    assert g["G1: Linear Move"] == {"F": [1800.0, 1800.0], "X": [10.0, 20.0], "Y": [2.0, 8.0]}


def test_count_counts_occurrences(translator, mapping):
    feed(translator, mapping, ["M104 S210", "M104 S210", "M104 S230"])
    _, m, _ = translator.sort_and_filter_dict(lists_to_strings=False, aggregation="count")
    assert m["M104: Set Hotend Temperature"] == {"S210": 2, "S230": 1}


def test_count_applies_to_movement_commands_too(translator, mapping):
    feed(translator, mapping, ["G1 X10", "G1 X10", "G1 X20"])
    g, _, _ = translator.sort_and_filter_dict(lists_to_strings=False, aggregation="count")
    assert g["G1: Linear Move"] == {"X10": 2, "X20": 1}


def test_default_aggregation_is_compact(translator, mapping):
    feed(translator, mapping, ["M104 S210", "M104 S210"])
    _, m, _ = translator.sort_and_filter_dict(lists_to_strings=False)
    assert m["M104: Set Hotend Temperature"] == "S210"  # deduped == compact
