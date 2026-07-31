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
        "illustration",
        "flat illustration",
        "complex illustration",
        "complex_artwork",
        "photograph",
        "binary_graphic",
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

            origin_type = row.get("origin_type", "").strip()
            original_asset_url = row.get("original_asset_url", "").strip()
            publication_scope = row.get("publication_scope", "").strip()
            creator = row.get("creator", "").strip()
            license_url = row.get("license_url", "").strip()
            source_url = row.get("source_url", "").strip()
            attribution = row.get("attribution", "").strip()

            # Core validation
            if role not in valid_roles:
                report["errors"].append(f"Row {row_idx}: Invalid dataset_role '{role}'.")
                has_error = True

            if role == "evaluation":
                if not license_val:
                    report["errors"].append(
                        f"Row {row_idx}: License cannot be empty for evaluation.")
                    has_error = True
                if not source:
                    report["errors"].append(
                        f"Row {row_idx}: Source cannot be empty for evaluation.")
                    has_error = True
                if category not in valid_categories:
                    report["errors"].append(
                        f"Row {row_idx}: Invalid category '{category}' for evaluation.")
                    has_error = True
                if not redist_allowed or redist_allowed not in ["true", "1", "yes"]:
                    report["errors"].append(
                        f"Row {row_idx}: Redistribution must be allowed for evaluation images.")
                    has_error = True

            # Strict Provenance Rules
            if license_val.lower() == "cc0" and "by-sa" in license_url.lower():
                report["errors"].append(f"Row {row_idx}: License mismatch, claimed CC0 but URL is CC BY-SA.")
                has_error = True

            if origin_type == "api_delivered_real_world" and creator.lower() in ["unsplash contributors", "unknown", "generic"]:
                report["errors"].append(f"Row {row_idx}: Generic creator not allowed when API provides real author.")
                has_error = True
            
            if "robohash" in source_url.lower() and role == "evaluation" and "real_world" in str(manifest_file):
                report["errors"].append(f"Row {row_idx}: RoboHash cannot be used as real-world evaluation data.")
                has_error = True

            if origin_type == "api_generated" and "real_world" in str(manifest_file):
                report["errors"].append(f"Row {row_idx}: Origin type api_generated cannot be used in real-world manifest.")
                has_error = True

            if origin_type == "api_generated" and publication_scope == "main_evaluation":
                report["errors"].append(f"Row {row_idx}: Generated data cannot have publication_scope=main_evaluation.")
                has_error = True
            
            if origin_type == "api_delivered_real_world" and not original_asset_url:
                report["errors"].append(f"Row {row_idx}: API delivered asset must include original_asset_url.")
                has_error = True
                
            if attribution:
                if "(" in attribution and attribution.endswith(")"):
                    attr_license = attribution.rsplit("(", 1)[1][:-1]
                    if license_val == "CC BY-SA 4.0" and attr_license != "CC BY-SA 4.0":
                        report["errors"].append(f"Row {row_idx}: Attribution suffix '({attr_license})' does not match license 'CC BY-SA 4.0'.")
                        has_error = True
                    elif license_val == "Unsplash License" and attr_license == "CC0":
                        report["errors"].append(f"Row {row_idx}: Unsplash License cannot have attribution (CC0).")
                        has_error = True
                    elif license_val == "Public Domain" and attr_license != "Public Domain":
                        report["errors"].append(f"Row {row_idx}: Public Domain license must have attribution (Public Domain).")
                        has_error = True
                    elif license_val == "CC0" and attr_license != "CC0":
                        report["errors"].append(f"Row {row_idx}: CC0 license must have attribution (CC0).")
                        has_error = True

            if role == "evaluation" and (not license_val or not license_url):
                report["errors"].append(f"Row {row_idx}: Evaluation data must have a valid license and license_url.")
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
                report["errors"].append(
                    f"Row {row_idx}: Image '{filename}' is corrupted or unreadable.")
                has_error = True
                continue

            if not has_error:
                report["summary"]["total_valid"] += 1

    report["summary"]["total_errors"] = len(report["errors"])
    report["summary"]["total_warnings"] = len(report["warnings"])

    # Convert defaultdict to standard dict for JSON serialization
    report["summary"]["categories_count"] = dict(report["summary"]["categories_count"])

    return report


def check_cross_dataset_duplicates():
    import glob
    from typing import Dict, Tuple
    manifests = glob.glob("benchmark/datasets/*/dataset_manifest.csv")
    global_hashes: Dict[str, Tuple[str, str]] = {}
    errors = []
    
    for manifest_path in manifests:
        dataset_name = Path(manifest_path).parent.name
        with open(manifest_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                sha = row.get("sha256", "").strip()
                img_id = row.get("image_id", "").strip()
                if not sha:
                    continue
                if sha in global_hashes:
                    prev_dataset, prev_id = global_hashes[sha]
                    if prev_dataset != dataset_name:
                        errors.append(
                            f"Cross-dataset duplicate hash detected: {sha} "
                            f"is in both '{prev_dataset}' (id: {prev_id}) "
                            f"and '{dataset_name}' (id: {img_id})."
                        )
                else:
                    global_hashes[sha] = (dataset_name, img_id)
    return errors


def main():
    parser = argparse.ArgumentParser(description="Dataset Manifest Validator")
    parser.add_argument("--manifest", default="benchmark/datasets/synthetic/dataset_manifest.csv")
    parser.add_argument("--schema", default="benchmark/real_world_manifest.schema.json")
    parser.add_argument("--samples", default="benchmark/datasets/synthetic/")
    parser.add_argument("--output", default="dataset_validation_report.json")
    parser.add_argument("--format", choices=["text", "json"], default="text")

    args = parser.parse_args()

    print("Checking for cross-dataset duplicate hashes...")
    cross_errors = check_cross_dataset_duplicates()
    
    print("Validating dataset manifest...")
    report = validate_manifest(args.manifest, args.schema, args.samples)

    if cross_errors:
        report["errors"].extend(cross_errors)
        report["summary"]["total_errors"] += len(cross_errors)

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
        # Benchmark gate check for real_world evaluation dataset
        if "real_world" in args.manifest:
            total = report["summary"]["total_valid"]
            valid_cats = sum(1 for _, v in report["summary"]["categories_count"].items() if v >= 10)

            ready = True
            if total < 60:
                print(f"  [!] Minimum 60 images required (Found {total})")
                ready = False
            if valid_cats < 5:
                print(f"  [!] Minimum 5 categories with >= 10 images required (Found {valid_cats})")
                ready = False

            if ready:
                print("\nDATASET_READY_FOR_PILOT_BENCHMARK")
                sys.exit(0)
            else:
                print("\nDATASET_NOT_READY")
                sys.exit(1)
        else:
            print("\nSuccess: Dataset is valid.")
            sys.exit(0)


if __name__ == "__main__":
    main()
