import argparse
import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

import cv2


def get_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_image_info(filepath: str):
    """Returns (width, height, has_alpha, is_corrupted)"""
    try:
        # IMREAD_UNCHANGED keeps alpha channel if present
        img = cv2.imread(filepath, cv2.IMREAD_UNCHANGED)
        if img is None:
            return None, None, None, True

        height, width = img.shape[:2]
        has_alpha = False
        if len(img.shape) == 3 and img.shape[2] == 4:
            has_alpha = True

        return width, height, has_alpha, False
    except Exception:
        return None, None, None, True


def validate_manifest(manifest_path: str, schema_path: str, samples_dir: str):
    manifest_file = Path(manifest_path)
    samples = Path(samples_dir)

    report = {
        "summary": {
            "total_rows": 0,
            "total_valid": 0,
            "total_errors": 0,
            "total_warnings": 0,
            "categories_count": defaultdict(int),
        },
        "errors": [],
        "warnings": [],
        "duplicates": [],
    }

    if not manifest_file.exists():
        report["errors"].append("Manifest file not found.")
        return report

    valid_categories = {
        "logo",
        "icon",
        "illustration",
        "complex_artwork",
        "photograph",
        "binary_graphic",
    }
    valid_splits = {"train", "validation", "test"}
    valid_formats = {"png", "jpg", "jpeg", "bmp", "webp"}

    # Check for jsonschema library, if available validate against schema file
    # We will skip formal jsonschema validation if lib is not present, doing it manually

    seen_ids = set()
    seen_filenames = set()
    seen_hashes = {}

    with open(manifest_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row_idx, row in enumerate(reader, start=2):
            report["summary"]["total_rows"] += 1
            has_error = False

            image_id = row.get("image_id", "").strip()
            filename = row.get("filename", "").strip()
            category = row.get("category", "").strip()
            license_val = row.get("license", "").strip()
            split = row.get("split", "").strip()
            format_val = row.get("format", "").strip()
            expected_sha256 = row.get("sha256", "").strip()
            has_alpha_str = row.get("has_alpha", "").strip().lower()

            # Uniqueness
            if not image_id:
                report["errors"].append(f"Row {row_idx}: Missing image_id.")
                has_error = True
            elif image_id in seen_ids:
                report["errors"].append(f"Row {row_idx}: Duplicate image_id '{image_id}'.")
                has_error = True
            else:
                seen_ids.add(image_id)

            if not filename:
                report["errors"].append(f"Row {row_idx}: Missing filename.")
                has_error = True
            elif filename in seen_filenames:
                report["errors"].append(f"Row {row_idx}: Duplicate filename '{filename}'.")
                has_error = True
            else:
                seen_filenames.add(filename)

            # License
            if not license_val:
                report["errors"].append(f"Row {row_idx}: License cannot be empty.")
                has_error = True

            # Category and Split
            if category and category not in valid_categories:
                report["errors"].append(f"Row {row_idx}: Invalid category '{category}'.")
                has_error = True
            if split and split not in valid_splits:
                report["errors"].append(f"Row {row_idx}: Invalid split '{split}'.")
                has_error = True
            if format_val and format_val not in valid_formats:
                report["errors"].append(f"Row {row_idx}: Invalid format '{format_val}'.")
                has_error = True

            report["summary"]["categories_count"][category] += 1

            # File validation
            filepath = samples / filename
            if not filepath.exists():
                report["errors"].append(
                    f"Row {row_idx}: File '{filename}' not found in samples directory."
                )
                has_error = True
                continue

            actual_sha256 = get_sha256(str(filepath))
            if expected_sha256 and actual_sha256 != expected_sha256:
                report["errors"].append(
                    f"Row {row_idx}: SHA-256 mismatch for '{filename}'. Expected: {expected_sha256}, Got: {actual_sha256}"
                )
                has_error = True

            if actual_sha256 in seen_hashes:
                dup = seen_hashes[actual_sha256]
                msg = f"Duplicate content detected: '{filename}' and '{dup}' have the same SHA-256."
                report["warnings"].append(msg)
                report["duplicates"].append(
                    {"file1": dup, "file2": filename, "sha256": actual_sha256}
                )
            else:
                seen_hashes[actual_sha256] = filename

            width, height, has_alpha, is_corrupt = get_image_info(str(filepath))
            if is_corrupt:
                report["errors"].append(
                    f"Row {row_idx}: File '{filename}' is corrupted or unreadable."
                )
                has_error = True
                continue

            expected_w = row.get("width")
            expected_h = row.get("height")
            if expected_w and str(width) != expected_w:
                report["errors"].append(
                    f"Row {row_idx}: Width mismatch for '{filename}'. Expected: {expected_w}, Got: {width}"
                )
                has_error = True
            if expected_h and str(height) != expected_h:
                report["errors"].append(
                    f"Row {row_idx}: Height mismatch for '{filename}'. Expected: {expected_h}, Got: {height}"
                )
                has_error = True

            if has_alpha_str == "true" and not has_alpha:
                report["errors"].append(
                    f"Row {row_idx}: Metadata says has_alpha=true, but no alpha channel found in '{filename}'."
                )
                has_error = True
            elif has_alpha_str == "false" and has_alpha:
                report["warnings"].append(
                    f"Row {row_idx}: Metadata says has_alpha=false, but alpha channel detected in '{filename}'."
                )

            if not has_error:
                report["summary"]["total_valid"] += 1

    report["summary"]["total_errors"] = len(report["errors"])
    report["summary"]["total_warnings"] = len(report["warnings"])
    return report


def main():
    parser = argparse.ArgumentParser(description="Dataset Manifest Validator")
    parser.add_argument("--manifest", default="benchmark/dataset_manifest.csv")
    parser.add_argument("--schema", default="benchmark/dataset_manifest.schema.json")
    parser.add_argument("--samples", default="benchmark/samples")
    parser.add_argument("--json", action="store_true", help="Output JSON report")
    args = parser.parse_args()

    report = validate_manifest(args.manifest, args.schema, args.samples)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("=== Dataset Validation Report ===")
        print(f"Total rows parsed: {report['summary']['total_rows']}")
        print(f"Total valid rows: {report['summary']['total_valid']}")
        print(f"Categories Count: {dict(report['summary']['categories_count'])}")

        if report["duplicates"]:
            print("\n--- Duplicates Found ---")
            for d in report["duplicates"]:
                print(f"  {d['file1']} == {d['file2']} (SHA: {d['sha256'][:8]}...)")

        if report["warnings"]:
            print("\n--- Warnings ---")
            for w in report["warnings"]:
                print(f"  [WARN] {w}")

        if report["errors"]:
            print("\n--- Critical Errors ---")
            for e in report["errors"]:
                print(f"  [ERROR] {e}")

    if report["summary"]["total_errors"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
