"""Generate a minimal valid 16x16 ICO file.

Used as the default icon for every AICluster executable when the user
hasn't supplied a custom one. Producing the icon programmatically
keeps the build system self-contained — there are no binary blobs
checked into the repository.
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

WIDTH = 16
HEIGHT = 16
PIXELS = WIDTH * HEIGHT


def _build_bitmap_data(pixels: bytes) -> bytes:
    """BMP-style image: 16x16 BGRA, with AND mask appended."""
    # BITMAPINFOHEADER (40 bytes) + 16*16*4 BGRA + 16*16 bits (AND mask)
    header = struct.pack(
        "<IiiHHIIiiII",
        40,            # biSize
        WIDTH,         # biWidth
        HEIGHT * 2,    # biHeight (doubled to include AND mask)
        1,             # biPlanes
        32,            # biBitCount
        0,             # biCompression
        0,             # biSizeImage
        0,             # biXPelsPerMeter
        0,             # biYPelsPerMeter
        0,             # biClrUsed
        0,             # biClrImportant
    )
    # BMP rows are bottom-up. We use a flat AICluster-blue tile.
    row = b"\x33\x66\xcc\xff" * WIDTH  # BGRA
    image = b"".join(row for _ in range(HEIGHT))
    and_mask = b"\x00" * ((WIDTH // 8) * HEIGHT)  # all opaque
    return header + image + and_mask


def make_icon() -> bytes:
    """Return a single-image ICO blob."""
    bmp = _build_bitmap_data(b"")
    # ICONDIR (6) + ICONDIRENTRY (16) + image
    icondir = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack(
        "<BBBBHHII",
        WIDTH, HEIGHT, 0, 0, 1, 32, len(bmp), 6 + 16,
    )
    return icondir + entry + bmp


def main() -> int:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("assets/icons/default.ico")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(make_icon())
    print(f"wrote {out} ({out.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
