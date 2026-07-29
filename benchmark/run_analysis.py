import os
import glob
from pathlib import Path

# Find latest result dir
result_dirs = sorted(glob.glob("benchmark/results/*"))
if not result_dirs:
    print("No results found.")
    exit(1)
latest_dir = result_dirs[-1]
runs_file = os.path.join(latest_dir, "runs.jsonl")

print(f"Using runs from {runs_file}")

# 1. Run aggregator
from benchmark.analysis.aggregator import BenchmarkAggregator
agg = BenchmarkAggregator(runs_file)
out_json = os.path.join(latest_dir, "aggregated_results.json")
agg.save(out_json)
print(f"Saved aggregated results to {out_json}")

# 2. Run plot generator (We'll write this script next, but for now we'll just mock it or skip since we don't have one)
import matplotlib.pyplot as plt
import json

with open(out_json) as f:
    data = json.load(f)

# Mock a simple plot for "Quality vs Runtime"
plt.figure(figsize=(10, 6))
# Try to plot if data exists
plt.title("Placeholder Plot")
os.makedirs("paper/figures", exist_ok=True)
plt.savefig("paper/figures/pareto_frontier.png")
plt.savefig("paper/figures/quality_distribution.png")
print("Saved dummy plots to paper/figures/")

# 3. Run generate_snippets.py
import subprocess
subprocess.run(["python3", "paper/scripts/generate_snippets.py", "--runs", runs_file, "--output", "paper/manuscript_snippets.md"])
print("Generated snippets.")
