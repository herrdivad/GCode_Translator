import json
import os
import time
import re
from pathlib import Path
import importlib.resources as resources

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
from abc import ABC, abstractmethod
from enum import Enum, auto


class GCodeFlavor(Enum):
    GENERIC = auto()
    MARLIN = auto() # currently in all use cases, MARLIN Firmware is used!
    # KLIPPER = auto()
    # REPETIER = auto()


class GCodeMapping(ABC):
    def __init__(self):
        self.gcode_type = GCodeFlavor.GENERIC
        # print("Initializing GCode Mapping for ...")

    def fetch_gcode_mapping(self):
        pass

    def set_type(self, found_type):
        self.gcode_type = found_type


class MarlinGcodeScraper(GCodeMapping):
    def __init__(self, url="https://marlinfw.org/meta/gcode/"):
        """
        Initializes the Marlin G-code scraper.
        If url="local", attempts to load from a local JSON file instead of scraping.
        """
        super().__init__()
        self.default_url = "https://marlinfw.org/meta/gcode/"
        self.use_local_cache = (url == "local")
        self.url = self.default_url if self.use_local_cache else url
        # Use importlib to access package resource safely
        self.mapping_resource_package = "gcode_translator"
        self.mapping_resource_file = "marlin_mapping.json"
        self.local_json_map_path = Path(os.getcwd()) / "resources" / self.mapping_resource_file
        self.driver = None

        if not self.use_local_cache:
            self._init_driver()

    def _init_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--disable-gpu")
        self.driver = webdriver.Chrome(options=chrome_options)

    def close(self):
        """Close the Selenium browser session."""
        if self.driver:
            self.driver.quit()

    def fetch_gcode_mapping(self):
        """
        Fetches the G-code mapping either from a local JSON file or by scraping the Marlin website.
        If website:
            Loads the Marlin G-code page in a real browser session,
            extracts the fully rendered HTML, and parses it into a single dictionary.
        If a code is a range (e.g. G0-G1), it splits into multiple entries:
            {
              "G0": "Linear Move",
              "G1": "Linear Move",
              ...
            }
        """
        # Case 1: Local JSON file exists
        if self.use_local_cache:
            try:
                # First try: in resource folder from local path
                with open(self.local_json_map_path, "r", encoding="utf-8") as f:
                    print("✅ Loaded G-code mapping from local file (non-package mode).")
                    return json.load(f)
            except FileNotFoundError:
                # Fallback for package usage: direct delivered file from package (No update / up-to-lateness guarantee)
                try:
                    # second try: in-package resource
                    with resources.files(self.mapping_resource_package).joinpath(self.mapping_resource_file).open("r",
                                                                                                                  encoding="utf-8") as f:
                        print("✅ Loaded G-code mapping from installed package resource.")
                        return json.load(f)
                except (FileNotFoundError, ModuleNotFoundError, AttributeError):
                    print("⚠️ No local mapping found. Falling back to web scraping...")
                    self._init_driver()

        # Case 2: Scrape using Selenium
        if not self.driver:
            raise RuntimeError(
                "❌ Selenium driver not initialized – cannot scrape.\n"
                "💡 Make sure Chrome or Chromium is installed and accessible in headless mode."
                "➡️ If your are not allowed to use the internet connection, "
                "✅ make sure to get an offline / local 'resources/marlin_mapping.json' file from the Repo or dev system *and* use this code only in url='local' (default) mode."
            )

        print("🌐 Scraping Marlin G-code documentation...")
        self.driver.get(self.url)
        time.sleep(3)  # wait for JavaScript to render content
        html = self.driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        gcode_map = {}

        # Process all <li> elements that might contain G-/M-code mappings
        for li in soup.find_all("li"):
            li_text = li.get_text().strip()
            match = re.match(r'^([GM]\d+(?:-[GM]?\d+)?)(?:[:\s-]+)(.*)$', li_text, re.IGNORECASE)
            if not match:
                continue

            code_text, description = match.groups()
            description = description.strip()

            # Handle code ranges (e.g. G0-G1)
            if '-' in code_text:
                range_match = re.match(r'^([GM])(\d+)-([GM])?(\d+)$', code_text, re.IGNORECASE)
                if range_match:
                    letter_start, start_num, letter_end, end_num = range_match.groups()
                    if not letter_end:
                        letter_end = letter_start
                    for i in range(int(start_num), int(end_num) + 1):
                        gcode_map[f"{letter_start}{i}"] = description
                else:
                    gcode_map[code_text] = description
            else:
                gcode_map[code_text] = description

        try:
            self.local_json_map_path = Path(__file__).parent / "resources" / "marlin_mapping.json"
            self.local_json_map_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.local_json_map_path, "w", encoding="utf-8") as f:
                json.dump(gcode_map, f, indent=2)
                print("💾 Saved scraped mapping as local JSON.")
        except Exception as e:
            print(f"⚠️ Could not save local mapping: {e}")

        return gcode_map


if __name__ == "__main__":
    scraper = MarlinGcodeScraper("local")
    # scraper = MarlinGcodeScraper() # use this to update your local mapping with the latest online version
    try:
        mapping = scraper.fetch_gcode_mapping()
        # Print each code sorted by alphanumeric order
        for code in sorted(mapping.keys()):
            print(f"{code}: {mapping[code]}")
    finally:
        scraper.close()
