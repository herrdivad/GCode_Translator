"""Tests for the Marlin mapping loader (BUG-1: cache + packaged default, no cwd/resources),
the firmware-flavor abstraction (BUG-7), and optional-selenium handling (SCRP-1)."""
import sys

import pytest
from platformdirs import user_cache_dir

import gcode_translator.GCode_Mapping as GM
from gcode_translator.GCode_Mapping import MarlinGcodeScraper


def _hide_scrape_deps(monkeypatch):
    """Simulate a system without the optional [scrape] extras installed."""
    for name in ("selenium", "selenium.webdriver", "bs4"):
        monkeypatch.setitem(sys.modules, name, None)


def test_local_mapping_loads_without_network():
    """url='local' must load the bundled mapping via importlib.resources (no scraping)."""
    scraper = MarlinGcodeScraper("local")
    try:
        mapping = scraper.fetch_gcode_mapping()
    finally:
        scraper.close()
    assert mapping.get("G1") == "Linear Move"
    assert len(mapping) > 50


def test_cache_path_lives_in_user_cache_dir():
    scraper = MarlinGcodeScraper("local")
    scraper.close()
    assert str(scraper.cache_path).startswith(user_cache_dir("gcode-translator"))
    assert scraper.cache_path.name == "marlin_mapping.json"


# --- BUG-7: firmware-flavor abstraction (kept as an extension point, made sound) ---

def test_base_class_is_truly_abstract():
    with pytest.raises(TypeError):
        GM.GCodeMapping()  # abstract fetch_gcode_mapping -> cannot instantiate


def test_scrapers_registry_maps_flavors_to_scraper():
    assert GM.SCRAPERS[GM.GCodeFlavor.MARLIN] is MarlinGcodeScraper
    assert GM.GCodeFlavor.GENERIC in GM.SCRAPERS


def test_marlin_scraper_reports_its_flavor():
    scraper = MarlinGcodeScraper("local")
    scraper.close()
    assert scraper.gcode_type is GM.GCodeFlavor.MARLIN


# --- SCRP-1: selenium/bs4 are optional (only needed for scraping) ------------------

def test_local_mapping_works_without_selenium(monkeypatch):
    _hide_scrape_deps(monkeypatch)
    scraper = MarlinGcodeScraper("local")
    try:
        mapping = scraper.fetch_gcode_mapping()
    finally:
        scraper.close()
    assert mapping.get("G1") == "Linear Move"


def test_scraping_without_selenium_raises_helpful_error(monkeypatch):
    _hide_scrape_deps(monkeypatch)
    with pytest.raises(RuntimeError, match="scrape"):
        MarlinGcodeScraper()  # non-local -> _init_driver tries to import selenium
