import json
from typing import Any, Dict, List


class ParetoFrontier:
    """
    Identifies Pareto-efficient configurations based on trade-offs
    between two competing metrics (e.g., SSIM vs SVG Size).

    A configuration is Pareto-efficient if no other configuration
    is strictly better in one metric without being worse in the other.

    Disclaimer: There is no single "best" preset for all needs. The
    Pareto frontier simply highlights the optimal configurations for
    specific trade-off preferences.
    """

    def __init__(self, aggregated_json_path: str):
        with open(aggregated_json_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        if "overall" not in self.data:
            raise ValueError("Aggregated data must contain 'overall' grouping for Pareto analysis.")

    def _extract_points(self, metric_x: str, metric_y: str) -> List[Dict[str, Any]]:
        points = []
        for backend, presets in self.data["overall"].items():
            for preset, stats in presets.items():
                mx = stats.get("metrics", {}).get(metric_x)
                my = stats.get("metrics", {}).get(metric_y)

                # Use median for robustness
                if mx and my and mx.get("median") is not None and my.get("median") is not None:
                    points.append(
                        {
                            "backend": backend,
                            "preset": preset,
                            "x_val": mx["median"],
                            "y_val": my["median"],
                        }
                    )
        return points

    def find_frontier(
        self, metric_x: str, metric_y: str, x_maximize: bool, y_maximize: bool
    ) -> Dict[str, Any]:
        points = self._extract_points(metric_x, metric_y)

        if not points:
            return {"error": "No valid data points found for the given metrics."}

        # A point A dominates point B if it is better or equal in all metrics,
        # and strictly better in at least one metric.

        def is_better_or_equal(a_val, b_val, maximize: bool) -> bool:
            return a_val >= b_val if maximize else a_val <= b_val  # type: ignore[no-any-return] # complex typing/external library

        def is_strictly_better(a_val, b_val, maximize: bool) -> bool:
            return a_val > b_val if maximize else a_val < b_val  # type: ignore[no-any-return] # complex typing/external library

        frontier = []
        dominated = []

        for i, pt_a in enumerate(points):
            is_dominated = False
            for j, pt_b in enumerate(points):
                if i == j:
                    continue

                # Check if B dominates A
                b_better_eq_x = is_better_or_equal(pt_b["x_val"], pt_a["x_val"], x_maximize)
                b_better_eq_y = is_better_or_equal(pt_b["y_val"], pt_a["y_val"], y_maximize)
                b_strict_x = is_strictly_better(pt_b["x_val"], pt_a["x_val"], x_maximize)
                b_strict_y = is_strictly_better(pt_b["y_val"], pt_a["y_val"], y_maximize)

                if b_better_eq_x and b_better_eq_y and (b_strict_x or b_strict_y):
                    is_dominated = True
                    break

            if not is_dominated:
                frontier.append(pt_a)
            else:
                dominated.append(pt_a)

        # Sort frontier for nice visualization (e.g., sorted by x)
        frontier.sort(key=lambda p: p["x_val"], reverse=x_maximize)

        return {
            "analysis": f"{metric_x} vs {metric_y}",
            "x_axis": {"metric": metric_x, "objective": "maximize" if x_maximize else "minimize"},
            "y_axis": {"metric": metric_y, "objective": "maximize" if y_maximize else "minimize"},
            "disclaimer": "There is no single best preset. The Pareto frontier shows the optimal trade-offs. Choose based on your priority.",
            "pareto_efficient_configurations": frontier,
            "dominated_configurations": dominated,
        }

    def analyze_tradeoffs(self, output_path: str):
        tradeoffs = [
            # High SSIM vs Low SVG Bytes
            ("ssim", "svg_bytes", True, False),
            # High Edge F1 vs Low Path Count
            ("edge_f1", "path_count", True, False),
            # Low RMSE vs Low Runtime
            ("rmse", "wall_clock_time_seconds", False, False),
            # High PSNR vs Low Element Count
            ("psnr", "element_count", True, False),
        ]

        report = {}
        for mx, my, max_x, max_y in tradeoffs:
            key = f"{mx}_vs_{my}"
            report[key] = self.find_frontier(mx, my, max_x, max_y)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
