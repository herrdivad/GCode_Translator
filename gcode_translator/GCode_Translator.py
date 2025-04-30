import base64
import os
import sys

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


class GCodeTranslator:
    def __init__(self):
        self.line_is_a_picture = False
        self.picture_code = []
        self.output_dict = {}
        # print("Initializing GCode Translator")

    def init_mapping(self):
        scraper = GCode_Mapping.GCodeMapping()
        if scraper.gcode_type == GCode_Mapping.GCodeFlavor.GENERIC or scraper.gcode_type == GCode_Mapping.GCodeFlavor.MARLIN:
            scraper = GCode_Mapping.MarlinGcodeScraper()
        mapping = {}  # initialize as valid empty dic
        try:
            mapping = scraper.fetch_gcode_mapping()
        except Exception as e:
            print("❌ Failed to fetch G-code mapping:", e)
        finally:
            scraper.close()
        return mapping

    def explain_gcode_line(self, line_to_translate, mapping, preview_picture_needed=True, preview_pic_as_file=True) -> tuple[str, bool]:
        if line_to_translate.startswith("; thumbnail end"):
            self.line_is_a_picture = False
            if preview_picture_needed and preview_pic_as_file:
                self.transform_preview_picture()
            return "", False
        if line_to_translate.startswith("; thumbnail begin") or self.line_is_a_picture:
            if not self.line_is_a_picture:
                self.picture_code = []
                self.line_is_a_picture = True
            if preview_picture_needed:
                self.extract_preview_picture(line_to_translate)
            return "", False
        blacklist = ["thumbnail", "base64", "preview", "width:", "height:", "layer", "type:", "time_elapsed:", "mesh:", "gimage", "simage",
                     "extrude_ratio:", "structure:", "support-"]  # if some important Comment or Metadata is missing, check this blacklist and adjust!
        if self.is_valid_comment(line_to_translate, blacklist):
            return line_to_translate[1:200].strip(), True
        if line_to_translate.startswith(";") or line_to_translate.strip() == "":
            return line_to_translate, False

        parts = line_to_translate.strip().split()
        cmd = parts[0]
        params = parts[1:]

        if mapping is not None:
            explanation = mapping.get(cmd, "Unknown command")
            param_str = "True" if not params else " ".join(params)
            # if param_str == "True":
                # print(f"{cmd}: {explanation} | Parameter: {param_str}")
            return f"{cmd}: {explanation} | Parameter: {param_str}", False
        else:
            param_str = "True" if not params else " ".join(params)
            return f"{cmd}: Unknown mapping | Parameter: {param_str}", False

    def translated_line_to_dict(self, translated_line):
        if "|" in translated_line:
            cmd = translated_line.split("|")[0].strip()
            comment_hint = translated_line.split(";")[-1].strip() if ";" in translated_line else ""
            if "Unknown command" in cmd and comment_hint:
                cmd = cmd.replace("Unknown command", "Special command - " + comment_hint)
            params = translated_line.split("|")[1].split(";")[0].strip(' ,\t\n')
            if "Parameter:" in params:
                param_parts = params.split(":", 1)
                if len(param_parts) == 2 and param_parts[1].strip() == "":
                    params += " True"
            helper.add_to_dict_smart(self.output_dict, cmd, params)

    def clean_str_from_dict(self, string_to_clean="Parameter:"):
        """
        Removes a given substring from all values in the output_dict.
        Works for both string values and lists of strings.

        :param string_to_clean: The substring to remove from all values
        """
        for key in self.output_dict:
            value = self.output_dict[key]

            if isinstance(value, str):
                # Clean substring from string
                self.output_dict[key] = value.replace(string_to_clean, "").strip()

            elif isinstance(value, list):
                # Clean substring from each element in the list
                cleaned_list = [
                    v.replace(string_to_clean, "").strip() if isinstance(v, str) else v
                    for v in value
                ]
                self.output_dict[key] = cleaned_list

    def sort_and_filter_dict(self, lists_to_strings=False, should_sort=True, should_filter=True):
        if should_sort:
            # noinspection PyUnusedLocal
            def my_gcode_sort_key(key_: str):
                # inner function to extract sortable key
                prefix = key_[0]
                digits = ''.join(filter(lambda c: c.isdigit(), key_))
                number = int(digits) if digits else 77777  # Magic Number / WTF-Marker: Fallback case for no number Codes
                return prefix, number

            self.output_dict = dict(sorted(self.output_dict.items(), key=lambda item: my_gcode_sort_key(item[0])))

        if should_filter:
            g_dict = {}
            m_dict = {}
            other_dict = {}
            for key, value in self.output_dict.items():
                if key.startswith("G"):
                    g_dict[key] = str(value) if lists_to_strings else value
                elif key.startswith("M"):
                    m_dict[key] = str(value) if lists_to_strings else value
                else:
                    other_dict[key] = str(value) if lists_to_strings else value

            return [g_dict, m_dict, other_dict]

        return [self.output_dict]

    def extract_preview_picture(self, line_to_translate):
        if not line_to_translate.startswith("; thumbnail"):
            self.picture_code.append(line_to_translate.lstrip("; ").strip())

    def get_preview_as_stream(self):
        if not self.picture_code:
            print("⚠️ No preview image data found.")
            return None

        base64_data = "".join(self.picture_code)
        try:
            return base64.b64decode(base64_data)
        except Exception as e:
            print(f"❌ Failed to decode preview image: {e}")
            return None

    def transform_preview_picture(self):
        image_data = self.get_preview_as_stream()
        if not image_data:
            return
        pic_name = "preview.png"
        with open(pic_name, "wb") as img_file:
            img_file.write(image_data)
        print(f"✅ Thumbnail saved as '{pic_name}'.")

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


def use(file: str = None):
    """
    Process a G-code file either from CLI arguments or direct Python call.

    :param file: Optional; path to the G-code file. If None, sys.argv[1] is used.
    """
    if file is None:
        if len(sys.argv) != 2:
            print("Usage: python -m gcode_translator.GCode_Translator <GCode file>")
            sys.exit(1)
        file = sys.argv[1]
    if os.path.isfile(file):
        if file.endswith(".bgcode"):
            file = Binary_GCode_Translator.binary_gcode_to_gcode(file)
            if not file:
                sys.exit(666)
        if file.endswith(".gcode") or file.endswith(".gx"):
            if file.endswith(".gx"):
                print("Extracting binary bmp from G-code file...")
                Binary_GCode_Translator.extract_binary_picture_from_gx(file, "preview_gx.bmp")
                print("binary bmp extracted.")
            with open(file, "r", encoding="utf-8", errors="replace") as f:
                translator = GCodeTranslator()
                gcode_mapping = translator.init_mapping()
                with open("output.txt", "w") as new_file:
                    pass
                with open("output.txt", "a", encoding="utf-8", errors="replace") as o:
                    for line in f:
                        result, _ = translator.explain_gcode_line(line,
                                                                  gcode_mapping)  # second parameter is a bool and not needed here
                        if result and result.strip():
                            o.write(result + "\n")
                        translator.translated_line_to_dict(result)
                translator.clean_str_from_dict()
                dictList_for_converter = translator.sort_and_filter_dict(True)
                print(dictList_for_converter)
    else:
        print("Please provide a valid GCode (gcode, bgcode, gx file.")
        sys.exit(2)


if __name__ == "__main__":
    use()
    print("EOC reached")
