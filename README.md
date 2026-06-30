# GCode Translator

A powerful Python-based tool for reading, interpreting, and converting standard and binary G-code (`.bgcode`) files.  
It integrates a native C++ binary (`bgcode`) and uses web scraping (3) to retrieve command documentation from Marlin firmware resources
or a local (1) / package (2) marlin_mapping.json file.

Using this order (1) > (2) > (3) in default **use() / CLI** mode!

---

## 🚀 Features

- ✅ Translate raw G-code lines into human-readable explanations
- ✅ Supports `.gcode`, `.bgcode`, and `.gx` formats
- ✅ Integrates with native C++ converter (`bgcode`) for decoding binary formats
- ✅ Able to automatically scrapes G/M-code documentation from Marlin's official site or use a local one
- ✅ Supports embedded thumbnails (base64 or binary)
- ✅ CLI access via `gcode-translator` command

---

## 🧪 Installation

### 🛠 For local development:

```bash
git clone https://github.com/herrdivad/GCode_Translator
cd gcode-translator
pip install -e .
```

### 📦 Install directly via pip:

```bash
pip install git+https://github.com/herrdivad/GCode_Translator
```

---

## ✅ Tests

```bash
pip install -e ".[dev]"      # installs pytest
pytest                       # full suite (~10s)
pytest -m "not slow"         # skip the large-file integration test (~7s)
```

The suite (`tests/`) covers command translation, metadata extraction, dict aggregation,
thumbnail/`.gx` image handling, and the `use()` library API. Unit tests use inline G-code
snippets; integration tests run real files from `exFiles/` end-to-end (PrusaSlicer and
AnycubicSlicer), so the metadata/command behaviour is checked against actual slicer output.

---

## 🖥️ CLI Usage

After installation, use the command:

```bash
gcode-translator path/to/your/file.gcode
```

> It processes the G-code file and outputs interpreted descriptions line by line into a file named output.txt (overwrite!).

---

## 📦 Dependencies

This project uses the following packages:

- [`selenium`](https://pypi.org/project/selenium/)
  - selenium requires Chrome or Chromium installed on your system and be accessible in headless mode. Otherwise use this code with an offline mapping JSON file (should also be delivered by this Repo). 
- [`beautifulsoup4`](https://pypi.org/project/beautifulsoup4/)
- [`platformdirs`](https://pypi.org/project/platformdirs/)
  - locates the per-user cache directory. The G/M-code mapping ships read-only inside the package; a freshly scraped mapping is cached under `platformdirs.user_cache_dir("gcode-translator")` (e.g. `~/.cache/gcode-translator/` on Linux) instead of being written into the installed package.

The `bgcode` Linux binary is included in the package and used automatically.
`bgcode` was built from the official source code from 
[Prusa3d](https://github.com/prusa3d/libbgcode) using the [AGPL-3.0 license](https://www.gnu.org/licenses/agpl-3.0.html.en).
It is used as a subprocess, and it use agrees with the [GPL FAQ](https://www.gnu.org/licenses/gpl-faq.en.html#MereAggregation).
If there are complaints, I declare hereby, that I will remove the binary ASAP or change license.

---

## 🧠 Python API Usage

You can also use it programmatically. `use()` **returns** the aggregated result
(`[g_dict, m_dict, other_dict]`) and, when called as a library, is side-effect free
(no files written, no stdout output):

```python
from gcode_translator.GCode_Translator import use

# Library mode: returns data, writes nothing.
g_codes, m_codes, other = use("your_file.gcode")

# Opt in to file output explicitly if you want it:
result = use("your_file.gcode", output_txt_path="output.txt", preview_path="preview.png")

# Get the embedded thumbnail(s) as raw bytes, without writing any file:
dicts, previews = use("your_file.gcode", return_preview=True)
for img in previews:          # a file may contain several thumbnails
    ...                       # e.g. hand the bytes to a converter / PIL.Image
```

The result is `[g_dict, m_dict, other_dict]`: G-commands, M-commands, and everything else.
Slicer metadata written as `; key = value` or `; key: value` comments (e.g.
`temperature`, `filament_type`, `nozzle_diameter`) is collected into `other_dict`, so the
converter can read print settings that have no direct G/M-command equivalent.

### Aggregation modes

A command (or setting) usually appears many times. The `aggregation` argument of `use()`
controls how those repeated values are reduced. Given, for example:

```
M104 S210
M104 S210
M104 S230
G1 X10 Y5
G1 X20 Y2
```

| Mode | `M104` value | `G1` (movement) value | Notes |
|------|--------------|-----------------------|-------|
| `"compact"` *(default)* | `["S210", "S230"]` | `{"X": [10.0, 20.0], "Y": [2.0, 5.0]}` | Unique values; movement commands (`G0`–`G3`) become per-axis `[min, max]` ranges. A single unique value is returned as a scalar (`"S210"`). |
| `"count"` | `{"S210": 2, "S230": 1}` | `{"X10 Y5": 1, "X20 Y2": 1}` | `{value: occurrences}` for **every** command, movement included. |
| `"full"` | `["S210", "S210", "S230"]` | `["X10 Y5", "X20 Y2"]` | Every occurrence, in order, duplicates kept (the original behaviour). |

```python
result = use("your_file.gcode", aggregation="count")   # "compact" | "count" | "full"
```

Why this matters: a high-frequency command can otherwise explode the result — in one real
file `SET_VELOCITY_LIMIT` occurred **59,825** times with only **2** distinct values, so
`"compact"`/`"count"` reduce that single entry from 59,825 items to 2. `"compact"` is the
default because it is the most readable; `"count"` keeps frequencies; `"full"` keeps raw data.
An unknown mode raises `ValueError`.

> The CLI (`gcode-translator <file>`) keeps the old behavior and writes `output.txt`
> and `preview.png` into the current directory.

## Intended use in other projects 

- [chemotion-converter-app](https://github.com/ComPlat/chemotion-converter-app) as part of the gcode_reader


---

## 📁 Project Structure

```
gcode_translator/
├── GCode_Translator.py          # CLI and translation logic
├── Binary_GCode_Translator.py   # Binary decoding using native binary
├── GCode_Mapping.py             # G/M code mapping using web scraping
├── helper.py                    # Parser and helper functions
├── bgcode                       # Embedded C++ executable
├── marlin_mapping.json          # Package marlin mapping file for systems without Internet connection
```

---

## 🤝 Contributing

Contributions, suggestions, and bug reports are welcome.  
Please open an issue or a pull request.

---

## 🪪 License

MIT License – see [LICENSE](./LICENSE).

---

## 👤 Author

**David Herrmann**  
<david.herrmann@kit.edu>
