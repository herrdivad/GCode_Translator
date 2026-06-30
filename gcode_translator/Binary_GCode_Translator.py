import importlib.resources
import logging
import os
import stat
import subprocess
import sys

logger = logging.getLogger(__name__)


# Size of the BMP file header (14 B) + minimal DIB header offset; the BMP "BM"
# signature in a binary Flashforge ".gx" sits a few dozen bytes in (after the
# "xgcode 1.0" magic), but the exact offset and image size vary per slicer/printer,
# so they are read from the BMP header instead of hard-coded.
_HEADER_SCAN_BYTES = 4096


def _locate_embedded_bmp(header: bytes) -> tuple[int, int] | None:
    """Locate an embedded BMP inside ``header`` and return ``(offset, size)``.

    Validates the BMP file header (``BM`` signature, zero reserved field, a pixel
    data offset that lies within the declared file size) so that a stray ``BM`` in
    the payload is not mistaken for the thumbnail. Returns ``None`` if no plausible
    BMP is present (e.g. a ``.gx`` file that is really plain-text G-code).
    """
    search_from = 0
    while True:
        pos = header.find(b"BM", search_from)
        if pos == -1 or pos + 14 > len(header):
            return None
        size = int.from_bytes(header[pos + 2:pos + 6], "little")          # total BMP size
        reserved = int.from_bytes(header[pos + 6:pos + 10], "little")     # must be 0
        pix_offset = int.from_bytes(header[pos + 10:pos + 14], "little")  # start of pixel data
        if reserved == 0 and 54 <= pix_offset < size:
            return pos, size
        search_from = pos + 1


def extract_binary_picture_from_gx(input_path: str, output_path: str | None = None,
                                   skip: int | None = None, count: int | None = None) -> bytes | None:
    """Extract the embedded BMP thumbnail from a Flashforge ``.gx`` file.

    By default the BMP's offset and length are derived from its own header, so the
    function works regardless of thumbnail resolution and returns ``None`` for ``.gx``
    files that carry no embedded image. Passing ``skip``/``count`` forces the legacy
    fixed-offset behavior (escape hatch for non-standard files).

    Writes the image to ``output_path`` only when one is given; the raw bytes are
    returned either way so callers can use the picture in memory without a file.
    """
    if skip is not None or count is not None:
        # Explicit override: read a fixed byte range (old behavior).
        skip = 58 if skip is None else skip
        count = 14454 if count is None else count
        with open(input_path, "rb") as infile:
            infile.seek(skip)
            data = infile.read(count)
    else:
        with open(input_path, "rb") as infile:
            header = infile.read(_HEADER_SCAN_BYTES)
            location = _locate_embedded_bmp(header)
            if location is None:
                logger.warning("⚠️ No embedded BMP thumbnail found in '%s'.", input_path)
                return None
            offset, size = location
            infile.seek(offset)
            data = infile.read(size)
        if len(data) < size:
            logger.warning("⚠️ Truncated BMP in '%s' (expected %d B, got %d B).",
                           input_path, size, len(data))

    if output_path and data:
        with open(output_path, "wb") as outfile:
            outfile.write(data)  # as bmp picture

    return data


def extract_picture_bytes_from_content(
        in_data: bytes,
        as_file: bool = True,
        output_path: str = "out.bmp",
        skip: int = 58,
        count: int = 14454
) -> tuple[bytes, bytes]:
    """
    Extracts a chunk of bytes from a binary block, optionally writes it to a file.
    Returns the extracted picture data and the remaining data after that block.
    """
    picture_data = in_data[skip:skip + count]

    if as_file:
        with open(output_path, "wb") as outfile:
            outfile.write(picture_data)

    remaining_data = in_data[skip + count:]
    return picture_data, remaining_data


def get_bgcode_executable_path():
    with importlib.resources.path('gcode_translator', 'bgcode') as bgcode_path:
        return str(bgcode_path)


def binary_gcode_to_gcode(bgcode, bgcode_binEXEC_path=None):
    """Convert a Prusa ``.bgcode`` file to ``.gcode`` via the bundled native binary.

    Returns the path to the produced ``.gcode`` file, or ``None`` if the platform is
    unsupported, the conversion fails, or the expected output file is not created.
    """
    if not sys.platform.startswith("linux"):
        logger.error("This script only works on Linux!")
        return None

    if not bgcode_binEXEC_path:
        bgcode_binEXEC_path = get_bgcode_executable_path()

    logger.info("Using bgcode binary: %s", bgcode_binEXEC_path)
    logger.info("Input file: %s", bgcode)

    make_executable(bgcode_binEXEC_path)

    try:
        subprocess.run([bgcode_binEXEC_path, bgcode], check=True)
    except (subprocess.CalledProcessError, OSError) as e:
        logger.error("❌ bgcode conversion failed: %s", e)
        return None

    file_path_gcode = bgcode[:-7] + ".gcode"
    if not os.path.isfile(file_path_gcode):
        logger.error("❌ bgcode reported success but the output file is missing: %s", file_path_gcode)
        return None

    logger.info("Output file: %s", file_path_gcode)
    return file_path_gcode


def make_executable(path):
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)


if __name__ == "__main__":
    # print(binary_gcode_to_gcode("./AbstandshalterZinsserWaage_0.4n_0.2mm_PLA_MINIIS_1h10m(1).bgcode"))
    extract_binary_picture_from_gx("modern_Flashforge_Ninetales_binaryPreview.gx", "binaryPreview.bmp")
