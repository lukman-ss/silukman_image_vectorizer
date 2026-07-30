import argparse
import csv
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict
from PIL import Image


def get_sha256(filepath: str, chunk_size: int = 8192) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(chunk_size):
            sha256.update(chunk)
    return sha256.hexdigest()


def check_image_properties(filepath: str):
    try:
        with Image.open(filepath) as img:
            width, height = img.size
            has_alpha = img.mode in ("RGBA", "LA", "PA")
            # Additional check for transparency in palette
            if img.mode == 'P':
                if 'transparency' in img.info:
                    has_alpha = True

        return width, height, has_alpha, False
    except Exception:
        return None, None, None, True


def validate_manifest(manifest_path: str, schema_path: str, samples_dir: str):
    manifest_file = Path(manifest_path)
    samples = Path(samples_dir)

    report: Dict[str, Any] = {
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
        "flat illustration",
        "complex illustration",
        "photograph",
        "binary graphic",
        "geometric_shapes",
        "gradients",
        "line_art",
        "flat_logo",
        "thin_lines",
        "curves",
        "pseudo_text",
        "transparent_shapes",
        "noisy_edges",
        "overlapping_objects",
        "monochrome_silhouette"
    }

    valid_formats = {"png", "jpg", "jpeg", "webp"}
    valid_roles = {"testing_only", "evaluation", "qualitative_only"}

    seen_hashes: Dict[str, str] = {}

    with open(manifest_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row_idx, row in enumerate(reader, start=2):
            report["summary"]["total_rows"] += 1
            has_error = False

            image_id = row.get("image_id", "").strip()
            filename = row.get("filename", row.get("file_path", "")).strip()
            category = row.get("category", "").strip()
            expected_sha256 = row.get("sha256", "").strip()
            license_val = row.get("license", "").strip()
            source = row.get("source", "").strip()
            redist_allowed = row.get("redistribution_allowed", "").strip().lower()
            role = row.get("dataset_role", "testing_only").strip()
            format_val = row.get("format", "").strip().lower()

            if not image_id or not filename:
                report["errors"].append(f"Row {row_idx}: Missing required image_id or filename.")
                has_error = True
                continue

            # Core validation
            if role not in valid_roles:
                report["errors"].append(f"Row {row_idx}: Invalid dataset_role '{role}'.")
                has_error = True

            if role == "evaluation":
                if not license_val:
                    report["errors"].append(f"Row {row_idx}: License cannot be empty for evaluation.")
                    has_error = True
                if not source:
                    report["errors"].append(f"Row {row_idx}: Source cannot be empty for evaluation.")
                    has_error = True
                if category not in valid_categories:
                    report["errors"].append(f"Row {row_idx}: Invalid category '{category}' for evaluation.")
                    has_error = True
                if not redist_allowed or redist_allowed not in ["true", "1", "yes"]:
                    report["errors"].append(f"Row {row_idx}: Redistribution must be allowed for evaluation images.")
                    has_error = True

            if category and category not in valid_categories:
                report["errors"].append(f"Row {row_idx}: Invalid category '{category}'.")
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
                    f"Row {row_idx}: Checksum mismatch for '{filename}'. Expected {expected_sha256}, got {actual_sha256}."
                )
                has_error = True

            if role == "evaluation" and not expected_sha256:
                report["errors"].append(f"Row {row_idx}: Checksum is missing for evaluation image.")
                has_error = True

            if actual_sha256 in seen_hashes:
                report["duplicates"].append(
                    f"Row {row_idx}: '{filename}' is a duplicate of '{seen_hashes[actual_sha256]}'."
                )
                report["warnings"].append(
                    f"Row {row_idx}: Duplicate hash found: {actual_sha256}"
                )
            seen_hashes[actual_sha256] = filename

            actual_w, actual_h, actual_alpha, is_corrupted = check_image_properties(str(filepath))
            if is_corrupted:
                report["errors"].append(f"Row {row_idx}: Image '{filename}' is corrupted or unreadable.")
                has_error = True
                continue

            if not has_error:
                report["summary"]["total_valid"] += 1

    report["summary"]["total_errors"] = len(report["errors"])
    report["summary"]["total_warnings"] = len(report["warnings"])

    # Convert defaultdict to standard dict for JSON serialization
    report["summary"]["categories_count"] = dict(report["summary"]["categories_count"])

    return report


def main():
    parser = argparse.ArgumentParser(description="Dataset Manifest Validator")
    parser.add_argument("--manifest", default="benchmark/datasets/synthetic/dataset_manifest.csv")
    parser.add_argument("--schema", default="benchmark/real_world_manifest.schema.json")
    parser.add_argument("--samples", default="benchmark/datasets/synthetic/")
    parser.add_argument("--output", default="dataset_validation_report.json")
    parser.add_argument("--format", choices=["text", "json"], default="text")

    args = parser.parse_args()

    print("Validating dataset manifest...")
    report = validate_manifest(args.manifest, args.schema, args.samples)

    if args.format == "json":
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Report saved to {args.output}")
    else:
        print("=== Dataset Validation Report ===")
        print(f"Total Rows Checked: {report['summary']['total_rows']}")
        print(f"Total Valid Rows:   {report['summary']['total_valid']}")
        print(f"Total Errors:       {report['summary']['total_errors']}")
        print(f"Total Warnings:     {report['summary']['total_warnings']}")
        print("\nCategories Distribution:")
        for cat, count in report['summary']['categories_count'].items():
            print(f"  - {cat}: {count}")

        if report["errors"]:
            print("\nErrors:")
            for err in report["errors"][:20]:
                print(f"  [X] {err}")
            if len(report["errors"]) > 20:
                print(f"  ... and {len(report['errors']) - 20} more errors.")

        if report["warnings"]:
            print("\nWarnings:")
            for w in report["warnings"][:10]:
                print(f"  [!] {w}")

    if report["errors"]:
        sys.exit(1)
    else:
        print("\nSuccess: Dataset is valid.")
        sys.exit(0)


if __name__ == "__main__":
    main()
