from Mapping import MarlinGcodeScraper
from typing import Dict


def init_mapping():
    scraper = MarlinGcodeScraper()
    mapping = {}  # initialize as valid empty dic
    try:
        mapping = scraper.fetch_gcode_mapping()
    except Exception as e:
        print("❌ Failed to fetch G-code mapping:", e)
    finally:
        scraper.close()
    return mapping


def explain_gcode_line(line_to_translate, mapping):
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


with open("MainConnectorCover_0.4n_0.2mm_PLA_MINIIS_16m(1).gcode") as f:
    gcode_mapping = init_mapping()
    for line in f:
        result = explain_gcode_line(line, gcode_mapping)
        print(result)
