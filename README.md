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
