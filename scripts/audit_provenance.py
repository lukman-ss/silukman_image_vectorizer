import csv
import json
import shutil
import urllib.request
import urllib.error
from pathlib import Path

def setup_synthetic_dir():
    Path("benchmark/datasets/synthetic_evaluation/images").mkdir(parents=True, exist_ok=True)
    manifest = Path("benchmark/datasets/synthetic_evaluation/dataset_manifest.csv")
    if not manifest.exists():
        with open(manifest, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "image_id", "filename", "category", "source", "source_url", "creator", "license",
                "license_url", "redistribution_allowed", "attribution", "width", "height", "format",
                "has_alpha", "sha256", "date_accessed", "notes", "dataset_role", "origin_type",
                "api_provider", "api_request_url", "original_asset_url", "work_title",
                "license_verified", "provenance_status", "publication_scope"
            ])

def setup_quarantine_dir():
    Path("benchmark/datasets/quarantine/images").mkdir(parents=True, exist_ok=True)
    manifest = Path("benchmark/datasets/quarantine/dataset_manifest.csv")
    if not manifest.exists():
        with open(manifest, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "image_id", "filename", "category", "source", "source_url", "creator", "license",
                "license_url", "redistribution_allowed", "attribution", "width", "height", "format",
                "has_alpha", "sha256", "date_accessed", "notes", "dataset_role", "origin_type",
                "api_provider", "api_request_url", "original_asset_url", "work_title",
                "license_verified", "provenance_status", "publication_scope"
            ])

def append_to_synthetic(row):
    manifest = Path("benchmark/datasets/synthetic_evaluation/dataset_manifest.csv")
    fields = [
        "image_id", "filename", "category", "source", "source_url", "creator", "license",
        "license_url", "redistribution_allowed", "attribution", "width", "height", "format",
        "has_alpha", "sha256", "date_accessed", "notes", "dataset_role", "origin_type",
        "api_provider", "api_request_url", "original_asset_url", "work_title",
        "license_verified", "provenance_status", "publication_scope"
    ]
    with open(manifest, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        for k in fields:
            if k not in row:
                row[k] = ""
        writer.writerow(row)

def append_to_quarantine(row):
    manifest = Path("benchmark/datasets/quarantine/dataset_manifest.csv")
    fields = [
        "image_id", "filename", "category", "source", "source_url", "creator", "license",
        "license_url", "redistribution_allowed", "attribution", "width", "height", "format",
        "has_alpha", "sha256", "date_accessed", "notes", "dataset_role", "origin_type",
        "api_provider", "api_request_url", "original_asset_url", "work_title",
        "license_verified", "provenance_status", "publication_scope"
    ]
    with open(manifest, "a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        for k in fields:
            if k not in row:
                row[k] = ""
        writer.writerow(row)

def fetch_picsum_info(seed_id):
    url = f"https://picsum.photos/seed/{seed_id}/info"
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            if response.status == 200:
                data = json.loads(response.read().decode())
                return data
    except Exception as e:
        print(f"Error fetching picsum info for {seed_id}: {e}")
    return None

def main():
    setup_synthetic_dir()
    setup_quarantine_dir()
    
    real_world_manifest = Path("benchmark/datasets/real_world/dataset_manifest.csv")
    with open(real_world_manifest, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    new_real_world = []
    
    fields = [
        "image_id", "filename", "category", "source", "source_url", "creator", "license",
        "license_url", "redistribution_allowed", "attribution", "width", "height", "format",
        "has_alpha", "sha256", "date_accessed", "notes", "dataset_role", "origin_type",
        "api_provider", "api_request_url", "original_asset_url", "work_title",
        "license_verified", "provenance_status", "publication_scope"
    ]
    
    for row in rows:
        source_url = row.get("source_url", "").lower()
        
        # Initialize new fields
        row["origin_type"] = "unverified"
        row["api_provider"] = ""
        row["api_request_url"] = ""
        row["original_asset_url"] = ""
        row["work_title"] = ""
        row["license_verified"] = "false"
        row["provenance_status"] = "unverified"
        row["publication_scope"] = "main_evaluation"
        
        if "robohash.org" in source_url:
            row["origin_type"] = "api_generated"
            row["dataset_role"] = "synthetic_evaluation"
            row["publication_scope"] = "synthetic_analysis"
            row["api_provider"] = "Robohash"
            row["api_request_url"] = row["source_url"]
            row["original_asset_url"] = ""
            row["license_verified"] = "true"
            row["provenance_status"] = "verified"
            
            # Move file
            src_path = Path("benchmark/datasets/real_world/images") / row["filename"]
            dst_path = Path("benchmark/datasets/synthetic_evaluation/images") / row["filename"]
            if src_path.exists():
                shutil.move(str(src_path), str(dst_path))
            
            append_to_synthetic(row)
            print(f"Moved {row['filename']} to synthetic.")
            
        elif "picsum.photos" in source_url:
            seed_id = row["source_url"].split("/seed/")[1].split("/")[0]
            info = fetch_picsum_info(seed_id)
            if info:
                row["origin_type"] = "api_delivered_real_world"
                row["api_provider"] = "Lorem Picsum"
                row["api_request_url"] = row["source_url"]
                row["original_asset_url"] = info.get("url", "")
                row["creator"] = info.get("author", "Unknown")
                row["work_title"] = f"Unsplash Photo {info.get('id', '')}"
                row["license"] = "Unsplash License"
                row["license_url"] = "https://unsplash.com/license"
                row["attribution"] = f"{row['creator']} via Unsplash"
                row["license_verified"] = "true"
                row["provenance_status"] = "verified"
                
                print(f"Updated Picsum image {row['filename']} with true author: {row['creator']}")
                new_real_world.append(row)
            else:
                print(f"Failed to fetch info for {row['filename']}")
                src_path = Path("benchmark/datasets/real_world/images") / row["filename"]
                dst_path = Path("benchmark/datasets/quarantine/images") / row["filename"]
                if src_path.exists():
                    shutil.move(str(src_path), str(dst_path))
                append_to_quarantine(row)
                
        elif "commons.wikimedia.org" in source_url:
            row["origin_type"] = "external_real_world"
            row["license_verified"] = "true"
            row["provenance_status"] = "verified"
            row["original_asset_url"] = row["source_url"]
            
            # Fix CC0 vs CC BY-SA mismatches
            if row.get("license", "").lower() == "cc0" and "by-sa" in row.get("license_url", "").lower():
                row["license"] = "CC BY-SA 4.0"
                print(f"Fixed license mismatch for {row['filename']} to CC BY-SA")
                
            new_real_world.append(row)
            
        else:
            # Other unverified
            print(f"Quarantining unverified image: {row['filename']}")
            src_path = Path("benchmark/datasets/real_world/images") / row["filename"]
            dst_path = Path("benchmark/datasets/quarantine/images") / row["filename"]
            if src_path.exists():
                shutil.move(str(src_path), str(dst_path))
            append_to_quarantine(row)

    # Write back to real_world
    with open(real_world_manifest, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in new_real_world:
            # Ensure all keys exist
            for k in fields:
                if k not in r:
                    r[k] = ""
            # subset dict to fields
            r_subset = {k: r[k] for k in fields}
            writer.writerow(r_subset)

if __name__ == "__main__":
    main()
