"""Tests for the Marlin mapping loader (BUG-1: cache + packaged default, no cwd/resources)."""
from platformdirs import user_cache_dir

from gcode_translator.GCode_Mapping import MarlinGcodeScraper


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
