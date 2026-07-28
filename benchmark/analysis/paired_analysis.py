import json
import math
from typing import Any, Dict, List, Tuple

import numpy as np
import scipy.stats as st

# Metrics where higher is better
HIGHER_IS_BETTER = {
    "psnr",
    "ssim",
    "histogram_correlation",
    "edge_f1",
    "edge_precision",
    "edge_recall",
    "success",
}


class PairedComparison:
    """
    Performs paired statistical comparisons between two configurations
    (e.g., Silukman vs VTracer Direct) on the exact same dataset of images.
    """

    def __init__(self, aggregated_json_path: str):
        with open(aggregated_json_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        if "by_image" not in self.data:
            raise ValueError(
                "Aggregated data must contain 'by_image' grouping for paired analysis."
            )

    def _extract_image_metric(self, backend: str, preset: str, metric: str) -> Dict[str, float]:
        """Extracts the median metric value per image for a specific configuration."""
        img_data = self.data["by_image"].get(backend, {}).get(preset, {})
        res = {}
        for img_id, stats in img_data.items():
            # Check if successful
            if stats.get("runs", {}).get("success", 0) > 0:
                metric_stats = stats.get("metrics", {}).get(metric)
                if metric_stats and metric_stats.get("median") is not None:
                    res[img_id] = metric_stats["median"]
        return res

    def compare(
        self, config_a: Tuple[str, str], config_b: Tuple[str, str], metric: str
    ) -> Dict[str, Any]:
        """
        Compares Config B against Config A.
        Returns positive delta if B is 'higher' than A.
        'Win' means B is better than A based on the metric's direction.
        """
        backend_a, preset_a = config_a
        backend_b, preset_b = config_b

        vals_a = self._extract_image_metric(backend_a, preset_a, metric)
        vals_b = self._extract_image_metric(backend_b, preset_b, metric)

        common_images = set(vals_a.keys()).intersection(set(vals_b.keys()))

        if len(common_images) == 0:
            return {"error": "No common successful images found for paired comparison."}

        deltas = []
        wins_b = 0
        losses_b = 0
        ties = 0

        higher_is_better = metric in HIGHER_IS_BETTER

        per_image_details = {}

        for img in common_images:
            val_a = vals_a[img]
            val_b = vals_b[img]

            # Delta = B - A
            delta = val_b - val_a
            deltas.append(delta)

            per_image_details[img] = {"A": val_a, "B": val_b, "delta": delta}

            if math.isclose(delta, 0, abs_tol=1e-9):
                ties += 1
            else:
                if higher_is_better:
                    if delta > 0:
                        wins_b += 1
                    else:
                        losses_b += 1
                else:  # lower is better
                    if delta < 0:
                        wins_b += 1
                    else:
                        losses_b += 1

        deltas_arr = np.array(deltas)
        mean_delta = float(np.mean(deltas_arr))
        median_delta = float(np.median(deltas_arr))
        std_delta = float(np.std(deltas_arr, ddof=1)) if len(deltas_arr) > 1 else 0.0

        # Effect size (Cohen's d for paired samples)
        effect_size = None
        if std_delta > 0:
            effect_size = mean_delta / std_delta

        # Wilcoxon signed-rank test (non-parametric)
        # Only run if N >= 10 for meaningful results, and not all deltas are 0
        p_value = None
        test_valid = False
        wilcoxon_stat = None

        non_zero_deltas = [d for d in deltas if not math.isclose(d, 0, abs_tol=1e-9)]
        if len(non_zero_deltas) >= 10:
            try:
                # wilcoxon requires non-zero differences
                res = st.wilcoxon(non_zero_deltas)
                wilcoxon_stat = float(res.statistic)
                p_value = float(res.pvalue)
                test_valid = True
            except Exception:
                pass

        return {
            "config_a": {"backend": backend_a, "preset": preset_a},
            "config_b": {"backend": backend_b, "preset": preset_b},
            "metric": metric,
            "higher_is_better": higher_is_better,
            "common_sample_size": len(common_images),
            "wins_for_b": wins_b,
            "losses_for_b": losses_b,
            "ties": ties,
            "mean_delta": mean_delta,
            "median_delta": median_delta,
            "std_delta": std_delta,
            "effect_size_cohens_d": effect_size,
            "significance_test": {
                "test_name": "Wilcoxon signed-rank test",
                "valid": test_valid,
                "statistic": wilcoxon_stat,
                "p_value": p_value,
                "note": (
                    "Not run if sample size < 10 or zero variance" if not test_valid else "Valid"
                ),
            },
            "per_image_deltas": per_image_details,
        }

    def save_report(
        self,
        config_a: Tuple[str, str],
        config_b: Tuple[str, str],
        metrics: List[str],
        output_path: str,
    ):
        report = {}
        for m in metrics:
            report[m] = self.compare(config_a, config_b, m)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
