import importlib.resources
import os
import stat
import subprocess
import sys


def extract_binary_picture_from_gx(input_path: str, output_path: str, skip=58, count=14454):
    with open(input_path, "rb") as infile:
        infile.seek(skip)  # Skip the first `skip` Bytes
        data = infile.read(count)  # Read `count` Bytes from position `skip`

    with open(output_path, "wb") as outfile:
        outfile.write(data)  # as bmp picture


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
    if not sys.platform.startswith("linux"):
        print("This script only works on Linux!")
        return None

    if not bgcode_binEXEC_path:
        bgcode_binEXEC_path = get_bgcode_executable_path()

    print(f"Using bgcode binary: {bgcode_binEXEC_path}")
    print(f"Input file: {bgcode}")

    # Make it executable
    st = os.stat(bgcode_binEXEC_path)
    os.chmod(bgcode_binEXEC_path, st.st_mode | 0o111)

    subprocess.run([bgcode_binEXEC_path, bgcode])

    file_path_gcode = bgcode[:-7] + ".gcode"
    print(f"Output file: {file_path_gcode}")

    return file_path_gcode


def make_executable(path):
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)


if __name__ == "__main__":
    # print(binary_gcode_to_gcode("./AbstandshalterZinsserWaage_0.4n_0.2mm_PLA_MINIIS_1h10m(1).bgcode"))
    extract_binary_picture_from_gx("modern_Flashforge_Ninetales_binaryPreview.gx", "binaryPreview.bmp")
