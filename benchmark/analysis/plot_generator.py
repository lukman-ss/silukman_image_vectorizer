import json
import os

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


class PlotGenerator:
    def __init__(self, exp_dir: str):
        self.exp_dir = exp_dir
        self.aggregated_file = os.path.join(exp_dir, "aggregated.json")
        with open(self.aggregated_file, "r", encoding="utf-8") as f:
            self.agg_data = json.load(f)

        self.output_dir = os.path.join(exp_dir, "plots")
        os.makedirs(self.output_dir, exist_ok=True)

        # Set publication-ready style
        sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)
        plt.rcParams.update(
            {
                "figure.dpi": 300,
                "savefig.dpi": 300,
                "axes.titlesize": 14,
                "axes.labelsize": 12,
                "pdf.fonttype": 42,  # TrueType for publication
                "ps.fonttype": 42,
            }
        )

    def _save_fig(self, filename: str):
        path = os.path.join(self.output_dir, filename)
        plt.savefig(f"{path}.png", bbox_inches="tight")
        plt.savefig(f"{path}.pdf", bbox_inches="tight")
        plt.close()

    def plot_quality_vs_complexity(self, quality_metric="ssim", comp_metric="svg_bytes"):
        # Plot quality vs file size or path count
        points = []
        for backend, presets in self.agg_data.get("overall", {}).items():
            for preset, stats in presets.items():
                m_q = stats.get("metrics", {}).get(quality_metric, {})
                m_c = stats.get("metrics", {}).get(comp_metric, {})
                if m_q.get("median") is not None and m_c.get("median") is not None:
                    points.append(
                        {
                            "Backend": backend,
                            "Preset": preset,
                            "Quality": m_q["median"],
                            "Complexity": (
                                m_c["median"] / 1024
                                if comp_metric == "svg_bytes"
                                else m_c["median"]
                            ),
                        }
                    )

        if not points:
            return
        df = pd.DataFrame(points)

        plt.figure(figsize=(8, 6))
        sns.scatterplot(
            data=df, x="Complexity", y="Quality", hue="Backend", style="Preset", s=100
        )

        c_label = "SVG Size (KB)" if comp_metric == "svg_bytes" else "Path Count"
        q_label = quality_metric.upper()

        plt.title(f"{q_label} vs {c_label}")
        plt.xlabel(c_label)
        plt.ylabel(f"Median {q_label}")
        # Don't truncate y-axis artificially if comparing quality
        plt.ylim(0, 1.05) if "ssim" in quality_metric else None

        self._save_fig(f"{quality_metric}_vs_{comp_metric}")

    def plot_runtime_comparison(self):
        records = []
        for backend, presets in self.agg_data.get("overall", {}).items():
            for preset, stats in presets.items():
                rt = stats.get("metrics", {}).get("wall_clock_time_seconds", {})
                if rt.get("median") is not None:
                    records.append(
                        {
                            "Backend": backend,
                            "Preset": preset,
                            "Runtime (s)": rt["median"],
                            "IQR": rt.get("iqr", 0),
                        }
                    )

        if not records:
            return
        df = pd.DataFrame(records)

        plt.figure(figsize=(10, 6))
        sns.barplot(data=df, x="Backend", y="Runtime (s)", hue="Preset")
        plt.title("Median Runtime by Backend and Preset")
        plt.ylabel("Runtime (Seconds)")

        self._save_fig("runtime_comparison")

    def plot_failure_rates(self):
        fail_file = os.path.join(self.exp_dir, "failure_report.json")
        if not os.path.exists(fail_file):
            return
        with open(fail_file, "r") as f:
            fail_data = json.load(f)

        classes = []
        counts = []
        for cls, data in fail_data.get("by_class", {}).items():
            if data["count"] > 0:
                classes.append(cls)
                counts.append(data["count"])

        if not classes:
            return

        plt.figure(figsize=(10, 6))
        sns.barplot(x=counts, y=classes, palette="Reds_r")
        plt.title("Failure Breakdown")
        plt.xlabel("Count")

        self._save_fig("failure_rates")

    def generate_all(self):
        self.plot_quality_vs_complexity("ssim", "svg_bytes")
        self.plot_quality_vs_complexity("edge_f1", "path_count")
        self.plot_runtime_comparison()
        self.plot_failure_rates()
        print(f"Plots generated in {self.output_dir}")
