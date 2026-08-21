# gcode-translator-bgcode-windows

Companion package that ships the **Windows** `bgcode.exe` used by
[`gcode-translator`](../../) to convert Prusa `.bgcode` files to plain `.gcode`.

The binary is built from the **unmodified** libbgcode CLI source (v0.2.0, commit
`5041c093b33e2748e76d6b326f2251310823f3df`) and is licensed under **AGPL-3.0**
(see `LICENSE.AGPL-3.0.txt`). Only the *dependency build scripts* were patched — the
libbgcode source code itself is untouched (details under
[Build-script modifications](#build-script-modifications)). It is kept in a separate,
opt-in package so the main `gcode-translator` package (MIT) can be installed
binary-free.

The produced executable is fully self-contained: it links the **static** MSVC runtime
(`/MT`), so it depends only on `KERNEL32.dll` and needs **no** Visual C++ Redistributable
on the target machine.

## Installation

This package is not published to PyPI. It is pulled in automatically via the
`gcode-translator` extras (git install):

```bash
pip install "gcode-translator[windows] @ git+https://github.com/herrdivad/GCode_Translator.git"
```

To install just this companion directly:

```bash
pip install "git+https://github.com/herrdivad/GCode_Translator.git#subdirectory=companion/bgcode-windows"
```

## Layout

```
companion/bgcode-windows/
├── pyproject.toml
├── LICENSE.AGPL-3.0.txt
└── gcode_translator_bgcode_windows/
    ├── __init__.py                                    # exposes binary_path()
    ├── bgcode.exe                                     # the PE32+ x86-64 Windows binary
    ├── CORRESPONDING_SOURCE.md                        # AGPL-3.0 §6 record (shipped in the wheel)
    └── 0001-deps-static-crt-and-policy-floor.patch    # build-script patch (part of Corresponding Source)
```

The Corresponding Source files live **inside** the package directory so they are bundled
into the built wheel, not only present in the git checkout.

The main package locates the binary at runtime by importing
`gcode_translator_bgcode_windows` and calling `binary_path()`.

## Corresponding Source (AGPL-3.0 §6)

This package distributes the AGPL-3.0 binary, so its full Corresponding Source record —
binary hash, upstream commit, build environment, the build-script patch, reproduce steps
and the written offer — is shipped **inside the package** (and therefore inside the wheel)
at [`gcode_translator_bgcode_windows/CORRESPONDING_SOURCE.md`](./gcode_translator_bgcode_windows/CORRESPONDING_SOURCE.md),
next to the patch it references.

At a glance:

| Field | Value |
|-------|-------|
| Binary SHA-256 | `49dfc4b5b698a455d4eaa56a91d745ba5ac0aad641643077286b945a6ae43927` |
| Version / commit | libbgcode 0.2.0 — [`5041c093…`](https://github.com/prusa3d/libbgcode/tree/5041c093b33e2748e76d6b326f2251310823f3df) |
| Source code modifications | none (clean upstream checkout) |
| Build-script modifications | `0001-deps-static-crt-and-policy-floor.patch` (dependency build config only) |
| MSVC runtime | static (`/MT`) — depends only on `KERNEL32.dll` |
