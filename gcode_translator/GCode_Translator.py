import base64
import io
import logging
import os
import re
import sys
from dataclasses import dataclass

try:
    from . import helper
except ImportError:
    import helper  # fallback für standalone
try:
    from . import Binary_GCode_Translator
except ImportError:
    import Binary_GCode_Translator
try:
    from . import GCode_Mapping
except ImportError:
    import GCode_Mapping

logger = logging.getLogger(__name__)

# Metadata comments come in two shapes:
#   "; key = value"  -> a slicer setting. These are reliable, so they are captured
#                       even when the comment blacklist would reject the key (e.g.
#                       "layer_height", "first_layer_temperature"): real per-layer
#                       noise never uses '='.
#   "; key: value"   -> captured only if the line survives the comment blacklist,
#                       which is where the per-layer ':' markers live (";LAYER:5",
#                       ";HEIGHT:0.2", "; end of layer_num: ...").
# In both cases the value must be non-empty (so "; design parameters:" and
# "; modifier_phrase =" stay plain comments) and the key must have at least
# _META_MIN_KEY_LEN characters (so axis markers like ";Z:0.2" are ignored).
_META_EQ_RE = re.compile(r"^;\s*([A-Za-z][^=]*?)\s*=\s*(\S.*)$")
_META_COLON_RE = re.compile(r"^;\s*([A-Za-z][\w. -]*?)\s*:\s*(\S.*)$")
_META_MIN_KEY_LEN = 2  # config keys are descriptive; 1-char keys are G-code markers

# Value-aggregation strategies for repeated commands/metadata (see use(aggregation=...)).
AGGREGATIONS = ("compact", "count", "full")
_MOVE_COMMANDS = {"G0", "G1", "G2", "G3"}  # get axis-range treatment in "compact" mode
_AXIS_TOKEN_RE = re.compile(r"^([A-Za-z])([-+]?\d*\.?\d+)$")  # e.g. "X158.835", "Z.25", "E-.8"


def _axis_ranges(values) -> dict:
    """Reduce a list of movement-command parameter sets to per-axis ``[min, max]``.

    e.g. ["X10 Y5 F1800", "X20 Y2"] -> {"X": [10.0, 20.0], "Y": [2.0, 5.0], "F": [1800.0, 1800.0]}
    Tokens that are not ``<letter><number>`` (e.g. the "True" placeholder) are ignored.
    """
    ranges = {}
    for entry in values:
        for token in str(entry).split():
            match = _AXIS_TOKEN_RE.match(token)
            if not match:
                continue
            axis = match.group(1).upper()
            num = float(match.group(2))
            if axis in ranges:
                lo, hi = ranges[axis]
                ranges[axis] = (min(lo, num), max(hi, num))
            else:
                ranges[axis] = (num, num)
    return {axis: [lo, hi] for axis, (lo, hi) in sorted(ranges.items())}


# Sentinel used to tell "argument not supplied" apart from an explicit None.
# Lets CLI mode default to writing files while library mode stays side-effect free.
_UNSET = object()


@dataclass
class GCodeLine:
    """Structured result of translating a single G-code line.

    Replaces the former ``"G1: Linear Move | Parameter: X10"`` string that was
    built and re-parsed elsewhere. The string form is only needed for the
    human-readable file output and is produced on demand via ``output_text``.
    """
    raw: str                              # original, untouched line
    cmd: str | None = None                # "G1" / "M104"; None for comments/blank lines
    explanation: str | None = None        # mapping description, e.g. "Linear Move"
    params: str = ""                       # raw parameter string ("True" when none)
    inline_comment: str = ""              # text after ';' on a command line
    is_comment: bool = False              # True for a meaningful standalone comment
    text: str = ""                         # what to write to the output file ("" = nothing)
    preview: bytes | None = None          # decoded embedded thumbnail (set on "; thumbnail end")
    meta_key: str | None = None           # key of a "; key = value" / "; key: value" pair
    meta_value: str | None = None         # value of that metadata pair

    @property
    def is_command(self) -> bool:
        return self.cmd is not None

    @property
    def is_metadata(self) -> bool:
        return self.meta_key is not None

    @property
    def dict_key(self) -> str:
        """Aggregation key, e.g. ``"G1: Linear Move"``.

        - Mapping hit            -> ``"<cmd>: <description>"``
        - No mapping, but the line carries an inline comment (an explanation)
                                 -> ``"<cmd>: Special command"`` (the comment is the value)
        - No mapping and no comment
                                 -> ``"<cmd>: Unknown command"``
        """
        if self.explanation:
            label = self.explanation
        elif self.inline_comment:
            label = "Special command"
        else:
            label = "Unknown command"
        return f"{self.cmd}: {label}"

    @property
    def dict_value(self) -> str:
        """Aggregation value.

        For a "Special command" (no mapping, but an inline comment) the comment is
        the value. Otherwise the parameters ("True" when there are none).
        """
        if not self.explanation and self.inline_comment:
            return self.inline_comment
        return self.params if self.params else "True"


class GCodeTranslator:
    def __init__(self, preview_path: str | None = None):
        self.line_is_a_picture = False
        self.picture_code = []
        self.output_dict = {}
        self.meta_dict = {}        # "; key = value" / "; key: value" pairs -> other_dict
        self.preview_path = preview_path

    def init_mapping(self, url: str | None = None,
                     flavor: "GCode_Mapping.GCodeFlavor" = GCode_Mapping.GCodeFlavor.MARLIN):
        # Pick the scraper for the requested firmware flavor. New firmwares are added by
        # registering a GCodeMapping subclass in GCode_Mapping.SCRAPERS (see GCodeFlavor).
        scraper_cls = GCode_Mapping.SCRAPERS.get(flavor, GCode_Mapping.MarlinGcodeScraper)
        scraper = scraper_cls() if url is None else scraper_cls(url)
        mapping = {}  # initialize as valid empty dic
        try:
            mapping = scraper.fetch_gcode_mapping()
        except Exception as e:
            logger.error("❌ Failed to fetch G-code mapping: %s", e)
        finally:
            scraper.close()
        return mapping

    def explain_gcode_line(self, line_to_translate, mapping, preview_picture_needed=True) -> GCodeLine:
        if line_to_translate.startswith("; thumbnail end"):
            self.line_is_a_picture = False
            gline = GCodeLine(raw=line_to_translate)
            if preview_picture_needed:
                # Decode the collected base64 block; transform_preview_picture writes a
                # file only if self.preview_path is set and returns the raw bytes either way.
                gline.preview = self.transform_preview_picture()
            return gline
        if line_to_translate.startswith("; thumbnail begin") or self.line_is_a_picture:
            if not self.line_is_a_picture:
                self.picture_code = []
                self.line_is_a_picture = True
            if preview_picture_needed:
                self.extract_preview_picture(line_to_translate)
            return GCodeLine(raw=line_to_translate)
        stripped = line_to_translate.strip()
        # Text after the leading ';' — kept in full for the human-readable output file
        # (no silent truncation; stripped already removed any leading whitespace).
        comment_text = stripped[1:].strip()

        # "; key = value" is a reliable setting -> metadata, regardless of the blacklist.
        eq = _META_EQ_RE.match(stripped)
        if eq and len(eq.group(1).strip()) >= _META_MIN_KEY_LEN:
            return GCodeLine(raw=line_to_translate, text=comment_text,
                             meta_key=eq.group(1).strip(), meta_value=eq.group(2).strip())

        blacklist = ["thumbnail", "base64", "preview", "width:", "height:", "layer", "type:", "time_elapsed:", "mesh:", "gimage", "simage",
                     "extrude_ratio:", "structure:", "support-"]  # if some important Comment or Metadata is missing, check this blacklist and adjust!
        if self.is_valid_comment(line_to_translate, blacklist):
            # "; key: value" on a non-blacklisted comment is metadata (-> other_dict);
            # anything else stays a plain comment that is only written to the output file.
            colon = _META_COLON_RE.match(stripped)
            if colon and len(colon.group(1).strip()) >= _META_MIN_KEY_LEN:
                return GCodeLine(raw=line_to_translate, text=comment_text,
                                 meta_key=colon.group(1).strip(), meta_value=colon.group(2).strip())
            return GCodeLine(raw=line_to_translate, is_comment=True, text=comment_text)
        if line_to_translate.startswith(";") or stripped == "":
            return GCodeLine(raw=line_to_translate, text=line_to_translate.rstrip("\n"))

        # Split off an inline comment first, even when it is glued to the command
        # ("M84; disable motors"), so the command token stays clean ("M84").
        code_part, _, comment_part = stripped.partition(";")
        inline_comment = comment_part.strip()
        parts = code_part.split()
        if not parts:
            # Nothing but a comment remained -> treat as a plain comment line.
            return GCodeLine(raw=line_to_translate, text=line_to_translate.rstrip("\n"))
        cmd = parts[0]
        params = parts[1:]
        param_str = " ".join(params) if params else "True"

        # explanation is the mapping description, or None when there is no match.
        explanation = mapping.get(cmd) if mapping is not None else None

        gline = GCodeLine(raw=line_to_translate, cmd=cmd, explanation=explanation,
                          params=param_str, inline_comment=inline_comment)
        # Human-readable label for the output file keeps the explanation inline.
        if explanation:
            label = explanation
        elif inline_comment:
            label = f"Special command - {inline_comment}"
        else:
            label = "Unknown command"
        gline.text = f"{cmd}: {label} | Parameter: {param_str}"
        return gline

    def add_line_to_dict(self, gline: GCodeLine):
        """Aggregate a translated line into the result dictionaries.

        Commands go to ``output_dict`` (later split into G/M/other); metadata pairs
        go to ``meta_dict`` (always routed into ``other_dict``). Plain comments and
        blank lines are skipped. Works directly on the structured fields.
        """
        if gline.is_metadata:
            helper.add_to_dict_smart(self.meta_dict, gline.meta_key, gline.meta_value)
            return
        if not gline.is_command:
            return
        helper.add_to_dict_smart(self.output_dict, gline.dict_key, gline.dict_value)

    def _aggregate_value(self, key: str, value, aggregation: str):
        """Reduce a collected value (str or list of all occurrences) per strategy.

        - ``full``    -> unchanged (every occurrence, duplicates kept).
        - ``compact`` -> movement commands (G0–G3) become per-axis ``[min, max]`` ranges;
                         everything else becomes its order-preserving set of unique values.
        - ``count``   -> ``{value: occurrences}`` for every command (movement included).

        Pure function: it does not mutate ``self`` (so it is safe to call repeatedly).
        """
        if aggregation == "full":
            return value
        values = value if isinstance(value, list) else [value]
        if aggregation == "compact":
            if key.split(":", 1)[0] in _MOVE_COMMANDS:
                return _axis_ranges(values)
            unique = list(dict.fromkeys(values))
            return unique[0] if len(unique) == 1 else unique
        if aggregation == "count":
            counts = {}
            for v in values:
                counts[v] = counts.get(v, 0) + 1
            return counts
        raise ValueError(f"unknown aggregation {aggregation!r}; expected one of {AGGREGATIONS}")

    def sort_and_filter_dict(self, lists_to_strings=False, should_sort=True, should_filter=True,
                             aggregation="compact"):
        if should_sort:
            # noinspection PyUnusedLocal
            def my_gcode_sort_key(key_: str):
                # inner function to extract sortable key
                prefix = key_[0]
                digits = ''.join(filter(lambda c: c.isdigit(), key_))
                number = int(digits) if digits else 77777  # Magic Number / WTF-Marker: Fallback case for no number Codes
                return prefix, number

            self.output_dict = dict(sorted(self.output_dict.items(), key=lambda item: my_gcode_sort_key(item[0])))

        def render(key, value):
            aggregated = self._aggregate_value(key, value, aggregation)
            return str(aggregated) if lists_to_strings else aggregated

        if should_filter:
            g_dict = {}
            m_dict = {}
            other_dict = {}
            for key, value in self.output_dict.items():
                if key.startswith("G"):
                    g_dict[key] = render(key, value)
                elif key.startswith("M"):
                    m_dict[key] = render(key, value)
                else:
                    other_dict[key] = render(key, value)

            # Metadata pairs always belong in other_dict, regardless of their key.
            for key, value in self.meta_dict.items():
                other_dict[key] = render(key, value)

            return [g_dict, m_dict, other_dict]

        return [{key: render(key, value)
                 for key, value in {**self.output_dict, **self.meta_dict}.items()}]

    def extract_preview_picture(self, line_to_translate):
        if not line_to_translate.startswith("; thumbnail"):
            self.picture_code.append(line_to_translate.lstrip("; ").strip())

    def get_preview_as_stream(self):
        if not self.picture_code:
            logger.warning("⚠️ No preview image data found.")
            return None

        base64_data = "".join(self.picture_code)
        try:
            return base64.b64decode(base64_data)
        except Exception as e:
            logger.error("❌ Failed to decode preview image: %s", e)
            return None

    def transform_preview_picture(self) -> bytes | None:
        """Decode the collected thumbnail and return its raw bytes.

        Writes the image to disk only when ``self.preview_path`` is set; otherwise
        the bytes are returned for in-memory use (e.g. via ``GCodeLine.preview``)
        without touching the filesystem.
        """
        image_data = self.get_preview_as_stream()
        if not image_data:
            return None
        if self.preview_path:
            with open(self.preview_path, "wb") as img_file:
                img_file.write(image_data)
            logger.info("✅ Thumbnail saved as '%s'.", self.preview_path)
        return image_data

    def is_valid_comment(self, com_line: str, blacklist: list[str]) -> bool:
        """
        Checks whether a line is a meaningful G-code comment.
        - Accepts comments that start with ';' or '; ' and contain real content.
        - Ignores lines that contain any blacklisted words.

        :param com_line: The line to check (typically from a G-code file)
        :param blacklist: List of lowercase terms to reject (e.g. ['thumbnail', 'base64'])
        :return: True if the line is a meaningful comment and not blacklisted
        """
        # Normalize line for easier checks
        com_line = com_line.strip()

        # Rule 1: Comment starts with '; ' and contains more than just one word
        has_comment_structure = (
                (com_line.startswith("; ") and " " in com_line[2:]) or
                (com_line.startswith(";") and len(com_line) > 1 and com_line[1] != " ")
        )

        # Rule 2: Blacklist check (case-insensitive)
        not_blacklisted = not any(bad_word in com_line.lower() for bad_word in blacklist)

        return has_comment_structure and not_blacklisted


def use(file: str = None, output_txt_path=_UNSET, preview_path=_UNSET,
        lists_to_strings: bool = True, mapping_source: str = "local",
        return_preview: bool = False, aggregation: str = "compact"):
    """
    Process a G-code file either from CLI arguments or a direct Python call.

    :param file: Path to the G-code file. If ``None``, ``sys.argv[1]`` is used (CLI mode).
    :param output_txt_path: Where to write the human-readable per-line output.
        Defaults to ``"output.txt"`` in CLI mode and to ``None`` (no file written)
        when called as a library.
    :param preview_path: Where to save an embedded thumbnail. Same CLI/library
        defaulting as ``output_txt_path``; ``None`` disables writing the thumbnail
        to disk (it can still be returned in memory, see ``return_preview``).
    :param lists_to_strings: Whether list values in the result are stringified.
    :param mapping_source: ``"local"`` (default), ``None`` for the live Marlin URL,
        or a custom URL.
    :param return_preview: If ``True``, return a ``(dict_list, previews)`` tuple where
        ``previews`` is a list of the extracted thumbnail images as raw ``bytes`` (a file
        may contain several). The pictures are decoded in memory without writing any file
        unless ``preview_path`` is also set.
    :param aggregation: How repeated values per command/setting are reduced:
        ``"compact"`` (default) keeps unique values and turns movement commands (G0–G3)
        into per-axis ``[min, max]`` ranges; ``"count"`` produces ``{value: occurrences}``
        for every command; ``"full"`` keeps every occurrence (duplicates included).
    :return: The sorted/filtered ``[g_dict, m_dict, other_dict]`` list. When
        ``return_preview`` is ``True``, a ``(list, previews)`` tuple instead.
    """
    if aggregation not in AGGREGATIONS:
        raise ValueError(f"aggregation must be one of {AGGREGATIONS}, got {aggregation!r}")

    cli_mode = file is None

    # Resolve side-effect defaults: write files in CLI mode, stay silent as a library.
    if output_txt_path is _UNSET:
        output_txt_path = "output.txt" if cli_mode else None
    if preview_path is _UNSET:
        preview_path = "preview.png" if cli_mode else None

    # Decode thumbnails whenever the caller wants them returned OR wants them written.
    want_preview = return_preview or (preview_path is not None)

    if cli_mode:
        if len(sys.argv) != 2:
            print("Usage: python -m gcode_translator.GCode_Translator <GCode file>")
            sys.exit(1)
        file = sys.argv[1]

    if not os.path.isfile(file):
        msg = "Please provide a valid GCode (gcode, bgcode, gx) file."
        if cli_mode:
            print(msg)
            sys.exit(2)
        raise FileNotFoundError(msg + f" Got: {file!r}")

    if file.endswith(".bgcode"):
        file = Binary_GCode_Translator.binary_gcode_to_gcode(file)
        if not file:
            raise RuntimeError("Binary G-code conversion failed (Linux + bgcode binary required).")

    if not (file.endswith(".gcode") or file.endswith(".gx")):
        raise ValueError(f"Unsupported file type: {file!r}")

    previews = []

    if file.endswith(".gx") and want_preview:
        # Write the .bmp only when an output location is desired (preview_path set);
        # otherwise just decode it into memory. extract_* returns None when the .gx
        # carries no embedded BMP (e.g. plain-text G-code with a .gx extension).
        gx_bmp_path = "preview_gx.bmp" if preview_path is not None else None
        gx_preview = Binary_GCode_Translator.extract_binary_picture_from_gx(file, gx_bmp_path)
        if gx_preview:
            previews.append(gx_preview)
            logger.info("Extracted embedded BMP thumbnail from .gx file.")

    translator = GCodeTranslator(preview_path=preview_path)
    gcode_mapping = translator.init_mapping(mapping_source)

    # A binary .gx prefixes the text G-code with a header + BMP thumbnail; skip that
    # preamble so its bytes are not mis-parsed as commands. Plain-text files start at 0.
    text_offset = Binary_GCode_Translator.gcode_text_offset(file) if file.endswith(".gx") else 0

    out_file = open(output_txt_path, "w", encoding="utf-8", errors="replace") if output_txt_path else None
    try:
        raw = open(file, "rb")
        raw.seek(text_offset)
        with io.TextIOWrapper(raw, encoding="utf-8", errors="replace") as f:
            for line in f:
                gline = translator.explain_gcode_line(
                    line, gcode_mapping,
                    preview_picture_needed=want_preview,
                )
                if out_file and gline.text and gline.text.strip():
                    out_file.write(gline.text + "\n")
                translator.add_line_to_dict(gline)
                if gline.preview is not None:
                    previews.append(gline.preview)
    finally:
        if out_file:
            out_file.close()

    result = translator.sort_and_filter_dict(lists_to_strings, aggregation=aggregation)
    if return_preview:
        return result, previews
    return result


def main():
    """Console-script entry point (CLI). Configures logging, then delegates to use()."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    result = use()
    print(result)


if __name__ == "__main__":
    main()
    print("EOC reached")
