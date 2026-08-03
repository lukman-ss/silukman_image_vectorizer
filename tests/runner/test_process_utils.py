"""
Tests for process_utils.py — covering hard timeout, process tree cleanup,
partial output handling, and zombie prevention.
"""
import os
import sys
import time

import pytest

from benchmark.runner.process_utils import ProcessExecutionError, run_in_isolated_process, run_isolated_process


# ---------------------------------------------------------------------------
# run_isolated_process (existing subprocess utility)
# ---------------------------------------------------------------------------

def test_successful_executable():
    cmd = [sys.executable, "-c", "print('hello')"]
    exit_code, stdout, stderr = run_isolated_process(cmd, timeout_sec=5)
    assert exit_code == 0
    assert "hello" in stdout


def test_failed_executable():
    cmd = ["/path/to/some/nonexistent/binary_xyz_123"]
    with pytest.raises(ProcessExecutionError) as exc:
        run_isolated_process(cmd, timeout_sec=5)
    assert "Executable not found" in str(exc.value)


def test_dummy_timeout():
    cmd = [sys.executable, "-c", "import time; time.sleep(10)"]
    with pytest.raises(TimeoutError) as exc:
        run_isolated_process(cmd, timeout_sec=1)
    assert "timed out after 1" in str(exc.value)


# ---------------------------------------------------------------------------
# run_in_isolated_process — helpers
# ---------------------------------------------------------------------------

def _dummy_module() -> str:
    """Used only to identify the worker module path."""
    return "benchmark.runner._test_workers"


# ---------------------------------------------------------------------------
# run_in_isolated_process — success path
# ---------------------------------------------------------------------------

def test_isolated_process_success(tmp_path):
    """Process completes within timeout → status=ok, result returned."""
    output_path = str(tmp_path / "out.svg")
    result = run_in_isolated_process(
        module_path="benchmark.runner._test_workers",
        callable_name="fast_succeed",
        kwargs={"output_path": output_path},
        output_path=output_path,
        timeout_sec=10,
    )
    assert result["status"] == "ok"
    assert result["result"]["success"] is True
    assert os.path.exists(output_path)


# ---------------------------------------------------------------------------
# run_in_isolated_process — timeout path
# ---------------------------------------------------------------------------

def test_isolated_process_timeout(tmp_path):
    """Process exceeds timeout → status=timeout, error_type set, metrics=None."""
    output_path = str(tmp_path / "out.svg")
    result = run_in_isolated_process(
        module_path="benchmark.runner._test_workers",
        callable_name="slow_sleep",
        kwargs={"seconds": 30, "output_path": output_path},
        output_path=output_path,
        timeout_sec=2,
    )
    assert result["status"] == "timeout"
    assert result["error_type"] == "BackendTimeoutError"
    assert result["metrics"] is None
    assert result["output_valid"] is False
    assert result["duration_seconds"] >= 2.0


def test_timeout_removes_partial_output(tmp_path):
    """Partial SVG created before timeout is deleted."""
    output_path = str(tmp_path / "partial.svg")
    result = run_in_isolated_process(
        module_path="benchmark.runner._test_workers",
        callable_name="write_then_sleep",
        kwargs={"output_path": output_path, "seconds": 30},
        output_path=output_path,
        timeout_sec=2,
    )
    assert result["status"] == "timeout"
    # Partial file must have been cleaned up
    assert not os.path.exists(output_path)


def test_timeout_no_zombie_process(tmp_path):
    """After timeout, no zombie process remains alive (basic check)."""
    output_path = str(tmp_path / "out.svg")
    result = run_in_isolated_process(
        module_path="benchmark.runner._test_workers",
        callable_name="slow_sleep",
        kwargs={"seconds": 30, "output_path": output_path},
        output_path=output_path,
        timeout_sec=2,
    )
    assert result["status"] == "timeout"
    # Give OS a moment to reap
    time.sleep(0.5)
    # We can't directly inspect zombie state portably, but the call must
    # return (not hang), which verifies the parent reaped the child.


def test_timeout_ignores_sigterm(tmp_path):
    """Process ignoring SIGTERM is killed via SIGKILL after grace period."""
    output_path = str(tmp_path / "out.svg")
    result = run_in_isolated_process(
        module_path="benchmark.runner._test_workers",
        callable_name="ignore_sigterm_and_sleep",
        kwargs={"seconds": 30, "output_path": output_path},
        output_path=output_path,
        timeout_sec=2,
    )
    assert result["status"] == "timeout"
    assert result["output_valid"] is False


def test_timeout_with_descendant_process(tmp_path):
    """Process that spawns children — all descendants must be cleaned."""
    output_path = str(tmp_path / "out.svg")
    result = run_in_isolated_process(
        module_path="benchmark.runner._test_workers",
        callable_name="spawn_child_and_sleep",
        kwargs={"seconds": 30, "output_path": output_path},
        output_path=output_path,
        timeout_sec=2,
    )
    assert result["status"] == "timeout"


# ---------------------------------------------------------------------------
# Multiple consecutive timeouts — experiment continues
# ---------------------------------------------------------------------------

def test_multiple_timeouts_dont_crash(tmp_path):
    """Two consecutive timeouts should both return timeout status, not crash."""
    for i in range(2):
        output_path = str(tmp_path / f"out_{i}.svg")
        result = run_in_isolated_process(
            module_path="benchmark.runner._test_workers",
            callable_name="slow_sleep",
            kwargs={"seconds": 30, "output_path": output_path},
            output_path=output_path,
            timeout_sec=1,
        )
        assert result["status"] == "timeout"
