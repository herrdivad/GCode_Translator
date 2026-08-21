# gcode-translator-bgcode-linux

Companion package that ships the **Linux** `bgcode` binary used by
[`gcode-translator`](../../) to convert Prusa `.bgcode` files to plain `.gcode`.

The binary is the **unmodified** libbgcode CLI and is licensed under **AGPL-3.0**
(see `LICENSE.AGPL-3.0.txt`). It is kept in a separate, opt-in package so the
main `gcode-translator` package (MIT) can be installed binary-free.

## Installation

This package is not published to PyPI. It is pulled in automatically via the
`gcode-translator` extras (git install):

```bash
pip install "gcode-translator[linux] @ git+https://github.com/herrdivad/GCode_Translator.git"
```

To install just this companion directly:

```bash
pip install "git+https://github.com/herrdivad/GCode_Translator.git#subdirectory=companion/bgcode-linux"
```

## Layout

```
companion/bgcode-linux/
├── pyproject.toml
├── LICENSE.AGPL-3.0.txt
└── gcode_translator_bgcode_linux/
    ├── __init__.py                  # exposes binary_path()
    ├── bgcode                       # the ELF x86-64 Linux binary
    └── CORRESPONDING_SOURCE.md      # AGPL-3.0 §6 record (shipped in the wheel)
```

The main package locates the binary at runtime by importing
`gcode_translator_bgcode_linux` and calling `binary_path()`.

## Corresponding Source (AGPL-3.0 §6)

This package distributes the AGPL-3.0 binary, so its full Corresponding Source record —
binary hash, upstream commit, build environment, reproduce steps and the written offer —
is shipped **inside the package** (and therefore inside the wheel) at
[`gcode_translator_bgcode_linux/CORRESPONDING_SOURCE.md`](./gcode_translator_bgcode_linux/CORRESPONDING_SOURCE.md).

At a glance:

| Field | Value |
|-------|-------|
| Binary SHA-256 | `15c6fe4d54defc4d375524452f433ff3f4e7a10e3b23f89c14096cd5484c1f4b` |
| Version / commit | libbgcode 0.2.0 — [`5041c093…`](https://github.com/prusa3d/libbgcode/tree/5041c093b33e2748e76d6b326f2251310823f3df) |
| Source code modifications | none (clean upstream checkout) |
| Build-script modifications | none |
| Target | ELF 64-bit x86-64, dynamically linked, GNU/Linux |
