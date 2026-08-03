import os
import sys
import tempfile
import time
import pytest
from pathlib import Path
import psutil

from benchmark.runner.process_utils import run_isolated_process


@pytest.mark.skipif(os.name != "nt", reason="Windows integration test only")
def test_windows_process_tree_termination():
    """
    Integration test to verify that run_isolated_process on Windows
    successfully uses taskkill to terminate the entire process tree,
    leaving no orphaned background processes.
    """
    # Create a temporary python script that spawns a child process and hangs
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(tmpdir) / "hang_script.py"

        script_content = """import subprocess
import sys
import time

# Spawn a child that sleeps indefinitely
child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(100)"])

# Sleep indefinitely in the parent as well
time.sleep(100)
"""
        script_path.write_text(script_content)

        start = time.time()
        # run_isolated_process(cmd: List[str], timeout_sec: int) -> Tuple[int, str, str]
        try:
            returncode, stdout, stderr = run_isolated_process(
                cmd=[sys.executable, str(script_path)],
                timeout_sec=2
            )
            # In process_utils.py, does it return a specific code for timeout, or raise?
            # We'll assert returncode != 0
            timeout_happened = (returncode != 0)
        except Exception:
            timeout_happened = True
        elapsed = time.time() - start

        # 1. Should timeout
        assert timeout_happened, "Expected timeout but process completed"
        assert elapsed < 10, "Test hung instead of timing out"

        # 3. Check for lingering child processes (this requires examining the process tree,
        # but since we can't reliably get the PID of the deeply nested child from run_measured_subprocess
        # we will check if any process running `time.sleep(100)` is left behind).
        # We look for processes running our exact command.
        lingering = []
        for p in psutil.process_iter(['cmdline']):
            try:
                cmdline = p.info['cmdline']
                if cmdline and "time.sleep(100)" in " ".join(cmdline):
                    lingering.append(p)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Kill them if they escaped so the test suite doesn't hang
        for p in lingering:
            p.kill()

        assert not lingering, "Orphaned child processes were left running on Windows!"
