"""
audit_dataset_diversity.py

Generates a comprehensive dataset diversity report covering:
- Images per source
- Twemoji percentage
- Images per resolution bucket
- Images per creator
- Images per category × source
- Source concentration (HHI)
- Resolution concentration
- Style concentration warning

Analysis groups:
- Overall
- Without dominant source family
- Per source family
- Per category

Output:
  benchmark/results/diversity/dataset_diversity_report.md
  benchmark/results/diversity/dataset_diversity.csv

Usage:
  python -m benchmark.scripts.audit_dataset_diversity
  python benchmark/scripts/audit_dataset_diversity.py [--manifest <path>]
"""
import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

DEFAULT_MANIFEST = REPO_ROOT / "benchmark" / "datasets" / "real_world" / "dataset_manifest.csv"
OUTPUT_DIR = REPO_ROOT / "benchmark" / "results" / "diversity"


def _load_manifest(path: Path) -> List[Dict[str, str]]:
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _hhi(counts: Counter) -> float:
    """Herfindahl-Hirschman Index: 0=perfectly diverse, 1=monopoly."""
    total = sum(counts.values())
    if total == 0:
        return 0.0
    return sum((v / total) ** 2 for v in counts.values())


def _resolution_bucket(w: int, h: int) -> str:
    pixels = w * h
    if pixels <= 72 * 72:
        return "tiny (≤72×72)"
    elif pixels <= 256 * 256:
        return "small (≤256×256)"
    elif pixels <= 512 * 512:
        return "medium (≤512×512)"
    elif pixels <= 1920 * 1080:
        return "large (≤1920×1080)"
    else:
        return "very large (>1920×1080)"


def audit(manifest_path: Path) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = _load_manifest(manifest_path)

    # Only evaluation-eligible rows
    eval_rows = [r for r in rows if r.get("dataset_role") == "evaluation"]
    total = len(eval_rows)

    if total == 0:
        print("No evaluation rows found in manifest.", file=sys.stderr)
        sys.exit(1)

    print(f"Loaded {total} evaluation images from {manifest_path.name}\n")

    # -----------------------------------------------------------------------
    # Dimension extraction
    # -----------------------------------------------------------------------
    for r in eval_rows:
        try:
            r["_w"] = int(r.get("width") or 0)
            r["_h"] = int(r.get("height") or 0)
        except ValueError:
            r["_w"] = r["_h"] = 0

        r["_source_family"] = r.get("source", "unknown")
        r["_resolution_bucket"] = _resolution_bucket(r["_w"], r["_h"])
        r["_category"] = r.get("category", "unknown")
        r["_creator"] = r.get("creator", "unknown")

    # -----------------------------------------------------------------------
    # Counters
    # -----------------------------------------------------------------------
    source_counts: Counter = Counter(r["_source_family"] for r in eval_rows)
    category_counts: Counter = Counter(r["_category"] for r in eval_rows)
    resolution_counts: Counter = Counter(r["_resolution_bucket"] for r in eval_rows)
    creator_counts: Counter = Counter(r["_creator"] for r in eval_rows)

    # Category × Source matrix
    cat_src: Dict[str, Counter] = defaultdict(Counter)
    for r in eval_rows:
        cat_src[r["_category"]][r["_source_family"]] += 1

    # Identify dominant source family
    dominant_source = source_counts.most_common(1)[0][0] if source_counts else "unknown"
    dominant_count = source_counts[dominant_source]
    dominant_pct = 100 * dominant_count / total

    twemoji_count = source_counts.get("Twemoji", 0)
    twemoji_pct = 100 * twemoji_count / total

    source_hhi = _hhi(source_counts)
    resolution_hhi = _hhi(resolution_counts)

    # Without dominant family
    non_dominant = [r for r in eval_rows if r["_source_family"] != dominant_source]
    non_dominant_category: Counter = Counter(r["_category"] for r in non_dominant)
    non_dominant_source: Counter = Counter(r["_source_family"] for r in non_dominant)

    # -----------------------------------------------------------------------
    # Build report
    # -----------------------------------------------------------------------
    lines: List[str] = [
        "# Dataset Diversity Audit Report",
        "",
        f"**Manifest:** `{manifest_path.name}`  ",
        f"**Total evaluation images:** {total}  ",
        f"**Dominant source family:** {dominant_source} ({dominant_count} images, {dominant_pct:.1f}%)  ",
        f"**Twemoji images:** {twemoji_count} ({twemoji_pct:.1f}%)  ",
        "",
    ]

    # Style concentration warning
    if dominant_pct > 60:
        lines += [
            "> [!WARNING]",
            f"> **Style concentration alert:** {dominant_pct:.1f}% of images ({dominant_count}/{total}) "
            f"are from a single source family ({dominant_source}). "
            "Aggregate results will heavily reflect this family's visual style. "
            "Do NOT claim broad visual diversity without this caveat.",
            "",
        ]

    # ---
    lines += ["## 1. Images per Source", "", "| Source | Count | Percentage |", "|:-------|------:|-----------:|"]
    for src, cnt in source_counts.most_common():
        lines.append(f"| {src} | {cnt} | {100*cnt/total:.1f}% |")
    lines += [f"| **Source HHI** | | **{source_hhi:.3f}** (0=diverse, 1=monopoly) |", ""]

    # ---
    lines += ["## 2. Images per Category", "", "| Category | Count | Percentage |", "|:---------|------:|-----------:|"]
    for cat, cnt in category_counts.most_common():
        lines.append(f"| {cat} | {cnt} | {100*cnt/total:.1f}% |")
    lines.append("")

    # ---
    lines += ["## 3. Images per Resolution Bucket", "", "| Bucket | Count | Percentage |", "|:-------|------:|-----------:|"]
    for bkt, cnt in resolution_counts.most_common():
        lines.append(f"| {bkt} | {cnt} | {100*cnt/total:.1f}% |")
    lines += [f"| **Resolution HHI** | | **{resolution_hhi:.3f}** |", ""]

    # ---
    lines += ["## 4. Images per Creator (Top 20)", "", "| Creator | Count |", "|:--------|------:|"]
    for creator, cnt in creator_counts.most_common(20):
        lines.append(f"| {creator} | {cnt} |")
    lines.append("")

    # ---
    lines += ["## 5. Category × Source Matrix", "", "| Category | " + " | ".join(source_counts.keys()) + " |",
              "|:---------|" + "|".join(["------:" for _ in source_counts]) + "|"]
    for cat in sorted(cat_src.keys()):
        row_vals = [str(cat_src[cat].get(src, 0)) for src in source_counts.keys()]
        lines.append(f"| {cat} | " + " | ".join(row_vals) + " |")
    lines.append("")

    # ---
    lines += [
        "## 6. Analysis Without Dominant Source Family",
        "",
        f"_(Excluding {dominant_source}: {len(non_dominant)} images remaining)_",
        "",
        "| Category | Count |",
        "|:---------|------:|",
    ]
    for cat, cnt in non_dominant_category.most_common():
        lines.append(f"| {cat} | {cnt} |")
    lines.append("")

    if non_dominant:
        lines += ["| Source | Count |", "|:-------|------:|"]
        for src, cnt in non_dominant_source.most_common():
            lines.append(f"| {src} | {cnt} |")
    lines.append("")

    # ---
    lines += [
        "## 7. Benchmark Analysis Guidance",
        "",
        "When reporting benchmark results, provide ALL of the following views:",
        "",
        "1. **Overall aggregate** — all images.",
        f"2. **Without {dominant_source}** — {len(non_dominant)} images, eliminates dominant-family bias.",
        "3. **Per source family** — separate stats for each source.",
        "4. **Per category** — separate stats for each category.",
        "",
        "> [!IMPORTANT]",
        "> Do NOT claim that logo, illustration, or binary_graphic categories represent a broad",
        f"> visual range if >60% of those images come from {dominant_source}.",
        "",
    ]

    # -----------------------------------------------------------------------
    # Write output
    # -----------------------------------------------------------------------
    report_path = OUTPUT_DIR / "dataset_diversity_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Report saved to: {report_path}")

    # Write detailed CSV
    csv_rows = []
    for r in eval_rows:
        csv_rows.append({
            "image_id": r["image_id"],
            "category": r["_category"],
            "source_family": r["_source_family"],
            "creator": r["_creator"],
            "width": r["_w"],
            "height": r["_h"],
            "total_pixels": r["_w"] * r["_h"],
            "resolution_bucket": r["_resolution_bucket"],
            "license": r.get("license", ""),
            "is_dominant_family": "true" if r["_source_family"] == dominant_source else "false",
        })

    csv_path = OUTPUT_DIR / "dataset_diversity.csv"
    if csv_rows:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
            writer.writeheader()
            writer.writerows(csv_rows)
        print(f"CSV saved to: {csv_path}")

    # Print summary
    print(f"\n=== Diversity Summary ===")
    print(f"Total images    : {total}")
    print(f"Dominant source : {dominant_source} ({dominant_count}, {dominant_pct:.1f}%)")
    print(f"Source HHI      : {source_hhi:.3f} (0=diverse, 1=monopoly)")
    print(f"Resolution HHI  : {resolution_hhi:.3f}")
    if twemoji_pct > 60:
        print(f"\n[!] Twemoji concentration: {twemoji_pct:.1f}% — aggregate results may not generalize.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Dataset diversity audit")
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST), help="Path to dataset_manifest.csv")
    args = parser.parse_args()
    audit(Path(args.manifest))


if __name__ == "__main__":
    main()
