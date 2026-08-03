"""
isolated_worker.py

Entry point for child processes spawned by run_in_isolated_process().

This module uses a result file (temp JSON) instead of multiprocessing.Queue
to avoid semaphore leak issues with spawn context across POSIX process groups.
"""
import json
import os
import traceback
from typing import Any, Dict


def worker_main(
    result_file: str,
    module_path: str,
    callable_name: str,
    kwargs: Dict[str, Any],
) -> None:
    """
    Main function executed in the child process.

    Imports callable from module_path, calls it with kwargs,
    then writes the result as JSON to result_file.

    Uses bare except to ensure any error is captured and written
    back to the parent — never crashes silently.
    """
    try:
        import importlib
        mod = importlib.import_module(module_path)
        fn = getattr(mod, callable_name)
        result = fn(**kwargs)
        payload = {"status": "ok", "result": result, "pid": os.getpid()}
    except Exception:  # noqa: BLE001
        payload = {
            "status": "error",
            "error": traceback.format_exc(),
            "pid": os.getpid(),
        }

    try:
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)
    except Exception:
        # Last-resort: write minimal error marker
        try:
            with open(result_file, "w", encoding="utf-8") as f:
                f.write('{"status": "error", "error": "Failed to write result file"}')
        except Exception:
            pass
