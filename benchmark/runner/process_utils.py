import json
import multiprocessing
import os
import signal
import subprocess
import tempfile
import time
from typing import Any, Dict, List, Optional, Tuple


class ProcessExecutionError(Exception):
    def __init__(self, message: str, exit_code: int = -1, stdout: str = "", stderr: str = ""):
        super().__init__(message)
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr


def _kill_process_tree(pid: int, grace_seconds: float = 3.0) -> None:
    """
    Terminate a process and all its descendants.

    Strategy (POSIX):
      1. Send SIGTERM to the entire process group.
      2. Wait up to grace_seconds.
      3. Send SIGKILL to the process group if still alive.

    Guaranteed not to raise.
    """
    if os.name != "posix":
        try:
            import subprocess
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                capture_output=True,
                check=False
            )
        except Exception:
            pass
        return

    try:
        pgid = os.getpgid(pid)
    except (ProcessLookupError, PermissionError):
        return

    # SIGTERM to whole group
    try:
        os.killpg(pgid, signal.SIGTERM)
    except Exception:
        pass

    # Grace period
    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        try:
            os.killpg(pgid, 0)  # probe
            time.sleep(0.1)
        except (ProcessLookupError, PermissionError):
            return  # group is gone

    # SIGKILL fallback
    try:
        os.killpg(pgid, signal.SIGKILL)
    except Exception:
        pass

    # Reap any remaining zombies
    try:
        os.waitpid(-pgid, os.WNOHANG)  # type: ignore[attr-defined]
    except Exception:
        pass


def _child_entrypoint(result_file: str, module_path: str, callable_name: str, kwargs: Dict[str, Any]) -> None:
    """Target function for the child process."""
    from benchmark.runner.isolated_worker import worker_main
    worker_main(result_file, module_path, callable_name, kwargs)


def run_in_isolated_process(
    module_path: str,
    callable_name: str,
    kwargs: Dict[str, Any],
    output_path: Optional[str],
    timeout_sec: float,
) -> Dict[str, Any]:
    """
    Run an arbitrary callable in a fresh child process with a hard timeout.

    Uses fork context on POSIX (avoids spawn/pickle complexity) and a temp file
    for IPC (avoids multiprocessing.Queue semaphore leaks).

    Args:
        module_path:    Dotted Python module path.
        callable_name:  Name of the callable to invoke.
        kwargs:         Keyword arguments forwarded to the callable.
        output_path:    Expected SVG output path — deleted on timeout.
        timeout_sec:    Hard timeout in seconds.

    Returns:
        On success:  {"status": "ok", "result": <return value>}
        On timeout:  {"status": "timeout", "error_type": "BackendTimeoutError",
                      "duration_seconds": N, "metrics": None, "output_valid": False}
        On error:    {"status": "error", "error": <traceback>}
    """
    # Use a temp file for result — avoids Queue semaphore leaks
    fd, result_file = tempfile.mkstemp(suffix=".json", prefix="iso_result_")
    os.close(fd)

    # Use spawn everywhere; fork causes segmentation faults on macOS/Linux if
    # Qt or other native libraries have been initialized in the parent process.
    ctx = multiprocessing.get_context("spawn")

    proc = ctx.Process(
        target=_child_entrypoint,
        args=(result_file, module_path, callable_name, kwargs),
        daemon=False,
    )

    start = time.monotonic()
    proc.start()

    # Assign child to its own process group immediately after start (POSIX)
    if os.name == "posix" and proc.pid:
        try:
            os.setpgid(proc.pid, proc.pid)
        except (ProcessLookupError, PermissionError):
            pass  # process may have already exited

    proc.join(timeout=timeout_sec)
    elapsed = time.monotonic() - start

    if proc.is_alive():
        # Hard timeout
        if proc.pid:
            _kill_process_tree(proc.pid, grace_seconds=3.0)
        proc.join(timeout=5)
        if proc.is_alive():
            proc.kill()

        # Clean up partial output
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except OSError:
                pass

        # Clean up result file
        try:
            os.unlink(result_file)
        except OSError:
            pass

        return {
            "status": "timeout",
            "error_type": "BackendTimeoutError",
            "duration_seconds": timeout_sec,
            "metrics": None,
            "output_valid": False,
        }

    # Read result from temp file
    result: Dict[str, Any] = {}
    try:
        with open(result_file, "r", encoding="utf-8") as f:
            result = json.load(f)
    except Exception:
        result = {"status": "error", "error": "Child process exited without writing result"}
    finally:
        try:
            os.unlink(result_file)
        except OSError:
            pass

    result["duration_seconds"] = elapsed
    return result


def run_isolated_process(cmd: List[str], timeout_sec: int) -> Tuple[int, str, str]:
    """
    Runs an external command with timeout and process isolation.
    Guarantees child process termination on timeout.

    Returns:
        tuple: (exit_code, stdout, stderr)
    Raises:
        TimeoutError: If process exceeds timeout limit.
        ProcessExecutionError: If process fails to execute.
    """
    use_shell = False
    kwargs: Dict[str, Any] = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "shell": use_shell,
        "text": True,
    }

    if os.name == "posix":
        kwargs["preexec_fn"] = os.setsid  # type: ignore[assignment]
    elif os.name == "nt":
        kwargs["creationflags"] = 0x00000200

    try:
        proc = subprocess.Popen(cmd, **kwargs)  # type: ignore[call-overload]
    except FileNotFoundError:
        raise ProcessExecutionError(f"Executable not found: {cmd[0]}")
    except Exception as e:
        raise ProcessExecutionError(f"Failed to start process: {str(e)}")

    try:
        stdout, stderr = proc.communicate(timeout=timeout_sec)
        return proc.returncode, stdout, stderr
    except subprocess.TimeoutExpired:
        if os.name == "posix":
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            except Exception:
                proc.kill()
        elif os.name == "nt":
            try:
                os.kill(proc.pid, getattr(signal, "CTRL_BREAK_EVENT", 1))
            except Exception:
                proc.kill()
        else:
            proc.kill()

        proc.communicate()  # reap zombie
        raise TimeoutError(f"Process timed out after {timeout_sec}s")
