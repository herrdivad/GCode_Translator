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

**Required:**

- [`platformdirs`](https://pypi.org/project/platformdirs/) ([MIT license](https://github.com/tox-dev/platformdirs/blob/main/LICENSE))
  - locates the per-user cache directory. The G/M-code mapping ships read-only inside the package; a freshly scraped mapping is cached under `platformdirs.user_cache_dir("gcode-translator")` (e.g. `~/.cache/gcode-translator/` on Linux) instead of being written into the installed package.

**Optional — only for re-scraping the Marlin mapping** (`pip install gcode-translator[scrape]`):

- [`selenium`](https://pypi.org/project/selenium/)
  - selenium requires Chrome or Chromium installed and accessible in headless mode.
- [`beautifulsoup4`](https://pypi.org/project/beautifulsoup4/)

The translator works fully offline using the bundled mapping; the `[scrape]` extras are only needed when you explicitly fetch a fresh mapping from marlinfw.org. Without them, the scraping path raises a clear error telling you to install the extra.

### `bgcode` binary — licensing & source

The `bgcode` Linux binary is bundled in the package (`gcode_translator/bgcode`) and used
automatically to convert Prusa `.bgcode` files. It is a separately compiled, **unmodified**
build of the [Prusa3D libbgcode project](https://github.com/prusa3d/libbgcode), which is
licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**. The binary is
therefore **not** covered by this project's MIT license; when using or redistributing it you
must comply with the AGPL-3.0. The full license text ships next to the binary at
[`gcode_translator/LICENSE.AGPL-3.0.txt`](./gcode_translator/LICENSE.AGPL-3.0.txt).

`bgcode` is invoked only as a separate subprocess (arm's-length communication via command-line
arguments and files). Under the FSF's [GPL FAQ on mere aggregation](https://www.gnu.org/licenses/gpl-faq.en.html#MereAggregation)
this does not create a combined work, so the MIT-licensed Python code keeps its MIT license.
Distributing the AGPL binary, however, carries the AGPL's own obligations (see below).

**Corresponding Source (AGPL-3.0 §6).** The shipped binary corresponds exactly to this public
revision (verified by hash):

| Field | Value |
|-------|-------|
| Binary SHA-256 | `15c6fe4d54defc4d375524452f433ff3f4e7a10e3b23f89c14096cd5484c1f4b` |
| Repository | https://github.com/prusa3d/libbgcode |
| Version | libbgcode 0.2.0 |
| Commit | [`5041c093b33e2748e76d6b326f2251310823f3df`](https://github.com/prusa3d/libbgcode/tree/5041c093b33e2748e76d6b326f2251310823f3df) (branch `main`, 2025-02-20) |
| Local modifications | none (clean upstream checkout) |

**Build environment** used to produce the shipped binary:

| Field | Value |
|-------|-------|
| Target | ELF 64-bit x86-64, dynamically linked, GNU/Linux |
| Toolchain | GNU g++ 11.4.0 |
| Build system | CMake 3.22.1 |
| Configure/build | CMake preset `default` → `CMAKE_BUILD_TYPE=Release`, deps preset `default` |

Reproduce from a clean checkout:

```bash
git clone https://github.com/prusa3d/libbgcode
cd libbgcode
git checkout 5041c093b33e2748e76d6b326f2251310823f3df
cmake --preset default        # configures deps + project (Release)
cmake --build --preset default
# resulting tool: build-default/src/LibBGCode/cmd/bgcode
```

**Written Offer.** The Corresponding Source for the exact version above is publicly available
at the commit link. In addition, for at least three (3) years from the date of distribution,
the author will provide, on request, a copy of the complete Corresponding Source of this
binary. Contact: david.herrmann@kit.edu

The full AGPL-3.0 compliance statement is also recorded in [LICENSE](./LICENSE).

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
