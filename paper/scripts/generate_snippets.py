#!/usr/bin/env python3
"""
Generate manuscript snippets from benchmark results.
Extracts dataset count, success rate, mean/median, baseline ranking,
preset trade-offs, category results, and generates table/figure references.

This script outputs factual markdown snippets and avoids interpretive claims.
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict
import statistics


def load_runs(jsonl_path):
    runs = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                runs.append(json.loads(line))
    return runs


def compute_dataset_count(runs):
    images = set(r.get('image_id') for r in runs if 'image_id' in r)
    return len(images)


def compute_success_rate(runs):
    if not runs:
        return 0.0
    success = sum(1 for r in runs if r.get('status') == 'success')
    return (success / len(runs)) * 100


def compute_metrics_by_group(runs, group_key, metric_category, metric_name):
    grouped = defaultdict(list)
    for r in runs:
        if r.get('status') == 'success' and metric_category in r:
            val = r[metric_category].get(metric_name)
            if val is not None:
                grouped[r.get(group_key, 'unknown')].append(val)

    results = {}
    for g, vals in grouped.items():
        if vals:
            results[g] = {
                'count': len(vals),
                'mean': statistics.mean(vals),
                'median': statistics.median(vals)
            }
    return results


def generate_snippets(runs, output_path=None):
    if not runs:
        snippets = "No benchmark data available to generate snippets.\n"
        if output_path:
            Path(output_path).write_text(snippets)
        else:
            print(snippets)
        return

    dataset_count = compute_dataset_count(runs)
    success_rate = compute_success_rate(runs)

    # Analyze by backend
    backend_quality = compute_metrics_by_group(runs, 'backend', 'quality', 'ssim')
    # Rank backends by mean quality
    ranked_backends = sorted(backend_quality.items(), key=lambda x: x[1]['mean'], reverse=True)

    # Analyze presets for Silukman
    silukman_runs = [r for r in runs if r.get('backend') == 'silukman']
    preset_quality = compute_metrics_by_group(silukman_runs, 'preset', 'quality', 'ssim')
    preset_runtime = compute_metrics_by_group(silukman_runs, 'preset', 'performance', 'duration_seconds')

    # Analyze by category
    category_quality = compute_metrics_by_group(runs, 'category', 'quality', 'ssim')

    lines = []
    lines.append("## Generated Manuscript Snippets")
    lines.append("\n### Dataset and Success Rate")
    lines.append(f"The evaluation dataset consisted of {dataset_count} unique images.")
    lines.append(f"Across all configured conditions, the overall execution success rate was {success_rate:.1f}%.")

    lines.append("\n### Baseline Ranking (Factual)")
    lines.append("Based on the primary quality metric, the evaluated backends achieved the following mean scores:")
    for b, stats in ranked_backends:
        lines.append(f"- {b}: mean = {stats['mean']:.4f}, median = {stats['median']:.4f} (n={stats['count']})")

    lines.append("\n### Preset Trade-offs (Silukman)")
    lines.append("For the Silukman backend, the presets yielded the following measurements:")
    for p, q_stats in preset_quality.items():
        r_stats = preset_runtime.get(p, {'mean': 0.0, 'median': 0.0})
        lines.append(f"- {p}: quality mean = {q_stats['mean']:.4f}, runtime mean = {r_stats['mean']:.4f}s")

    lines.append("\n### Category Results")
    lines.append("Performance observed across dataset categories:")
    for c, stats in category_quality.items():
        lines.append(f"- {c}: mean quality = {stats['mean']:.4f}, median = {stats['median']:.4f}")

    lines.append("\n### Table & Figure References")
    lines.append("- **Table 10**: Summary of dataset dimensions, categories, and execution status.")
    lines.append("- **Table 11**: Overall quality metrics across all backends and presets.")
    lines.append("- **Table 13**: End-to-end runtime distributions.")
    lines.append("- **Figure 8**: Distribution of the primary quality metric by backend.")
    lines.append("- **Figure 14**: Pareto frontier analysis comparing quality versus SVG size.")

    snippet_text = "\n".join(lines)

    if output_path:
        Path(output_path).write_text(snippet_text)
        print(f"Snippets written to {output_path}")
    else:
        print(snippet_text)


def main():
    parser = argparse.ArgumentParser(description="Generate manuscript snippets from runs.jsonl")
    parser.add_argument("--runs", type=str, default="benchmark/runs.jsonl", help="Path to runs.jsonl")
    parser.add_argument("--output", type=str, help="Output markdown file for snippets")
    args = parser.parse_args()

    if Path(args.runs).exists():
        runs = load_runs(args.runs)
        generate_snippets(runs, args.output)
    else:
        print(f"Warning: {args.runs} not found. Awaiting benchmark completion.")
        # Generate empty placeholder logic or just exit
        generate_snippets([], args.output)


if __name__ == '__main__':
    main()
