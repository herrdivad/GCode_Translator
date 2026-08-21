"""Companion package shipping the Linux ``bgcode`` binary for gcode-translator.

The binary is the unmodified libbgcode CLI (AGPL-3.0). This package only exposes
its on-disk location; the actual invocation lives in the main gcode-translator
package. Keeping the AGPL binary in a separate, opt-in package lets the main
package be installed binary-free.
"""

import importlib.resources


def binary_path() -> str:
    """Return the absolute path to the bundled Linux ``bgcode`` binary."""
    with importlib.resources.path(__package__, "bgcode") as p:
        return str(p)
