"""Companion package shipping the Windows ``bgcode`` binary for gcode-translator.

The binary is built from the unmodified libbgcode CLI (AGPL-3.0); only the
dependency build scripts were patched (static MSVC runtime + CMake policy floor,
see the package README and ``patches/``). This package only exposes the binary's
on-disk location; the actual invocation lives in the main gcode-translator
package. Keeping the AGPL binary in a separate, opt-in package lets the main
package be installed binary-free.
"""

import importlib.resources


def binary_path() -> str:
    """Return the absolute path to the bundled Windows ``bgcode.exe``."""
    with importlib.resources.path(__package__, "bgcode.exe") as p:
        return str(p)
