#!/usr/bin/env python3
"""
Build NaroEditor.ico from naroeditor_ico.png.

Sizes generated:
  256, 128, 64, 48, 32 — LANCZOS downscale from source
  16                   — hand-crafted pixel art
"""
import os, struct
from io import BytesIO
from PIL import Image

DIR = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(DIR, "naroeditor_ico.png")
DST = os.path.join(DIR, "NaroEditor.ico")

# ── Palette (sampled from source) ──────────────────────────────────────────
TRANS  = (  0,   0,   0,   0)
BG     = ( 37,  40,  55, 255)   # dark background
TEAL   = ( 72, 216, 192, 255)   # teal border
PAPER  = (234, 235, 242, 255)   # white paper/scroll
PEN_D  = ( 46,  84, 150, 255)   # pen shadow/dark side
PEN_M  = ( 70, 110, 172, 255)   # pen main body
PEN_H  = (200, 218, 240, 255)   # pen highlight stripe


# ── 16×16 hand-crafted pixel art ───────────────────────────────────────────
def make_16() -> Image.Image:
    img = Image.new("RGBA", (16, 16), TRANS)
    px = img.load()

    def dot(r: int, c: int, col: tuple) -> None:
        if 0 <= r < 16 and 0 <= c < 16:
            px[c, r] = col          # PIL pixel access: [x=col, y=row]

    # 1. Dark background fill
    for r in range(16):
        for c in range(16):
            dot(r, c, BG)

    # 2. Teal border ring (1 px, corners clipped to transparent)
    for c in range(1, 15):
        dot(0,  c, TEAL)
        dot(15, c, TEAL)
    for r in range(1, 15):
        dot(r,  0, TEAL)
        dot(r, 15, TEAL)
    for r, c in [(0, 0), (0, 15), (15, 0), (15, 15)]:
        dot(r, c, TRANS)

    # 3. White paper/scroll (simplified wave shape)
    paper: dict[int, range] = {
        5:  range(5, 10),
        6:  range(4, 11),
        7:  range(3, 11),
        8:  range(2, 11),
        9:  range(2, 11),
        10: range(2, 10),
        11: range(3,  9),
    }
    for row, cols in paper.items():
        for col in cols:
            dot(row, col, PAPER)

    # 4. Pen diagonal (top-right → bottom-left, 3 px wide)
    #    Center col: c = 11 − (r − 2) × 0.7  (linear from col 11 at r=2 to col 4 at r=12)
    for r in range(2, 13):
        c = round(11 - (r - 2) * 0.7)
        dot(r, c - 1, PEN_D)   # shadow / left side
        dot(r, c,     PEN_M)   # main body
        dot(r, c + 1, PEN_H)   # highlight / right side

    # 5. Nib tip (2 extra rows, narrowing to 1 px)
    dot(12, 3, PEN_D)
    dot(13, 3, PEN_D)

    return img


# ── ICO file writer (PNG-compressed entries) ───────────────────────────────
def save_ico(images: list[Image.Image], path: str) -> None:
    """Write a Windows ICO file using PNG-compressed image data."""
    buffers: list[bytes] = []
    for img in images:
        buf = BytesIO()
        img.save(buf, format="PNG")
        buffers.append(buf.getvalue())

    n = len(images)
    header = struct.pack("<HHH", 0, 1, n)           # reserved, type=1 (ICO), count

    offset = 6 + n * 16                             # header + n × ICONDIRENTRY
    entries = b""
    for img, data in zip(images, buffers):
        w = img.width  if img.width  < 256 else 0   # 0 encodes 256 in ICO spec
        h = img.height if img.height < 256 else 0
        entries += struct.pack(
            "<BBBBHHII",
            w, h,           # image dimensions
            0,              # color count (0 for >8 bpp)
            0,              # reserved
            1,              # color planes
            32,             # bits per pixel (RGBA)
            len(data),      # byte size of image data
            offset,         # byte offset of image data from file start
        )
        offset += len(data)

    with open(path, "wb") as f:
        f.write(header + entries)
        for data in buffers:
            f.write(data)


# ── Main ───────────────────────────────────────────────────────────────────
def main() -> None:
    src = Image.open(SRC).convert("RGBA")
    print(f"Source: {SRC}  ({src.width}×{src.height})")

    images: list[Image.Image] = []

    for s in (256, 128, 64, 48, 32):
        images.append(src.resize((s, s), Image.LANCZOS))
        print(f"  {s:>3}x{s:<3} LANCZOS")

    save_ico(images, DST)
    print(f"\nSaved: {DST}")
    print(f"  {len(images)} sizes: " + ", ".join(f"{i.width}x{i.height}" for i in images))


if __name__ == "__main__":
    main()
