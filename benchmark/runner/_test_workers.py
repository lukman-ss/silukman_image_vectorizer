"""
_test_workers.py

Dummy callables for use by tests/runner/test_process_utils.py.
These run in child processes spawned by run_in_isolated_process().

Must be importable by child processes (no relative imports).
"""
import os
import signal
import subprocess
import time
from typing import Any, Dict


def fast_succeed(output_path: str) -> Dict[str, Any]:
    """Writes a minimal SVG and returns success."""
    with open(output_path, "w") as f:
        f.write("<svg xmlns='http://www.w3.org/2000/svg'></svg>")
    return {"success": True}


def slow_sleep(seconds: float, output_path: str) -> Dict[str, Any]:
    """Sleeps longer than any reasonable timeout — should always be killed."""
    time.sleep(seconds)
    return {"success": True}


def write_then_sleep(output_path: str, seconds: float) -> Dict[str, Any]:
    """Writes a partial SVG then sleeps — tests partial output cleanup."""
    with open(output_path, "w") as f:
        f.write("<svg xmlns='http://www.w3.org/2000/svg'><!-- partial")
    time.sleep(seconds)
    return {"success": True}


def ignore_sigterm_and_sleep(seconds: float, output_path: str) -> Dict[str, Any]:
    """Ignores SIGTERM to force SIGKILL path."""
    if os.name == "posix":
        signal.signal(signal.SIGTERM, signal.SIG_IGN)
    time.sleep(seconds)
    return {"success": True}


def spawn_child_and_sleep(seconds: float, output_path: str) -> Dict[str, Any]:
    """Spawns a grandchild process, then sleeps — tests descendant cleanup."""
    # Launch a grandchild that also sleeps
    subprocess.Popen(
        ["python", "-c", f"import time; time.sleep({seconds})"],
        start_new_session=True,
    )
    time.sleep(seconds)
    return {"success": True}
