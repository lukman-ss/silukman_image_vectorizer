import json
import time

import pytest

from benchmark.evaluation.performance_metrics import PerformanceTracker


def dummy_vectorization(delay: float, fail: bool = False, fail_times: int = 0):
    """Simulates a core vectorization function."""
    if not hasattr(dummy_vectorization, "fail_counter"):
        dummy_vectorization.fail_counter = 0  # type: ignore[attr-defined] # complex typing/external library

    time.sleep(delay)

    if fail:
        raise RuntimeError("Fatal vectorization error")

    if dummy_vectorization.fail_counter < fail_times:  # type: ignore[attr-defined] # complex typing/external library
        dummy_vectorization.fail_counter += 1  # type: ignore[attr-defined] # complex typing/external library
        raise RuntimeError("Transient error")

    # Reset for next tests
    dummy_vectorization.fail_counter = 0  # type: ignore[attr-defined] # complex typing/external library


@pytest.fixture
def dummy_files(tmp_path):
    input_f = tmp_path / "in.png"
    input_f.write_bytes(b"0" * 1024)  # 1KB

    output_f = tmp_path / "out.svg"
    output_f.write_bytes(b"1" * 512)  # 512B

    return str(input_f), str(output_f)


def test_performance_success(dummy_files):
    in_f, out_f = dummy_files
    tracker = PerformanceTracker()

    # Warmup
    tracker.warmup(dummy_vectorization, 0.01)

    # Measure
    result = tracker.measure(
        func=dummy_vectorization, input_file=in_f, output_file=out_f, delay=0.1
    )

    assert result["success"] is True
    assert result["wall_clock_time_seconds"] >= 0.1
    assert result["input_bytes"] == 1024
    assert result["output_bytes"] == 512
    assert result["throughput_bytes_per_second"] > 0
    assert result["retry_count"] == 0
    assert result["error"] is None

    json.dumps(result)


def test_performance_retry(dummy_files):
    in_f, out_f = dummy_files
    tracker = PerformanceTracker()

    # Needs to fail once, succeed on second try
    result = tracker.measure(
        func=dummy_vectorization,
        input_file=in_f,
        output_file=out_f,
        retries=2,
        delay=0.01,
        fail_times=1,
    )

    assert result["success"] is True
    assert result["retry_count"] == 1
    assert result["error"] is None


def test_performance_failure(dummy_files):
    in_f, out_f = dummy_files
    tracker = PerformanceTracker()

    result = tracker.measure(
        func=dummy_vectorization,
        input_file=in_f,
        output_file=out_f,
        retries=1,
        delay=0.01,
        fail=True,
    )

    assert result["success"] is False
    assert result["retry_count"] == 1
    assert "Fatal" in result["error"]
    assert result["throughput_bytes_per_second"] == 0.0
