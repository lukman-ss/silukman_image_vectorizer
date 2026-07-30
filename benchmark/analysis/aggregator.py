import json
import math
from collections import defaultdict
from typing import cast
from typing import Any, Dict, List, DefaultDict

import numpy as np
import scipy.stats as st


class BenchmarkAggregator:
    """
    Aggregates raw JSONL benchmark runs into statistically sound summaries.
    Methods Documented:
    - Null/Failed Filtering: Failed runs or missing metrics are explicitly ignored for mean/median.
    - Confidence Intervals: Uses t-distribution for small sample sizes, requires at least 2 samples.
    - Repeated-Run Runtime: Median is the primary central tendency measure for runtime and memory to resist outliers.
    - Outlier Detection: Flags observations > 1.5 IQR from the upper/lower quartiles. They are NOT removed, just identified.
    - Spread: Reports standard deviation and IQR (p75 - p25).
    """

    def __init__(self, runs_file: str):
        self.runs_file = runs_file
        self.raw_data = self._load_data()

    def _load_data(self) -> List[Dict[str, Any]]:
        data = []
        with open(self.runs_file, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return data

    def _calculate_stats(self, values: List[float]) -> Dict[str, Any]:
        """Calculates robust descriptive statistics for a list of valid numeric values."""
        clean_vals = [v for v in values if v is not None and not math.isnan(v)]
        n = len(clean_vals)

        if n == 0:
            return {
                "count": 0,
                "mean": None,
                "median": None,
                "std": None,
                "min": None,
                "max": None,
                "p25": None,
                "p75": None,
                "ci_95": None,
            }

        arr = np.array(clean_vals)
        mean = float(np.mean(arr))
        median = float(np.median(arr))
        std = float(np.std(arr, ddof=1)) if n > 1 else 0.0
        vmin = float(np.min(arr))
        vmax = float(np.max(arr))
        p25 = float(np.percentile(arr, 25))
        p75 = float(np.percentile(arr, 75))

        # Confidence interval 95%
        ci_95 = None
        if n > 1 and std > 0:
            ci = st.t.interval(0.95, df=n - 1, loc=mean, scale=std / np.sqrt(n))
            ci_95 = [float(ci[0]), float(ci[1])]

        # Outliers (1.5 * IQR)
        iqr = p75 - p25
        lower_bound = p25 - (1.5 * iqr)
        upper_bound = p75 + (1.5 * iqr)
        outliers = [float(v) for v in arr if v < lower_bound or v > upper_bound]

        return {
            "count": n,
            "mean": mean,
            "median": median,
            "std": std,
            "min": vmin,
            "max": vmax,
            "p25": p25,
            "p75": p75,
            "iqr": iqr,
            "ci_95": ci_95,
            "outliers": outliers,
            "raw_observations": [float(v) for v in arr],  # Retain all per prompt 38
        }

    def aggregate(self) -> Dict[str, Any]:
        # Groupings
        # backend -> preset -> category -> metric -> values
        by_bpc: DefaultDict[Any, DefaultDict[Any, DefaultDict[Any, DefaultDict[Any, list[Any]]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
        by_bp: DefaultDict[Any, DefaultDict[Any, DefaultDict[Any, list[Any]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        by_bpi: DefaultDict[Any, DefaultDict[Any, DefaultDict[Any, DefaultDict[Any, list[Any]]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))

        # Track success/failures
        # backend -> preset -> category -> status_counts
        status_bpc: DefaultDict[Any, DefaultDict[Any, DefaultDict[Any, Dict[str, int]]]] = defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(lambda: {"total": 0, "success": 0, "failed": 0, "skipped": 0})
            )
        )
        status_bp: DefaultDict[Any, DefaultDict[Any, Dict[str, int]]] = defaultdict(
            lambda: defaultdict(lambda: {"total": 0, "success": 0, "failed": 0, "skipped": 0})
        )
        status_bpi: DefaultDict[Any, DefaultDict[Any, DefaultDict[Any, Dict[str, int]]]] = defaultdict(
            lambda: defaultdict(
                lambda: defaultdict(lambda: {"total": 0, "success": 0, "failed": 0, "skipped": 0})
            )
        )

        for record in self.raw_data:
            b = record.get("backend", "unknown")
            p = record.get("preset", "unknown")
            c = record.get("category", "all")
            i = record.get("image_id", "unknown")

            st = record.get("status", "unknown")

            status_bp[b][p]["total"] += 1
            status_bpc[b][p][c]["total"] += 1
            status_bpi[b][p][i]["total"] += 1
            if st in ["success", "failed", "skipped"]:
                status_bp[b][p][st] += 1
                status_bpc[b][p][c][st] += 1
                status_bpi[b][p][i][st] += 1

            if st != "success":
                continue

            # Collect metrics if success
            metrics = {}
            if "quality" in record:
                metrics.update(record["quality"])
            if "complexity" in record:
                metrics.update(record["complexity"])
            if "performance" in record:
                metrics.update(record["performance"])
            if "vectorize_metadata" in record and "performance" in record["vectorize_metadata"]:
                # Sometimes performance is nested here depending on backend adapter
                metrics.update(record["vectorize_metadata"]["performance"])

            for m_key, m_val in metrics.items():
                if isinstance(m_val, (int, float)):
                    by_bpc[b][p][c][m_key].append(m_val)
                    by_bpi[b][p][i][m_key].append(m_val)
                    by_bp[b][p][m_key].append(m_val)

        # Build report
        report: Dict[str, Any] = {"overall": {}, "by_category": {}, "by_image": {}}

        # Aggregate overall (Backend + Preset)
        for b, presets in by_bp.items():
            report["overall"][b] = {}
            for p, metrics in presets.items():
                rep: Dict[str, Any] = {"runs": status_bp[b][p], "warnings": [], "metrics": {}}
                if status_bp[b][p]["success"] < 3:
                    rep["warnings"].append("Low run count for robust statistics (n < 3)")

                for m_key, vals in metrics.items():
                    rep["metrics"][m_key] = self._calculate_stats(vals)
                report["overall"][b][p] = rep

        # Aggregate by Category (Backend + Preset + Category)
        for b, presets in by_bpc.items():  # type: ignore[assignment] # complex typing/external library
            if b not in report["by_category"]:
                report["by_category"][b] = cast(Any, {})
            for p, categories in cast(Any, presets).items():
                report["by_category"][b][p] = cast(Any, {})
                for c, metrics in categories.items():
                    rep_cat: Dict[str, Any] = {"runs": status_bpc[b][p][c], "metrics": {}}
                    for m_key, vals in metrics.items():
                        rep_cat["metrics"][m_key] = self._calculate_stats(vals)
                    report["by_category"][b][p][c] = cast(Any, rep_cat)

        # Aggregate by Image (Backend + Preset + Image)
        for b, presets in by_bpi.items():  # type: ignore[assignment] # complex typing/external library
            if b not in report["by_image"]:
                report["by_image"][b] = cast(Any, {})
            for p, images in cast(Any, presets).items():
                report["by_image"][b][p] = cast(Any, {})
                for i, metrics in images.items():
                    rep_img: Dict[str, Any] = {"runs": status_bpi[b][p][i], "metrics": {}}
                    for m_key, vals in metrics.items():
                        rep_img["metrics"][m_key] = self._calculate_stats(vals)
                    report["by_image"][b][p][i] = cast(Any, rep_img)

        return report

    def save(self, output_path: str):
        report = self.aggregate()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
