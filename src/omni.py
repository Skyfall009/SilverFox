# SPDX-License-Identifier: MPL-2.0
"""Read Firefox's optimized JAR archives, which store the ZIP directory first."""
import io
import struct
from zipfile import ZipFile


def read_omni(path):
    data = path.read_bytes()
    end_offset = data.rindex(b"PK\x05\x06")
    directory_size, directory_offset = struct.unpack_from("<II", data, end_offset + 12)
    if directory_offset + directory_size == end_offset:
        return ZipFile(io.BytesIO(data))

    # Copy the directory to the end for the ZIP reader. The file entries
    # remain at their original offsets, so their directory records stay valid.
    directory = data[directory_offset:directory_offset + directory_size]
    end_record = bytearray(data[end_offset:])
    struct.pack_into("<I", end_record, 16, end_offset)
    return ZipFile(io.BytesIO(data[:end_offset] + directory + end_record))
