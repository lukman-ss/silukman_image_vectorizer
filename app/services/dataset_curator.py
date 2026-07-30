import os
import csv
import json
import hashlib
import shutil
import argparse
from datetime import datetime, timezone
from PIL import Image


def calculate_sha256(filepath: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def handle_dataset_command(args: argparse.Namespace) -> int:
    if getattr(args, "dataset_cmd", None) == "add":
        return cmd_add(args)
    elif getattr(args, "dataset_cmd", None) == "status":
        return cmd_status(args)
    else:
        print("Invalid dataset command. Use 'add' or 'status'.")
        return 1


def cmd_add(args: argparse.Namespace) -> int:
    manifest_path = "benchmark/datasets/real_world/dataset_manifest.csv"
    images_dir = "benchmark/datasets/real_world/images"

    if not args.license or args.license.strip() == "":
        print("Error: License cannot be empty.")
        return 1

    ALLOWED_LICENSES = {"cc0", "public domain", "cc by", "cc-by"}
    if args.license.strip().lower() not in ALLOWED_LICENSES:
        print(f"Error: License '{args.license}' is not in the approved list: "
              f"{sorted(ALLOWED_LICENSES)}. Only CC0, Public Domain, CC BY are accepted.")
        return 1

    if not os.path.exists(args.file):
        print(f"Error: File {args.file} not found.")
        return 1

    # Read image props
    try:
        with Image.open(args.file) as img:
            width, height = img.size
            img_format = img.format or "UNKNOWN"
            has_alpha = img.mode in (
                "RGBA", "LA", "PA") or (
                img.info.get("transparency") is not None)
    except Exception as e:
        print(f"Error reading image: {e}")
        return 1

    file_hash = calculate_sha256(args.file)
    filename = os.path.basename(args.file)

    # 2. Duplicate Check
    os.makedirs(images_dir, exist_ok=True)
    if not os.path.exists(manifest_path):
        # Initialize manifest if missing
        headers = [
            "image_id", "filename", "category", "source", "source_url",
            "creator", "license", "license_url", "redistribution_allowed",
            "attribution", "width", "height", "format", "has_alpha",
            "sha256", "date_accessed", "notes", "dataset_role"
        ]
        if not args.dry_run:
            with open(manifest_path, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)

    existing_hashes = set()
    existing_filenames = set()
    max_id = 0

    with open(manifest_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            existing_hashes.add(row.get("sha256", ""))
            existing_filenames.add(row.get("filename", ""))
            try:
                # Expecting img_XXX
                id_num = int(row.get("image_id", "").replace("img_", ""))
                if id_num > max_id:
                    max_id = id_num
            except ValueError:
                pass

    if file_hash in existing_hashes:
        print(f"Error: Image hash {file_hash} already exists in dataset.")
        return 1
    if filename in existing_filenames:
        print(f"Error: Filename {filename} already exists. Please rename.")
        return 1

    new_id = f"img_{max_id + 1:03d}"
    dest_path = os.path.join(images_dir, filename)

    # Metadata construction
    row_data = {
        "image_id": new_id,
        "filename": filename,
        "category": args.category.strip().lower(),
        "source": "curation_cli",
        "source_url": args.source_url,
        "creator": args.creator,
        "license": args.license,
        "license_url": args.license_url,
        "redistribution_allowed": "true",
        "attribution": f"{args.creator} via {args.source_url} ({args.license})",
        "width": width,
        "height": height,
        "format": img_format,
        "has_alpha": str(has_alpha).lower(),
        "sha256": file_hash,
        "date_accessed": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "notes": "",
        "dataset_role": "evaluation"
    }

    if args.dry_run:
        print("DRY RUN: Validation passed. Will add:")
        print(json.dumps(row_data, indent=2))
        return 0

    # 3. Execution
    try:
        shutil.copy2(args.file, dest_path)
    except Exception as e:
        print(f"Error copying file: {e}")
        return 1

    with open(manifest_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=row_data.keys())
        writer.writerow(row_data)

    print(f"Successfully added {filename} as {new_id} to the dataset.")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    manifest_path = args.manifest

    if not os.path.exists(manifest_path):
        print(f"Error: Manifest {manifest_path} not found.")
        return 1

    total_images = 0
    categories = {}
    licenses = {}
    missing_metadata = 0
    invalid_files = 0
    hashes = set()
    duplicate_hashes = 0

    images_dir = os.path.join(os.path.dirname(manifest_path), "images")

    with open(manifest_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("dataset_role") != "evaluation":
                continue

            total_images += 1

            # Categories
            cat = row.get("category", "UNKNOWN")
            categories[cat] = categories.get(cat, 0) + 1

            # Licenses
            lic = row.get("license", "UNKNOWN")
            licenses[lic] = licenses.get(lic, 0) + 1

            # Missing fields
            required = ["image_id", "filename", "license", "sha256"]
            if any(not row.get(k) or str(row.get(k)).strip() == "" for k in required):
                missing_metadata += 1

            # File presence
            fname = row.get("filename", "")
            fpath = os.path.join(images_dir, fname)
            if not os.path.exists(fpath):
                invalid_files += 1

            # Duplicates
            h = row.get("sha256", "")
            if h in hashes:
                duplicate_hashes += 1
            hashes.add(h)

    print("=== Dataset Composition Report ===")
    print(f"Total Evaluation Images: {total_images}")

    print("\n-- By Category --")
    valid_categories = 0
    for k, v in categories.items():
        print(f"  {k}: {v}")
        if v >= 10:
            valid_categories += 1

    print("\n-- By License --")
    for k, v in licenses.items():
        print(f"  {k}: {v}")

    print("\n-- Quality Checks --")
    print(f"Missing Metadata: {missing_metadata}")
    print(f"Duplicate Hashes: {duplicate_hashes}")
    print(f"Missing Files: {invalid_files}")

    print("\n-- Benchmark Readiness --")
    shortfall = max(0, 60 - total_images)
    cat_shortfall = max(0, 5 - valid_categories)

    ready = True
    if total_images < 60:
        print(f" [!] Shortfall: Need {shortfall} more images.")
        ready = False
    if valid_categories < 5:
        print(f" [!] Shortfall: Need {cat_shortfall} more categories with >= 10 images.")
        ready = False
    if missing_metadata > 0 or duplicate_hashes > 0 or invalid_files > 0:
        print(" [!] Shortfall: Fix quality check failures.")
        ready = False

    print("\nStatus:")
    if ready:
        print("DATASET_READY_FOR_PILOT_BENCHMARK")
    else:
        print("DATASET_NOT_READY")

    return 0 if ready else 1
