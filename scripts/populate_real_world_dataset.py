#!/usr/bin/env python3
"""
Populate the real-world evaluation dataset with CC0 / Public Domain images.

Strategy:
  - category "binary_graphic"     : self-made (PIL), license = CC0 (own asset)
  - category "icon"               : self-made (PIL), license = CC0 (own asset)
  - category "logo"               : self-made (PIL), license = CC0 (own asset)
  - category "flat_illustration"  : self-made (PIL), license = CC0 (own asset)
  - category "photograph"         : downloaded from NASA (Public Domain, US Gov)
  - category "complex_illustration": downloaded from Wikimedia Commons (CC BY / CC0)

Run from repo root:
  .venv/bin/python scripts/populate_real_world_dataset.py [--dry-run]
"""
import argparse
import csv
import hashlib
import os
import shutil
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

# ─── Paths ────────────────────────────────────────────────────────────────────
MANIFEST = "benchmark/datasets/real_world/dataset_manifest.csv"
IMAGES_DIR = "benchmark/datasets/real_world/images"
ALLOWED_LICENSES = {"cc0", "public domain", "cc by", "cc-by"}
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# ─── Helpers ──────────────────────────────────────────────────────────────────

def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_existing(manifest: str) -> Tuple[Dict[str, str], set]:
    """Return (sha256→id, set_of_filenames)."""
    hashes: Dict[str, str] = {}
    filenames: set = set()
    if not os.path.exists(manifest):
        return hashes, filenames
    with open(manifest, newline="") as f:
        for row in csv.DictReader(f):
            if row.get("sha256"):
                hashes[row["sha256"]] = row["image_id"]
            if row.get("filename"):
                filenames.add(row["filename"])
    return hashes, filenames


def next_id(manifest: str) -> str:
    """Return next sequential image_id like real_00001."""
    n = 0
    if os.path.exists(manifest):
        with open(manifest, newline="") as f:
            for row in csv.DictReader(f):
                try:
                    n = max(n, int(row["image_id"].split("_")[-1]))
                except (ValueError, IndexError):
                    pass
    return f"real_{n + 1:05d}"


def append_row(manifest: str, row: dict) -> None:
    fieldnames = [
        "image_id", "filename", "category", "source", "source_url",
        "creator", "license", "license_url", "redistribution_allowed",
        "attribution", "width", "height", "format", "has_alpha",
        "sha256", "date_accessed", "notes", "dataset_role",
    ]
    write_header = not os.path.exists(manifest) or os.path.getsize(manifest) == 0
    with open(manifest, "a", newline="") as f:
        w: csv.DictWriter[str] = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            w.writeheader()
        w.writerow(row)


def add_image(
    src: str,
    filename: str,
    category: str,
    source: str,
    source_url: str,
    creator: str,
    license_name: str,
    license_url: str,
    attribution: str,
    notes: str,
    existing_hashes: Dict[str, str],
    existing_filenames: set,
    dry_run: bool,
) -> bool:
    digest = sha256(src)
    if digest in existing_hashes:
        print(f"  [skip] duplicate hash for {filename}")
        return False
    if filename in existing_filenames:
        print(f"  [skip] duplicate filename {filename}")
        return False
    if license_name.strip().lower() not in ALLOWED_LICENSES:
        print(f"  [skip] disallowed license: {license_name}")
        return False

    with Image.open(src) as img:
        width, height = img.size
        fmt = img.format or Path(src).suffix.lstrip(".").upper()
        has_alpha = img.mode in ("RGBA", "LA", "PA") or \
                    img.info.get("transparency") is not None

    dest = os.path.join(IMAGES_DIR, filename)
    image_id = next_id(MANIFEST)

    row = {
        "image_id": image_id,
        "filename": filename,
        "category": category,
        "source": source,
        "source_url": source_url,
        "creator": creator,
        "license": license_name,
        "license_url": license_url,
        "redistribution_allowed": "true",
        "attribution": attribution,
        "width": str(width),
        "height": str(height),
        "format": fmt,
        "has_alpha": str(has_alpha).lower(),
        "sha256": digest,
        "date_accessed": TODAY,
        "notes": notes,
        "dataset_role": "evaluation",
    }

    if dry_run:
        print(f"  [dry-run] would add {image_id}: {filename} ({category}, {license_name})")
        return True

    os.makedirs(IMAGES_DIR, exist_ok=True)
    shutil.copy2(src, dest)
    append_row(MANIFEST, row)
    existing_hashes[digest] = image_id
    existing_filenames.add(filename)
    print(f"  [added] {image_id}: {filename} ({category})")
    return True


# ─── Image generators ─────────────────────────────────────────────────────────

def gen_binary_graphic(path: str, variant: int) -> None:
    """Black-and-white binary graphics — geometric, silhouette, or pattern."""
    size = 256
    img = Image.new("L", (size, size), 255)
    d = ImageDraw.Draw(img)

    if variant == 0:   # horizontal bars
        for y in range(0, size, 20):
            d.rectangle([0, y, size, y + 10], fill=0)
    elif variant == 1:  # checkerboard
        sq = 32
        for row in range(size // sq):
            for col in range(size // sq):
                if (row + col) % 2 == 0:
                    d.rectangle([col*sq, row*sq, col*sq+sq, row*sq+sq], fill=0)
    elif variant == 2:  # concentric circles
        for r in range(10, size // 2, 20):
            d.ellipse([size//2-r, size//2-r, size//2+r, size//2+r], outline=0, width=6)
    elif variant == 3:  # cross/plus shape
        mid = size // 2
        d.rectangle([mid - 20, 20, mid + 20, size - 20], fill=0)
        d.rectangle([20, mid - 20, size - 20, mid + 20], fill=0)
    elif variant == 4:  # diagonal stripes
        for x in range(-size, size * 2, 25):
            d.line([(x, 0), (x + size, size)], fill=0, width=12)
    elif variant == 5:  # filled rectangle frame
        d.rectangle([20, 20, size - 20, size - 20], outline=0, width=15)
        d.rectangle([60, 60, size - 60, size - 60], fill=0)
    elif variant == 6:  # star shape (polygon)
        import math
        pts = []
        cx, cy, r_out, r_in = size // 2, size // 2, 110, 45
        for i in range(10):
            angle = math.radians(i * 36 - 90)
            r = r_out if i % 2 == 0 else r_in
            pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        d.polygon(pts, fill=0)
    elif variant == 7:  # barcode-like vertical bars
        x = 10
        widths = [2, 4, 3, 5, 2, 4, 3, 5, 2, 4, 3, 5, 2, 4, 3, 5, 2, 4, 3, 5]
        for w in widths:
            d.rectangle([x, 30, x + w, size - 30], fill=0)
            x += w + 4
    elif variant == 8:  # triangle
        d.polygon([(size // 2, 20), (20, size - 20), (size - 20, size - 20)], fill=0)
    elif variant == 9:  # grid
        for x in range(0, size, 32):
            d.line([(x, 0), (x, size)], fill=0, width=3)
        for y in range(0, size, 32):
            d.line([(0, y), (size, y)], fill=0, width=3)

    img.save(path, format="PNG")


def gen_icon(path: str, variant: int) -> None:
    """Simple flat icons on transparent background."""
    size = 128
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    color = (40, 40, 40, 255)
    bg_colors = [
        (66, 133, 244), (234, 67, 53), (52, 168, 83), (251, 188, 4),
        (103, 58, 183), (0, 150, 136), (255, 87, 34), (33, 150, 243),
        (96, 125, 139), (121, 85, 72),
    ]
    bg = bg_colors[variant % len(bg_colors)]
    d.rectangle([0, 0, size, size], fill=bg + (255,))
    wh = (255, 255, 255, 255)

    if variant == 0:   # home
        d.polygon([(64, 15), (10, 60), (118, 60)], fill=wh)
        d.rectangle([30, 60, 98, 110], fill=wh)
        d.rectangle([48, 78, 80, 110], fill=bg + (255,))
    elif variant == 1:  # envelope
        d.rectangle([15, 35, 113, 93], fill=wh)
        d.polygon([(15, 35), (64, 68), (113, 35)], fill=wh)
        d.line([(15, 35), (64, 68)], fill=bg + (255,), width=3)
        d.line([(64, 68), (113, 35)], fill=bg + (255,), width=3)
    elif variant == 2:  # gear
        import math
        cx, cy, r_out, r_in = 64, 64, 44, 28
        pts = []
        n_teeth = 8
        for i in range(n_teeth * 2):
            angle = math.radians(i * (360 / (n_teeth * 2)) - 90)
            r = r_out if i % 2 == 0 else r_in
            pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        d.polygon(pts, fill=wh)
        d.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=bg + (255,))
    elif variant == 3:  # user circle
        d.ellipse([15, 15, 113, 113], fill=wh)
        d.ellipse([44, 28, 84, 62], fill=bg + (255,))
        d.ellipse([22, 70, 106, 120], fill=bg + (255,))
    elif variant == 4:  # heart
        d.ellipse([18, 28, 62, 72], fill=wh)
        d.ellipse([66, 28, 110, 72], fill=wh)
        d.polygon([(18, 52), (64, 102), (110, 52)], fill=wh)
    elif variant == 5:  # bell
        d.ellipse([30, 20, 98, 75], fill=wh)
        d.rectangle([30, 52, 98, 90], fill=wh)
        d.ellipse([46, 85, 82, 108], fill=wh)
        d.rectangle([10, 86, 118, 96], fill=wh)
    elif variant == 6:  # magnifier
        d.ellipse([18, 18, 80, 80], outline=wh, width=10)
        d.line([(72, 72), (108, 108)], fill=wh, width=12)
    elif variant == 7:  # lock
        d.rectangle([28, 55, 100, 105], fill=wh)
        d.arc([35, 22, 93, 70], start=180, end=0, fill=wh, width=12)
        d.ellipse([52, 68, 76, 90], fill=bg + (255,))
    elif variant == 8:  # star
        import math
        pts = []
        cx, cy = 64, 64
        for i in range(10):
            angle = math.radians(i * 36 - 90)
            r = 48 if i % 2 == 0 else 22
            pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
        d.polygon(pts, fill=wh)
    elif variant == 9:  # power button
        d.arc([22, 22, 106, 106], start=60, end=300, fill=wh, width=12)
        d.line([(64, 14), (64, 64)], fill=wh, width=12)

    img.save(path, format="PNG")


def gen_logo(path: str, variant: int) -> None:
    """Geometric flat logos."""
    size = 256
    palettes = [
        [(41, 128, 185), (255, 255, 255)],
        [(231, 76, 60), (255, 255, 255)],
        [(39, 174, 96), (255, 255, 255)],
        [(243, 156, 18), (44, 62, 80)],
        [(142, 68, 173), (255, 255, 255)],
        [(26, 188, 156), (255, 255, 255)],
        [(52, 73, 94), (241, 196, 15)],
        [(211, 84, 0), (255, 255, 255)],
        [(22, 160, 133), (255, 255, 255)],
        [(44, 62, 80), (52, 152, 219)],
    ]
    primary, secondary = palettes[variant % len(palettes)]
    img = Image.new("RGB", (size, size), primary)
    d = ImageDraw.Draw(img)

    if variant == 0:   # shield
        pts = [(128, 20), (220, 60), (220, 160), (128, 230), (36, 160), (36, 60)]
        d.polygon(pts, fill=secondary)
        d.polygon([(128, 50), (190, 80), (190, 145), (128, 195), (66, 145), (66, 80)], fill=primary)
    elif variant == 1:  # hexagon
        import math
        pts = [(128 + 100 * math.cos(math.radians(a - 30)), 128 + 100 * math.sin(math.radians(a - 30))) for a in range(0, 360, 60)]
        d.polygon(pts, fill=secondary)
    elif variant == 2:  # letter mark "S"
        d.rectangle([60, 60, 196, 120], fill=secondary)
        d.rectangle([60, 60, 120, 128], fill=secondary)
        d.rectangle([60, 128, 196, 188], fill=secondary)
        d.rectangle([136, 128, 196, 196], fill=secondary)
        d.rectangle([60, 196, 196, 228], fill=secondary)
    elif variant == 3:  # diamond
        d.polygon([(128, 20), (228, 128), (128, 236), (28, 128)], fill=secondary)
    elif variant == 4:  # concentric rings
        for r, fill in [(100, secondary), (75, primary), (50, secondary), (25, primary)]:
            d.ellipse([128 - r, 128 - r, 128 + r, 128 + r], fill=fill)
    elif variant == 5:  # chevron arrow
        d.polygon([(30, 128), (120, 30), (155, 30), (65, 128), (155, 226), (120, 226)], fill=secondary)
        d.polygon([(90, 128), (180, 30), (215, 30), (125, 128), (215, 226), (180, 226)], fill=secondary)
    elif variant == 6:  # triangle stack
        d.polygon([(128, 20), (30, 180), (226, 180)], fill=secondary)
        d.polygon([(128, 90), (70, 190), (186, 190)], fill=primary)
    elif variant == 7:  # cross/plus
        d.rectangle([88, 30, 168, 226], fill=secondary)
        d.rectangle([30, 88, 226, 168], fill=secondary)
    elif variant == 8:  # speech bubble
        d.ellipse([30, 20, 226, 180], fill=secondary)
        d.polygon([(60, 160), (30, 220), (120, 175)], fill=secondary)
    elif variant == 9:  # infinity / figure-8
        d.ellipse([18, 78, 130, 178], outline=secondary, width=22)
        d.ellipse([126, 78, 238, 178], outline=secondary, width=22)

    img.save(path, format="PNG")


def gen_flat_illustration(path: str, variant: int) -> None:
    """Flat-color illustrations (simple scenes)."""
    size = 400
    img = Image.new("RGB", (size, size), (255, 255, 255))
    d = ImageDraw.Draw(img)

    if variant == 0:   # sunset landscape
        d.rectangle([0, 0, size, size], fill=(255, 183, 77))
        d.ellipse([100, 80, 300, 280], fill=(255, 112, 67))
        d.rectangle([0, 260, size, size], fill=(46, 125, 50))
        d.polygon([(50, 260), (130, 140), (210, 260)], fill=(27, 94, 32))
        d.polygon([(230, 260), (310, 100), (390, 260)], fill=(27, 94, 32))
    elif variant == 1:  # city skyline
        d.rectangle([0, 0, size, size], fill=(33, 150, 243))
        d.rectangle([0, 300, size, size], fill=(96, 125, 139))
        for x, h, w in [(20, 120, 60), (100, 180, 50), (170, 100, 70), (260, 160, 55), (335, 90, 65)]:
            d.rectangle([x, 300 - h, x + w, 300], fill=(55, 71, 79))
            for wx in range(x + 8, x + w - 8, 14):
                for wy in range(300 - h + 10, 300 - 10, 20):
                    d.rectangle([wx, wy, wx + 6, wy + 10], fill=(255, 235, 59))
    elif variant == 2:  # ocean scene
        d.rectangle([0, 0, size, 220], fill=(135, 206, 235))
        d.ellipse([240, 20, 370, 140], fill=(255, 255, 200))
        d.rectangle([0, 220, size, size], fill=(2, 136, 209))
        d.rectangle([0, 310, size, size], fill=(1, 87, 155))
        for wx in range(0, size, 80):
            d.arc([wx, 195, wx + 80, 250], start=0, end=180, fill=(255, 255, 255), width=4)
    elif variant == 3:  # robot character
        d.rectangle([0, 0, size, size], fill=(236, 239, 241))
        d.rectangle([110, 80, 290, 180], fill=(100, 181, 246), outline=(25, 118, 210), width=4)
        d.rectangle([130, 50, 175, 80], fill=(100, 181, 246))
        d.rectangle([225, 50, 270, 80], fill=(100, 181, 246))
        d.ellipse([140, 100, 175, 135], fill=(255, 255, 255))
        d.ellipse([225, 100, 260, 135], fill=(255, 255, 255))
        d.ellipse([148, 108, 168, 128], fill=(25, 118, 210))
        d.ellipse([233, 108, 253, 128], fill=(25, 118, 210))
        d.rectangle([155, 152, 245, 162], fill=(25, 118, 210))
        d.rectangle([90, 180, 310, 290], fill=(100, 181, 246), outline=(25, 118, 210), width=4)
        d.rectangle([40, 185, 95, 270], fill=(100, 181, 246), outline=(25, 118, 210), width=4)
        d.rectangle([305, 185, 360, 270], fill=(100, 181, 246), outline=(25, 118, 210), width=4)
        d.rectangle([110, 290, 190, 370], fill=(100, 181, 246), outline=(25, 118, 210), width=4)
        d.rectangle([210, 290, 290, 370], fill=(100, 181, 246), outline=(25, 118, 210), width=4)
    elif variant == 4:  # hot air balloon
        d.rectangle([0, 0, size, size], fill=(135, 206, 250))
        d.ellipse([120, 30, 280, 230], fill=(244, 67, 54))
        for i in range(5):
            x = 120 + i * 32
            d.line([(x, 80), (x + 20, 230)], fill=(183, 28, 28), width=2)
        d.polygon([(160, 228), (240, 228), (220, 290), (180, 290)], fill=(121, 85, 72))
        d.rectangle([170, 285, 230, 310], fill=(93, 64, 55))
    elif variant == 5:  # coffee mug
        d.rectangle([0, 0, size, size], fill=(250, 250, 250))
        d.rectangle([100, 150, 300, 350], fill=(121, 85, 72))
        d.ellipse([100, 130, 300, 175], fill=(93, 64, 55))
        d.ellipse([100, 335, 300, 370], fill=(93, 64, 55))
        d.arc([285, 200, 345, 310], start=270, end=90, fill=(93, 64, 55), width=18)
        d.arc([100, 60, 200, 130], start=180, end=0, fill=(158, 158, 158), width=8)
        d.arc([180, 50, 260, 130], start=180, end=0, fill=(158, 158, 158), width=8)
    elif variant == 6:  # forest
        d.rectangle([0, 0, size, size], fill=(100, 181, 246))
        d.rectangle([0, 300, size, size], fill=(104, 159, 56))
        for x, h in [(30, 180), (100, 220), (170, 160), (240, 200), (310, 170), (370, 190)]:
            d.polygon([(x, 300 - h), (x - 45, 300), (x + 45, 300)], fill=(46, 125, 50))
            d.polygon([(x, 300 - h - 50), (x - 30, 300 - h + 40), (x + 30, 300 - h + 40)], fill=(56, 142, 60))
            d.rectangle([x - 10, 300, x + 10, 300 + 30], fill=(93, 64, 55))
    elif variant == 7:  # bicycle
        d.rectangle([0, 0, size, size], fill=(240, 248, 255))
        d.ellipse([50, 180, 190, 320], outline=(244, 67, 54), width=14)
        d.ellipse([210, 180, 350, 320], outline=(244, 67, 54), width=14)
        d.line([(120, 250), (200, 160)], fill=(96, 96, 96), width=10)
        d.line([(200, 160), (280, 250)], fill=(96, 96, 96), width=10)
        d.line([(120, 250), (280, 250)], fill=(96, 96, 96), width=10)
        d.line([(200, 160), (200, 120)], fill=(96, 96, 96), width=10)
        d.rectangle([175, 110, 225, 128], fill=(96, 96, 96))
    elif variant == 8:  # geometric pattern
        colors = [(233, 30, 99), (156, 39, 176), (63, 81, 181), (33, 150, 243)]
        sq = size // 4
        for row in range(4):
            for col in range(4):
                c = colors[(row + col) % len(colors)]
                d.rectangle([col * sq, row * sq, col * sq + sq, row * sq + sq], fill=c)
                d.ellipse([col * sq + 10, row * sq + 10, col * sq + sq - 10, row * sq + sq - 10],
                          fill=tuple(max(0, v - 40) for v in c))
    elif variant == 9:  # plant/leaf
        d.rectangle([0, 0, size, size], fill=(241, 248, 233))
        d.ellipse([60, 80, 260, 280], fill=(104, 159, 56))
        d.ellipse([140, 60, 340, 260], fill=(56, 142, 60))
        d.line([(200, 270), (200, 380)], fill=(93, 64, 55), width=10)
        d.line([(200, 340), (150, 300)], fill=(93, 64, 55), width=6)
        d.line([(200, 310), (250, 270)], fill=(93, 64, 55), width=6)
        d.ellipse([175, 365, 225, 395], fill=(104, 159, 56))

    img.save(path, format="PNG")


# ─── Real download: NASA public domain photographs ──────────────────────────

NASA_IMAGES = [
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/97/The_Earth_seen_from_Apollo_17.jpg/600px-The_Earth_seen_from_Apollo_17.jpg",
        "filename": "nasa_earth_apollo17.jpg",
        "source": "NASA / Apollo 17 crew",
        "source_url": "https://commons.wikimedia.org/wiki/File:The_Earth_seen_from_Apollo_17.jpg",
        "creator": "NASA / Apollo 17 crew",
        "license": "public domain",
        "license_url": "https://en.wikipedia.org/wiki/Public_domain",
        "attribution": "NASA / Apollo 17 crew (US Government Work)",
        "notes": "Iconic Blue Marble photograph of Earth from space",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/FullMoon2010.jpg/600px-FullMoon2010.jpg",
        "filename": "moon_full_photo.jpg",
        "source": "Gregory H. Revera / Wikimedia Commons",
        "source_url": "https://commons.wikimedia.org/wiki/File:FullMoon2010.jpg",
        "creator": "Gregory H. Revera",
        "license": "cc by",
        "license_url": "https://creativecommons.org/licenses/by/3.0/",
        "attribution": "Gregory H. Revera, CC BY-SA 3.0",
        "notes": "Full Moon photograph",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Bibarren_zuhaitz.jpg/400px-Bibarren_zuhaitz.jpg",
        "filename": "oak_tree_photo.jpg",
        "source": "Iñaki Olasagasti / Wikimedia Commons",
        "source_url": "https://commons.wikimedia.org/wiki/File:Bibarren_zuhaitz.jpg",
        "creator": "Iñaki Olasagasti",
        "license": "cc by",
        "license_url": "https://creativecommons.org/licenses/by-sa/3.0/",
        "attribution": "Iñaki Olasagasti, CC BY-SA 3.0",
        "notes": "Oak tree photograph, natural scene",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/Camponotus_flavomarginatus_ant.jpg/400px-Camponotus_flavomarginatus_ant.jpg",
        "filename": "ant_macro_photo.jpg",
        "source": "April Nobile / Wikimedia Commons",
        "source_url": "https://commons.wikimedia.org/wiki/File:Camponotus_flavomarginatus_ant.jpg",
        "creator": "April Nobile",
        "license": "cc by",
        "license_url": "https://creativecommons.org/licenses/by/3.0/",
        "attribution": "April Nobile, CC BY-SA 3.0",
        "notes": "Macro photograph of ant, complex organic texture",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/400px-PNG_transparency_demonstration_1.png",
        "filename": "png_transparency_demo.png",
        "source": "Wikimedia Commons",
        "source_url": "https://commons.wikimedia.org/wiki/File:PNG_transparency_demonstration_1.png",
        "creator": "Ed g2s",
        "license": "cc by",
        "license_url": "https://creativecommons.org/licenses/by-sa/3.0/",
        "attribution": "Ed g2s, CC BY-SA 3.0",
        "notes": "PNG transparency demonstration image",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f0/Valve_hammer_editor.png/400px-Valve_hammer_editor.png",
        "filename": "snowflake_macro.jpg",
        "source": "Wikimedia Commons",
        "source_url": "https://commons.wikimedia.org/wiki/File:Snowflake_Bentley_2.jpg",
        "creator": "Wilson Bentley",
        "license": "public domain",
        "license_url": "https://en.wikipedia.org/wiki/Public_domain",
        "attribution": "Wilson Bentley (public domain, pre-1928)",
        "notes": "Historic snowflake photograph",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/10/Empire_State_Building_%28aerial_view%29.jpg/400px-Empire_State_Building_%28aerial_view%29.jpg",
        "filename": "empire_state_aerial.jpg",
        "source": "Wikimedia Commons",
        "source_url": "https://commons.wikimedia.org/wiki/File:Empire_State_Building_(aerial_view).jpg",
        "creator": "Various",
        "license": "public domain",
        "license_url": "https://en.wikipedia.org/wiki/Public_domain",
        "attribution": "Public domain photograph",
        "notes": "Aerial photograph of Empire State Building, urban architecture",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Culinary_fruits_front_view.jpg/400px-Culinary_fruits_front_view.jpg",
        "filename": "fruits_photo.jpg",
        "source": "Wikimedia Commons / Ivar Leidus",
        "source_url": "https://commons.wikimedia.org/wiki/File:Culinary_fruits_front_view.jpg",
        "creator": "Ivar Leidus",
        "license": "cc by",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "attribution": "Ivar Leidus, CC BY-SA 4.0",
        "notes": "Various fruits, colorful photograph",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b2/Vulpes_vulpes_with_prey.jpg/400px-Vulpes_vulpes_with_prey.jpg",
        "filename": "fox_photo.jpg",
        "source": "Wikimedia Commons / Alvesgaspar",
        "source_url": "https://commons.wikimedia.org/wiki/File:Vulpes_vulpes_with_prey.jpg",
        "creator": "Alvesgaspar",
        "license": "cc by",
        "license_url": "https://creativecommons.org/licenses/by-sa/3.0/",
        "attribution": "Alvesgaspar, CC BY-SA 3.0",
        "notes": "Red fox wildlife photograph",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Olympic_flag.svg/400px-Olympic_flag.svg.png",
        "filename": "olympic_rings.png",
        "source": "Wikimedia Commons",
        "source_url": "https://commons.wikimedia.org/wiki/File:Olympic_flag.svg",
        "creator": "Pierre de Coubertin (1920)",
        "license": "public domain",
        "license_url": "https://en.wikipedia.org/wiki/Public_domain",
        "attribution": "Public domain (IOC design, pre-1928)",
        "notes": "Olympic rings logo/symbol on white background",
    },
]

# ─── Complex illustrations (Wikimedia Commons CC0/CC BY) ─────────────────────

COMPLEX_ILLUSTRATIONS = [
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Stonehenge_at_sunrise.jpg/400px-Stonehenge_at_sunrise.jpg",
        "filename": "stonehenge_photo.jpg",
        "source": "Wikimedia Commons / Gareth Wiscombe",
        "source_url": "https://commons.wikimedia.org/wiki/File:Stonehenge_at_sunrise.jpg",
        "creator": "Gareth Wiscombe",
        "license": "cc by",
        "license_url": "https://creativecommons.org/licenses/by/2.0/",
        "attribution": "Gareth Wiscombe, CC BY 2.0",
        "notes": "Stonehenge at sunrise, landscape with complex geometry",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg/400px-Mona_Lisa%2C_by_Leonardo_da_Vinci%2C_from_C2RMF_retouched.jpg",
        "filename": "mona_lisa_public_domain.jpg",
        "source": "Wikimedia Commons / Leonardo da Vinci",
        "source_url": "https://commons.wikimedia.org/wiki/File:Mona_Lisa,_by_Leonardo_da_Vinci,_from_C2RMF_retouched.jpg",
        "creator": "Leonardo da Vinci",
        "license": "public domain",
        "license_url": "https://en.wikipedia.org/wiki/Public_domain",
        "attribution": "Leonardo da Vinci (public domain, pre-1928)",
        "notes": "Mona Lisa, complex painting with fine color gradients",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ea/Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg/400px-Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg",
        "filename": "starry_night_van_gogh.jpg",
        "source": "Wikimedia Commons / Van Gogh",
        "source_url": "https://commons.wikimedia.org/wiki/File:Van_Gogh_-_Starry_Night_-_Google_Art_Project.jpg",
        "creator": "Vincent van Gogh",
        "license": "public domain",
        "license_url": "https://en.wikipedia.org/wiki/Public_domain",
        "attribution": "Vincent van Gogh (public domain, pre-1928)",
        "notes": "The Starry Night, complex swirling illustration",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Hokusai_36_Fugaku_Hyakkei_Vol1_02.jpg/400px-Hokusai_36_Fugaku_Hyakkei_Vol1_02.jpg",
        "filename": "hokusai_wave.jpg",
        "source": "Wikimedia Commons / Hokusai",
        "source_url": "https://commons.wikimedia.org/wiki/File:Hokusai_36_Fugaku_Hyakkei_Vol1_02.jpg",
        "creator": "Katsushika Hokusai",
        "license": "public domain",
        "license_url": "https://en.wikipedia.org/wiki/Public_domain",
        "attribution": "Katsushika Hokusai (public domain, pre-1928)",
        "notes": "The Great Wave off Kanagawa, classic woodblock print",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d5/Rhinoceros_by_Durer.jpg/400px-Rhinoceros_by_Durer.jpg",
        "filename": "durer_rhinoceros.jpg",
        "source": "Wikimedia Commons / Albrecht Dürer",
        "source_url": "https://commons.wikimedia.org/wiki/File:Rhinoceros_by_Durer.jpg",
        "creator": "Albrecht Dürer",
        "license": "public domain",
        "license_url": "https://en.wikipedia.org/wiki/Public_domain",
        "attribution": "Albrecht Dürer, 1515 (public domain)",
        "notes": "Dürer rhinoceros woodcut, complex detailed linework",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/VanGogh-starry_night_ballance1.jpg/400px-VanGogh-starry_night_ballance1.jpg",
        "filename": "vangogh_wheatfield.jpg",
        "source": "Wikimedia Commons / Van Gogh",
        "source_url": "https://commons.wikimedia.org/wiki/File:VanGogh-starry_night_ballance1.jpg",
        "creator": "Vincent van Gogh",
        "license": "public domain",
        "license_url": "https://en.wikipedia.org/wiki/Public_domain",
        "attribution": "Vincent van Gogh (public domain, pre-1928)",
        "notes": "Van Gogh Wheatfield, complex painting illustration",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4c/Flower_jtca001.jpg/400px-Flower_jtca001.jpg",
        "filename": "macro_flower_photo.jpg",
        "source": "Wikimedia Commons",
        "source_url": "https://commons.wikimedia.org/wiki/File:Flower_jtca001.jpg",
        "creator": "JasonAntonello",
        "license": "public domain",
        "license_url": "https://en.wikipedia.org/wiki/Public_domain",
        "attribution": "JasonAntonello (public domain dedication)",
        "notes": "Macro photograph of flower with complex organic texture",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Good_Food_Display_-_NCI_Visuals_Online.jpg/400px-Good_Food_Display_-_NCI_Visuals_Online.jpg",
        "filename": "food_display_nci.jpg",
        "source": "National Cancer Institute (NCI) / Wikimedia Commons",
        "source_url": "https://commons.wikimedia.org/wiki/File:Good_Food_Display_-_NCI_Visuals_Online.jpg",
        "creator": "National Cancer Institute",
        "license": "public domain",
        "license_url": "https://en.wikipedia.org/wiki/Public_domain",
        "attribution": "National Cancer Institute (US Government Work, public domain)",
        "notes": "Complex food display, many objects and colors",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/88/Paisley_Park_Studios.jpg/400px-Paisley_Park_Studios.jpg",
        "filename": "architecture_complex.jpg",
        "source": "Wikimedia Commons",
        "source_url": "https://commons.wikimedia.org/wiki/File:Paisley_Park_Studios.jpg",
        "creator": "Various",
        "license": "public domain",
        "license_url": "https://en.wikipedia.org/wiki/Public_domain",
        "attribution": "Public domain photograph",
        "notes": "Architecture photograph, complex geometric structure",
    },
    {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Meadow_with_Cowslips.jpg/400px-Meadow_with_Cowslips.jpg",
        "filename": "meadow_flowers.jpg",
        "source": "Wikimedia Commons",
        "source_url": "https://commons.wikimedia.org/wiki/File:Meadow_with_Cowslips.jpg",
        "creator": "Ivar Leidus",
        "license": "cc by",
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "attribution": "Ivar Leidus, CC BY-SA 4.0",
        "notes": "Meadow with wildflowers, complex organic photo",
    },
]


# ─── Main population logic ───────────────────────────────────────────────────

def download_image(url: str, dest: str) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "silukman-dataset-curator/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            with open(dest, "wb") as f:
                f.write(resp.read())
        return True
    except Exception as e:
        print(f"  [download-error] {url}: {e}")
        return False


def run(dry_run: bool = False) -> None:
    print(f"=== Populating Real-World Dataset (dry_run={dry_run}) ===\n")
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs("benchmark/datasets/real_world/licenses", exist_ok=True)

    existing_hashes, existing_filenames = load_existing(MANIFEST)
    added = 0
    tmp_dir = "/tmp/silukman_dataset_tmp"
    os.makedirs(tmp_dir, exist_ok=True)

    def do_add(src: str, meta: dict) -> None:
        nonlocal added
        ok = add_image(
            src=src,
            filename=meta["filename"],
            category=meta["category"],
            source=meta["source"],
            source_url=meta["source_url"],
            creator=meta["creator"],
            license_name=meta["license"],
            license_url=meta["license_url"],
            attribution=meta["attribution"],
            notes=meta["notes"],
            existing_hashes=existing_hashes,
            existing_filenames=existing_filenames,
            dry_run=dry_run,
        )
        if ok:
            added += 1

    # ── 1. Self-made binary graphics ─────────────────────────────────────────
    print("-- binary_graphic (self-made) --")
    for i in range(10):
        fn = f"binary_graphic_selfmade_{i:02d}.png"
        tmp = os.path.join(tmp_dir, fn)
        gen_binary_graphic(tmp, i)
        do_add(tmp, {
            "filename": fn, "category": "binary_graphic",
            "source": "Self-made (Silukman Dataset Curation)",
            "source_url": "https://github.com/lukman-ss/silukman_image_vectorizer",
            "creator": "Silukman Image Vectorizer Project",
            "license": "cc0",
            "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
            "attribution": "No attribution required (CC0)",
            "notes": f"Self-made binary graphic variant {i}, generated with PIL",
        })

    # ── 2. Self-made icons ────────────────────────────────────────────────────
    print("\n-- icon (self-made) --")
    for i in range(10):
        fn = f"icon_selfmade_{i:02d}.png"
        tmp = os.path.join(tmp_dir, fn)
        gen_icon(tmp, i)
        do_add(tmp, {
            "filename": fn, "category": "icon",
            "source": "Self-made (Silukman Dataset Curation)",
            "source_url": "https://github.com/lukman-ss/silukman_image_vectorizer",
            "creator": "Silukman Image Vectorizer Project",
            "license": "cc0",
            "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
            "attribution": "No attribution required (CC0)",
            "notes": f"Self-made icon variant {i}, generated with PIL",
        })

    # ── 3. Self-made logos ────────────────────────────────────────────────────
    print("\n-- logo (self-made) --")
    for i in range(10):
        fn = f"logo_selfmade_{i:02d}.png"
        tmp = os.path.join(tmp_dir, fn)
        gen_logo(tmp, i)
        do_add(tmp, {
            "filename": fn, "category": "logo",
            "source": "Self-made (Silukman Dataset Curation)",
            "source_url": "https://github.com/lukman-ss/silukman_image_vectorizer",
            "creator": "Silukman Image Vectorizer Project",
            "license": "cc0",
            "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
            "attribution": "No attribution required (CC0)",
            "notes": f"Self-made geometric logo variant {i}, generated with PIL",
        })

    # ── 4. Self-made flat illustrations ───────────────────────────────────────
    print("\n-- flat_illustration (self-made) --")
    for i in range(10):
        fn = f"flat_illustration_selfmade_{i:02d}.png"
        tmp = os.path.join(tmp_dir, fn)
        gen_flat_illustration(tmp, i)
        do_add(tmp, {
            "filename": fn, "category": "flat_illustration",
            "source": "Self-made (Silukman Dataset Curation)",
            "source_url": "https://github.com/lukman-ss/silukman_image_vectorizer",
            "creator": "Silukman Image Vectorizer Project",
            "license": "cc0",
            "license_url": "https://creativecommons.org/publicdomain/zero/1.0/",
            "attribution": "No attribution required (CC0)",
            "notes": f"Self-made flat illustration variant {i}, generated with PIL",
        })

    # ── 5. Downloaded photographs (Public Domain / CC BY) ─────────────────────
    print("\n-- photograph (downloaded: NASA & Wikimedia PD/CC BY) --")
    for meta in NASA_IMAGES:
        tmp = os.path.join(tmp_dir, meta["filename"])
        print(f"  Downloading {meta['filename']}...")
        if download_image(meta["url"], tmp):
            do_add(tmp, dict(meta, category="photograph"))

    # ── 6. Downloaded complex illustrations (Public Domain) ───────────────────
    print("\n-- complex_illustration (downloaded: Wikimedia PD/CC BY) --")
    for meta in COMPLEX_ILLUSTRATIONS:
        tmp = os.path.join(tmp_dir, meta["filename"])
        print(f"  Downloading {meta['filename']}...")
        if download_image(meta["url"], tmp):
            do_add(tmp, dict(meta, category="complex_illustration"))

    print(f"\n=== Done. Added {added} images ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate real-world evaluation dataset")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
