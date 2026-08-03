from unittest.mock import patch
from benchmark.runner.process_utils import _kill_process_tree


@patch("subprocess.run")
@patch("benchmark.runner.process_utils.os.name", "nt")
def test_windows_kill_process_tree_calls_taskkill(mock_run):
    """Verify that on Windows, taskkill is used to terminate the process tree."""
    pid = 12345
    _kill_process_tree(pid)
    mock_run.assert_called_once_with(
        ["taskkill", "/PID", "12345", "/T", "/F"],
        capture_output=True,
        check=False
    )


@patch("subprocess.run")
@patch("benchmark.runner.process_utils.os.name", "nt")
def test_windows_kill_process_tree_ignores_exceptions(mock_run):
    """Verify that exceptions from taskkill are suppressed."""
    mock_run.side_effect = Exception("Simulated error")
    pid = 12345
    # Should not raise
    _kill_process_tree(pid)
