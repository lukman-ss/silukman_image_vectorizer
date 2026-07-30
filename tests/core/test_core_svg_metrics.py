import json


from app.core.postprocessing import calculate_svg_metrics, parse_and_validate_svg
from benchmark.analysis.aggregator import BenchmarkAggregator
from benchmark.analysis.failure_analysis import FailureAnalyzer


def test_svg_metrics(tmp_path):
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <path d="M10 10 H 90 V 90 H 10 Z" fill="#ff0000" stroke="#000000"/>
        <path d="M20 20 H 80 V 80 H 20 Z" fill="#ff0000"/>
        <g><circle cx="50" cy="50" r="40" /></g>
    </svg>"""
    svg_file = tmp_path / "test.svg"
    svg_file.write_text(svg_content)

    root = parse_and_validate_svg(svg_content)
    metrics = calculate_svg_metrics(root)

    assert metrics["path_count"] == 2
    assert metrics["total_elements"] > 2


def test_failure_classification(tmp_path):
    dummy = tmp_path / "dummy.jsonl"
    dummy.write_text("")
    analyzer = FailureAnalyzer(str(dummy))
    assert analyzer._classify_error("Skipped: Category unfair") == "unsupported format"
    assert analyzer._classify_error("Process timed out after 10s") == "backend timeout"
    assert analyzer._classify_error("Potrace CLI is not installed") == "backend unavailable"
    assert analyzer._classify_error("OOM error allocated") == "resource exhaustion"
    assert analyzer._classify_error("missing SVG") == "empty SVG"
    assert analyzer._classify_error("XML parsing failed") == "invalid SVG"
    assert analyzer._classify_error("Failed to decode image") == "decode failure"
    assert analyzer._classify_error("Random exception occurred") == "unknown failure"


def test_result_aggregation(tmp_path):
    runs_file = tmp_path / "runs.jsonl"
    runs_file.write_text(
        json.dumps(
            {
                "status": "success",
                "backend": "silukman",
                "preset": "balanced",
                "quality": {"ssim": 0.9},
                "performance": {"wall_clock_time_seconds": 1.5},
            }
        )
        + "\n"
        + json.dumps(
            {
                "status": "success",
                "backend": "silukman",
                "preset": "balanced",
                "quality": {"ssim": 0.95},
                "performance": {"wall_clock_time_seconds": 2.0},
            }
        )
        + "\n"
        + json.dumps(
            {"status": "failed", "backend": "silukman", "preset": "balanced", "error": "OOM"}
        )
    )

    agg = BenchmarkAggregator(str(runs_file))
    report = agg.aggregate()

    overall = report["overall"]["silukman"]["balanced"]
    assert overall["runs"]["success"] == 2
    assert overall["runs"]["failed"] == 1

    assert overall["metrics"]["ssim"]["mean"] == 0.925
    assert overall["metrics"]["wall_clock_time_seconds"]["median"] == 1.75
