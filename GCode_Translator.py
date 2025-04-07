import base64

from GCode_Mapping import MarlinGcodeScraper, GCode_Mapping, GCodeFlavor
from typing import Dict


class GCodeTranslator:
    def __init__(self):
        self.line_is_a_picture = False
        self.picture_code = []
        print("Initializing GCode Translator")

    def init_mapping(self):
        scraper = GCode_Mapping()
        if scraper.gcode_type == GCodeFlavor.GENERIC or scraper.gcode_type == GCodeFlavor.MARLIN:
            scraper = MarlinGcodeScraper()
        mapping = {}  # initialize as valid empty dic
        try:
            mapping = scraper.fetch_gcode_mapping()
        except Exception as e:
            print("❌ Failed to fetch G-code mapping:", e)
        finally:
            scraper.close()
        return mapping

    def explain_gcode_line(self, line_to_translate, mapping):
        if line_to_translate.startswith("; thumbnail end"):
            self.line_is_a_picture = False
            self.transform_preview_picture()
            return ""
        if line_to_translate.startswith("; thumbnail begin") or self.line_is_a_picture:
            self.line_is_a_picture = True
            self.extract_preview_picture(line_to_translate)
            return ""
        if line_to_translate.startswith(";") or line_to_translate == "\n":
            return line_to_translate
        parts = line_to_translate.split()
        cmd = parts[0]
        params = parts[1:]
        if mapping is not None:
            explanation = mapping.get(cmd, "Unknown command")
            return f"{cmd}: {explanation} | Parameter: {', '.join(params)}"
        else:
            return f"{cmd}: {' '.join(params)}"

    def extract_preview_picture(self, line_to_translate):
        if not line_to_translate.startswith("; thumbnail"):
            self.picture_code.append(line_to_translate.lstrip("; ").strip())

    def transform_preview_picture(self):
        if not self.picture_code:
            print("⚠️ No preview image data found.")
            return

        base64_data = "".join(self.picture_code)
        try:
            image_data = base64.b64decode(base64_data)
        except Exception as e:
            print(f"❌ Failed to decode preview image: {e}")
            return

        pic_name = "preview.png"
        with open(pic_name, "wb") as img_file:
            img_file.write(image_data)
        print(f"✅ Thumbnail saved as '{pic_name}'.")


if __name__ == "__main__":
    with open("MainConnectorCover_0.4n_0.2mm_PLA_MINIIS_16m(1).gcode") as f:
        translator = GCodeTranslator()
        gcode_mapping = translator.init_mapping()
        for line in f:
            result = translator.explain_gcode_line(line, gcode_mapping)
            print(result)
