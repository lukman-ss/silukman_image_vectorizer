import sys
import pytest
from benchmark.runner.process_utils import run_isolated_process, ProcessExecutionError

def test_successful_executable():
    # 'python -c "print(\'hello\')"' should succeed
    cmd = [sys.executable, "-c", "print('hello')"]
    exit_code, stdout, stderr = run_isolated_process(cmd, timeout_sec=5)
    assert exit_code == 0
    assert "hello" in stdout

def test_failed_executable():
    # Executable doesn't exist
    cmd = ["/path/to/some/nonexistent/binary_xyz_123"]
    with pytest.raises(ProcessExecutionError) as exc:
        run_isolated_process(cmd, timeout_sec=5)
    assert "Executable not found" in str(exc.value)

def test_dummy_timeout():
    # Process that sleeps forever
    cmd = [sys.executable, "-c", "import time; time.sleep(10)"]
    with pytest.raises(TimeoutError) as exc:
        run_isolated_process(cmd, timeout_sec=1)
    assert "timed out after 1" in str(exc.value)
