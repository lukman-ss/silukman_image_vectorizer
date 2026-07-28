import json
from typing import Any, Dict


class CategoryAnalyzer:
    """
    Analyzes and compares benchmark performance across different image categories
    (e.g., logo, icon, illustration, photograph, binary_graphic).
    """

    def __init__(self, aggregated_json_path: str):
        with open(aggregated_json_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        if "by_category" not in self.data:
            raise ValueError(
                "Aggregated data must contain 'by_category' grouping for category analysis."
            )

    def analyze(self) -> Dict[str, Any]:
        report = {
            "interpretation_limitations": (
                "Direct quality comparison across categories is inherently biased. "
                "For example, photographs naturally contain high-frequency details that "
                "lower SSIM scores globally compared to flat-color icons. Therefore, "
                "category comparisons are meant to identify where tools excel or struggle, "
                "not to claim one dataset segment is universally 'better'."
            ),
            "backend_category_profiles": {},
        }

        # We need to analyze per backend + preset
        for backend, presets in self.data["by_category"].items():
            report["backend_category_profiles"][backend] = {}
            for preset, categories in presets.items():
                cat_profile = {
                    "best_quality_category": None,
                    "highest_failure_category": None,
                    "category_metrics": {},
                }

                best_ssim = -1.0
                worst_fail_rate = -1.0

                for cat, stats in categories.items():
                    runs = stats.get("runs", {})
                    total = runs.get("total", 0)
                    fails = runs.get("failed", 0) + runs.get("skipped", 0)
                    fail_rate = (fails / total) if total > 0 else 0.0

                    if fail_rate > worst_fail_rate:
                        worst_fail_rate = fail_rate
                        cat_profile["highest_failure_category"] = cat

                    metrics = stats.get("metrics", {})
                    ssim_median = metrics.get("ssim", {}).get("median", 0.0)

                    if ssim_median > best_ssim:
                        best_ssim = ssim_median
                        cat_profile["best_quality_category"] = cat

                    cat_profile["category_metrics"][cat] = {
                        "failure_rate": fail_rate,
                        "ssim_median": ssim_median,
                        "runtime_median_sec": metrics.get("wall_clock_time_seconds", {}).get(
                            "median"
                        ),
                        "complexity_path_count_median": metrics.get("path_count", {}).get("median"),
                    }

                report["backend_category_profiles"][backend][preset] = cat_profile

        return report

    def save_report(self, output_path: str):
        report = self.analyze()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
