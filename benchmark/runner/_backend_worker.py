"""
_backend_worker.py

Callable executed in the isolated child process by ExperimentRunner.

This module must be importable by the child process (started via multiprocessing
"spawn" context). It imports the backend registry and runs the requested
backend's vectorize() method.

Keeping it as a standalone module (rather than a lambda/closure) ensures
picklability across all Python versions and platforms.
"""
from typing import Any, Dict, Optional


def run_backend_vectorize(
    backend_name: str,
    input_path: str,
    output_path: str,
    preset: str,
    category: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Called inside the child process.
    Imports the backend, runs vectorize(), and returns the result dict.

    Any exception here will be captured by isolated_worker.worker_main()
    and reported back as status="error".
    """
    from benchmark.baselines.backends import (
        InkscapeBackend,
        PotraceBackend,
        SilukmanBackend,
        VTracerBackend,
    )

    registry = {
        "silukman": SilukmanBackend,
        "vtracer": VTracerBackend,
        "potrace": PotraceBackend,
        "inkscape": InkscapeBackend,
    }

    name = backend_name.lower()
    if name not in registry:
        return {
            "error": f"Unknown backend: {backend_name}",
            "performance": {"success": False, "error": f"Unknown backend: {backend_name}"},
        }

    backend = registry[name]()

    if not backend.is_available():
        return {
            "error": f"Backend '{backend_name}' is not available on this system.",
            "performance": {"success": False, "error": f"Backend '{backend_name}' not available"},
        }

    return backend.vectorize(input_path, output_path, preset, category=category)  # type: ignore[call-arg]
