import json
from typing import Any, Dict, List


class FailureAnalyzer:
    """
    Classifies and analyzes failed or skipped benchmark runs based on the raw JSONL.
    Never removes failed cases from the report; transparency is strictly required.
    """

    ERROR_CLASSES = [
        "unsupported format",
        "decode failure",
        "preprocessing failure",
        "backend unavailable",
        "backend timeout",
        "invalid SVG",
        "empty SVG",
        "rasterization failure",
        "metric failure",
        "resource exhaustion",
        "unknown failure",
    ]

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

    def _classify_error(self, err_string: str) -> str:
        if not err_string:
            return "unknown failure"

        lower_err = err_string.lower()

        if "category" in lower_err and "unfair" in lower_err:
            return "unsupported format"
        if "timeout" in lower_err or "time out" in lower_err or "timed out" in lower_err:
            return "backend timeout"
        if (
            "not installed" in lower_err
            or "not available" in lower_err
            or "skipped: backend" in lower_err
        ):
            return "backend unavailable"
        if "memory" in lower_err or "oom" in lower_err or "exhausted" in lower_err:
            return "resource exhaustion"
        if "empty svg" in lower_err or "missing svg" in lower_err:
            return "empty SVG"
        if "xml" in lower_err or "parse" in lower_err:
            return "invalid SVG"
        if "rasterize" in lower_err or "qsvg" in lower_err:
            return "rasterization failure"
        if "metric" in lower_err:
            return "metric failure"
        if "preprocess" in lower_err:
            return "preprocessing failure"
        if "decode" in lower_err or "read image" in lower_err:
            return "decode failure"

        return "unknown failure"

    def analyze(self) -> Dict[str, Any]:
        report = {
            "total_runs": len(self.raw_data),
            "total_failures": 0,
            "failure_rate_percent": 0.0,
            "by_class": {cls: {"count": 0, "examples": []} for cls in self.ERROR_CLASSES},
        }

        for record in self.raw_data:
            if record.get("status") in ["failed", "skipped"] or len(record.get("errors", [])) > 0:
                report["total_failures"] += 1

                # Use the first error for classification
                errs = record.get("errors", [])
                err_msg = errs[0] if errs else str(record.get("error"))

                cls = self._classify_error(err_msg)
                report["by_class"][cls]["count"] += 1

                # Save up to 5 examples per class
                if len(report["by_class"][cls]["examples"]) < 5:
                    report["by_class"][cls]["examples"].append(
                        {
                            "run_id": record.get("run_id"),
                            "image_id": record.get("image_id"),
                            "backend": record.get("backend"),
                            "preset": record.get("preset"),
                            "raw_error": err_msg,
                        }
                    )

        if report["total_runs"] > 0:
            report["failure_rate_percent"] = round(
                (report["total_failures"] / report["total_runs"]) * 100, 2
            )

        return report

    def save_report(self, output_path: str):
        report = self.analyze()
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
