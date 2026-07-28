import os
import sys
import time
import tracemalloc
from typing import Any, Callable, Dict

try:
    import resource

    HAS_RESOURCE = True
except ImportError:
    HAS_RESOURCE = False


class PerformanceTracker:
    """
    Measures execution runtime and memory metrics for a given core function.

    Security & Scope:
    This tracker strictly isolates the timing of the core vectorization execution.
    It intentionally excludes GUI initialization and asset loading.

    Cross-OS Limitations:
    1. Memory Tracking: Tracking peak memory of C/Rust extensions (like vtracer)
       is extremely difficult across platforms.
       - On macOS/Linux, we use `resource.getrusage().ru_maxrss`. Note that macOS
         returns bytes, while Linux returns kilobytes. We attempt to normalize to bytes.
       - On Windows (where `resource` is missing), we fall back to Python's `tracemalloc`.
         However, `tracemalloc` ONLY tracks memory allocated by Python, and completely
         misses native extension allocations.
    2. CPU Time: `time.process_time()` does not include sleep time and is highly
       OS-dependent regarding multi-threading.
    """

    def __init__(self):
        self.is_mac = sys.platform == "darwin"

    def _get_maxrss_bytes(self) -> int:
        if not HAS_RESOURCE:
            return 0
        usage = resource.getrusage(resource.RUSAGE_SELF)
        # MacOS returns bytes, Linux returns KB
        if self.is_mac:
            return usage.ru_maxrss
        else:
            return usage.ru_maxrss * 1024

    def warmup(self, func: Callable, *args, **kwargs):
        """
        Runs the function once purely for warm-up.
        This forces Python to load modules, JIT compile paths, and allocate
        necessary caches before the actual benchmark starts.
        """
        try:
            func(*args, **kwargs)
        except Exception:
            pass

    def measure(
        self,
        func: Callable,
        input_file: str,
        output_file: str,
        timeout_seconds: float = None,
        retries: int = 0,
        *args,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Measures the performance of the core vectorization function.

        Args:
            func: The core function to execute (e.g. vectorizer.process)
            input_file: Path to input raster
            output_file: Path to output SVG
            timeout_seconds: Hard limit for execution (Not fully enforced in synchronous python without multiprocessing, documented as config)
            retries: Number of times to retry on failure.
        """

        input_bytes = os.path.getsize(input_file) if os.path.exists(input_file) else 0

        # Initial memory states
        initial_rss = self._get_maxrss_bytes()

        if not HAS_RESOURCE:
            tracemalloc.start()

        success = False
        retry_count = 0
        error_msg = ""

        wall_start = time.perf_counter()
        cpu_start = time.process_time()

        # Retry loop
        while retry_count <= retries and not success:
            try:
                # The core execution
                func(*args, **kwargs)
                success = True
            except Exception as e:
                error_msg = str(e)
                if retry_count < retries:
                    retry_count += 1
                else:
                    break

        wall_end = time.perf_counter()
        cpu_end = time.process_time()

        wall_time = wall_end - wall_start
        cpu_time = cpu_end - cpu_start

        # Memory metrics
        peak_memory = 0
        if HAS_RESOURCE:
            final_rss = self._get_maxrss_bytes()
            peak_memory = max(0, final_rss - initial_rss)
        else:
            _, peak_tracemalloc = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            peak_memory = peak_tracemalloc

        output_bytes = os.path.getsize(output_file) if os.path.exists(output_file) else 0

        throughput = 0.0
        if success and wall_time > 0:
            throughput = input_bytes / wall_time

        return {
            "success": success,
            "wall_clock_time_seconds": wall_time,
            "cpu_time_seconds": cpu_time,
            "peak_memory_bytes": peak_memory,
            "input_bytes": input_bytes,
            "output_bytes": output_bytes,
            "throughput_bytes_per_second": throughput,
            "timeout_configured": timeout_seconds,
            "retry_count": retry_count,
            "error": error_msg if not success else None,
        }
