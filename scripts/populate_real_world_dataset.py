#!/usr/bin/env python3
"""
Populate the real-world evaluation dataset with CC0 / Public Domain images.

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
from typing import Dict, Tuple

# ─── Paths ────────────────────────────────────────────────────────────────────
MANIFEST = "benchmark/datasets/real_world/dataset_manifest.csv"
IMAGES_DIR = "benchmark/datasets/real_world/images"
ALLOWED_LICENSES = {"cc0", "public domain", "cc by", "cc-by", "cc by-sa", "cc-by-sa"}
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

# ─── Helpers ──────────────────────────────────────────────────────────────────


def sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_existing(manifest: str) -> Tuple[Dict[str, str], set]:
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
        w = csv.DictWriter(f, fieldnames=fieldnames)
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

    # Assuming these are all JPEGs or PNGs without alpha for these public domain photos
    fmt = Path(src).suffix.lstrip(".").upper()
    has_alpha = False

    # Optional width/height extraction (since we removed PIL dependency, we just put "unknown")
    width = 0
    height = 0

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
]


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

    print("\n-- photograph (downloaded: NASA & Wikimedia PD/CC BY) --")
    for meta in NASA_IMAGES:
        tmp = os.path.join(tmp_dir, meta["filename"])
        print(f"  Downloading {meta['filename']}...")
        if download_image(meta["url"], tmp):
            do_add(tmp, dict(meta, category="photograph"))

    print(f"\n=== Done. Added {added} images ===")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Populate real-world evaluation dataset")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    run(dry_run=args.dry_run)
