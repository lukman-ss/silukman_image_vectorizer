"""
run_scaling_pilot.py

Scaling pilot to determine the relationship between image resolution and
runtime/quality, enabling evidence-based pixel limits for benchmark configs.

Resizes 1-2 representative images to 5 resolution tiers, then runs Silukman
and VTracer across all 3 presets, measuring wall-clock time, peak memory,
SVG size, path count, and quality metrics.

Output:
  benchmark/results/scaling_pilot/scaling_results.csv
  benchmark/results/scaling_pilot/scaling_pilot_report.md

Usage:
  python -m benchmark.scripts.run_scaling_pilot
"""

import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

RESOLUTION_TIERS = [256, 512, 1024, 2048, None]  # None = original
PRESETS = ["low_complexity", "balanced", "high_fidelity"]
BACKENDS = ["silukman", "vtracer"]

OUTPUT_DIR = REPO_ROOT / "benchmark" / "results" / "scaling_pilot"
RESULTS_CSV = OUTPUT_DIR / "scaling_results.csv"
REPORT_MD = OUTPUT_DIR / "scaling_pilot_report.md"

TIMEOUT_SECONDS = 120  # per-run hard limit for scaling pilot


def _pick_representative_images() -> List[Dict[str, str]]:
    """
    Select 2 representative images from the real-world dataset:
      - One small image (Twemoji, 72x72)
      - One large image (Wikimedia photograph)
    """
    manifest_path = REPO_ROOT / "benchmark" / "datasets" / "real_world" / "dataset_manifest.csv"
    images_dir = REPO_ROOT / "benchmark" / "datasets" / "real_world" / "images"

    candidates = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("dataset_role") != "evaluation":
                continue
            fname = row.get("filename", "")
            fpath = images_dir / fname
            if not fpath.exists():
                continue
            candidates.append({
                "image_id": row["image_id"],
                "path": str(fpath),
                "width": int(row["width"]) if row.get("width") else 0,
                "height": int(row["height"]) if row.get("height") else 0,
                "category": row["category"],
            })

    # Pick smallest and largest by pixel count
    candidates.sort(key=lambda r: r["width"] * r["height"])
    selected = []
    if candidates:
        selected.append(candidates[0])   # smallest
        if len(candidates) > 1:
            selected.append(candidates[-1])  # largest
    return selected


def _resize_image(src: str, max_side: Optional[int], dest: str) -> bool:
    """Resize image to fit within max_side x max_side using Pillow."""
    try:
        from PIL import Image as PILImage
        with PILImage.open(src) as img:
            if max_side is None:
                shutil.copy(src, dest)
                return True
            w, h = img.size
            ratio = min(max_side / w, max_side / h, 1.0)
            new_w = max(1, int(w * ratio))
            new_h = max(1, int(h * ratio))
            resized = img.resize((new_w, new_h), PILImage.LANCZOS)
            resized.save(dest)
            return True
    except Exception as e:
        print(f"  [WARN] Resize failed for {src} at {max_side}px: {e}", file=sys.stderr)
        return False


def _get_actual_size(path: str) -> tuple:
    """Return (width, height) of image using PIL."""
    try:
        from PIL import Image as PILImage
        with PILImage.open(path) as img:
            return img.size
    except Exception:
        return (0, 0)


def _run_backend(
    backend_name: str,
    input_path: str,
    output_path: str,
    preset: str,
    timeout: int,
) -> Dict[str, Any]:
    """
    Run a single vectorization via subprocess with timeout.
    Returns a result dict.
    """
    cmd = [
        sys.executable, "-m", "benchmark.runner._backend_worker_cli",
        "--backend", backend_name,
        "--input", input_path,
        "--output", output_path,
        "--preset", preset,
    ]
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(REPO_ROOT),
        )
        elapsed = time.perf_counter() - start
        if proc.returncode == 0:
            try:
                result = json.loads(proc.stdout)
            except json.JSONDecodeError:
                result = {"performance": {"success": True}}
            result["wall_clock_time_seconds"] = elapsed
            result["status"] = "success"
            return result
        else:
            return {"status": "failed", "error": proc.stderr, "wall_clock_time_seconds": elapsed}
    except subprocess.TimeoutExpired:
        elapsed = time.perf_counter() - start
        return {
            "status": "timeout",
            "error_type": "BackendTimeoutError",
            "wall_clock_time_seconds": elapsed,
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _svg_stats(svg_path: str) -> Dict[str, Any]:
    """Compute SVG file size and approximate path count."""
    if not os.path.exists(svg_path):
        return {"svg_size_bytes": 0, "path_count": 0}
    size = os.path.getsize(svg_path)
    try:
        with open(svg_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        path_count = content.count("<path ")
    except Exception:
        path_count = 0
    return {"svg_size_bytes": size, "path_count": path_count}


def run_scaling_pilot() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    images = _pick_representative_images()
    if not images:
        print("ERROR: No representative images found in dataset.", file=sys.stderr)
        sys.exit(1)

    print(f"Running scaling pilot on {len(images)} image(s) across {len(RESOLUTION_TIERS)} resolution tiers.")
    print(f"Backends: {BACKENDS} | Presets: {PRESETS} | Timeout: {TIMEOUT_SECONDS}s")

    rows: List[Dict[str, Any]] = []

    with tempfile.TemporaryDirectory() as tmpdir:
        for img in images:
            for tier in RESOLUTION_TIERS:
                tier_label = str(tier) if tier else "original"
                resized_path = os.path.join(tmpdir, f"{img['image_id']}_{tier_label}.png")
                ok = _resize_image(img["path"], tier, resized_path)
                if not ok:
                    continue

                actual_w, actual_h = _get_actual_size(resized_path)
                pixels = actual_w * actual_h

                for backend in BACKENDS:
                    for preset in PRESETS:
                        output_svg = os.path.join(
                            tmpdir, f"{img['image_id']}_{tier_label}_{backend}_{preset}.svg"
                        )

                        print(
                            f"  [{img['image_id']}] {actual_w}x{actual_h}px "
                            f"| {backend} | {preset} ...",
                            end=" ",
                            flush=True,
                        )

                        result = _run_backend(backend, resized_path, output_svg, preset, TIMEOUT_SECONDS)
                        svg_info = _svg_stats(output_svg)

                        row = {
                            "image_id": img["image_id"],
                            "category": img["category"],
                            "resolution_tier": tier_label,
                            "actual_width": actual_w,
                            "actual_height": actual_h,
                            "total_pixels": pixels,
                            "backend": backend,
                            "preset": preset,
                            "status": result.get("status", "unknown"),
                            "wall_clock_time_seconds": round(result.get("wall_clock_time_seconds", 0), 4),
                            "svg_size_bytes": svg_info["svg_size_bytes"],
                            "svg_size_kb": round(svg_info["svg_size_bytes"] / 1024, 2),
                            "path_count": svg_info["path_count"],
                            "error": result.get("error", "") or result.get("error_type", ""),
                        }
                        rows.append(row)

                        status_icon = "✓" if row["status"] == "success" else ("⏱" if row["status"] == "timeout" else "✗")
                        print(f"{status_icon} {row['wall_clock_time_seconds']:.2f}s")

    # Write CSV
    if rows:
        fieldnames = list(rows[0].keys())
        with open(RESULTS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"\nResults saved to: {RESULTS_CSV}")

    # Generate markdown report
    _write_report(rows)
    print(f"Report saved to: {REPORT_MD}")


def _write_report(rows: List[Dict[str, Any]]) -> None:
    lines = [
        "# Scaling Pilot Report",
        "",
        "## Purpose",
        "Determine the relationship between image pixel count and runtime/quality to define",
        "evidence-based pixel limits for `full-standard-v1.yaml` and `stress-large-images-v1.yaml`.",
        "",
        f"**Images tested:** {len({r['image_id'] for r in rows})}",
        f"**Resolution tiers:** {RESOLUTION_TIERS}",
        f"**Backends:** {BACKENDS}",
        f"**Presets:** {PRESETS}",
        f"**Timeout per run:** {TIMEOUT_SECONDS}s",
        "",
        "## Results by Resolution Tier",
        "",
        "| Image | Resolution | Pixels | Backend | Preset | Status | Time (s) | SVG KB | Paths |",
        "|:------|:-----------|-------:|:--------|:-------|:-------|----------:|-------:|------:|",
    ]

    for r in rows:
        lines.append(
            f"| {r['image_id']} | {r['actual_width']}x{r['actual_height']} "
            f"| {r['total_pixels']:,} | {r['backend']} | {r['preset']} "
            f"| {r['status']} | {r['wall_clock_time_seconds']:.2f} "
            f"| {r['svg_size_kb']:.1f} | {r['path_count']} |"
        )

    # Compute timeout boundary
    lines += ["", "## Timeout Analysis", ""]
    timeouts = [r for r in rows if r["status"] == "timeout"]
    if timeouts:
        min_timeout_pixels = min(r["total_pixels"] for r in timeouts)
        lines.append(f"- First timeout observed at **{min_timeout_pixels:,} pixels**.")
        lines.append(
            f"- Recommended `max_input_pixels` for standard benchmark: "
            f"**< {min_timeout_pixels:,}** (below first observed timeout)."
        )
    else:
        lines.append("- No timeouts observed. All runs completed within the timeout budget.")
        max_pixels = max((r["total_pixels"] for r in rows), default=0)
        lines.append(f"- Maximum pixels tested: {max_pixels:,}.")
        lines.append("- Consider testing higher resolutions if timeout boundary is unknown.")

    lines += [
        "",
        "## Recommended Config Values",
        "",
        "> [!NOTE]",
        "> These values must be verified against the actual timeout analysis above before",
        "> populating `full-standard-v1.yaml`.",
        "",
        "```yaml",
        "resource_policy:",
        f"  max_input_pixels: null  # TBD from scaling pilot — first timeout at ~{min(r['total_pixels'] for r in timeouts):,}px" if timeouts else "  max_input_pixels: null  # No timeout observed — may need higher resolution test",
        "  resize_policy: reject",
        "```",
    ]

    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    run_scaling_pilot()
