# GCode Translator

A powerful Python-based tool for reading, interpreting, and converting standard and binary G-code (`.bgcode`) files.  
It integrates a native C++ binary (`bgcode`) and uses web scraping to retrieve command documentation from Marlin firmware resources.

---

## 🚀 Features

- ✅ Translate raw G-code lines into human-readable explanations
- ✅ Supports `.gcode`, `.bgcode`, and `.gx` formats
- ✅ Integrates with native C++ converter (`bgcode`) for decoding binary formats
- ✅ Automatically scrapes G/M-code documentation from Marlin's official site
- ✅ Supports embedded thumbnails (base64 or binary)
- ✅ CLI access via `gcode-translator` command

---

## 🧪 Installation

### 🛠 For local development:

```bash
git clone https://github.com/YOURNAME/gcode-translator.git
cd gcode-translator
pip install -e .
```

### 📦 Install directly via pip:

```bash
pip install git+https://github.com/YOURNAME/gcode-translator.git
```

---

## 🖥️ CLI Usage

After installation, use the command:

```bash
gcode-translator path/to/your/file.gcode
```

> It processes the G-code file and outputs interpreted descriptions line by line.

---

## 📦 Dependencies

This project uses the following packages:

- [`selenium`](https://pypi.org/project/selenium/)
- [`beautifulsoup4`](https://pypi.org/project/beautifulsoup4/)

The `bgcode` Linux binary is included in the package and used automatically.
`bgcode` was built from the official source code from 
[Prusa3d](https://github.com/prusa3d/libbgcode) using the [AGPL-3.0 license](https://www.gnu.org/licenses/agpl-3.0.html.en).
It is used as a subprocess, and it use agrees with the [GPL FAQ](https://www.gnu.org/licenses/gpl-faq.en.html#MereAggregation).
If there are complaints, I declare hereby, that I will remove the binary ASAP.

---

## 🧠 Python API Usage

You can also use it programmatically:

```python
from gcode_translator.GCode_Translator import main

main("your_file.gcode")
```

---

## 📁 Project Structure

```
gcode_translator/
├── GCode_Translator.py          # CLI and translation logic
├── Binary_GCode_Translator.py   # Binary decoding using native binary
├── GCode_Mapping.py             # G/M code mapping using web scraping
├── helper.py                    # Parser and helper functions
├── bgcode                       # Embedded C++ executable
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
