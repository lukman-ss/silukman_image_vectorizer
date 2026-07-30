from typing import Any, Dict, Optional

from app.config.preset_manager import PresetManager
from app.core.vectorization_service import vectorize_image
from benchmark.baselines.backend_interface import VectorizerBackend
from benchmark.baselines.inkscape_baseline import InkscapeBaselineRunner
from benchmark.baselines.potrace_baseline import PotraceBaselineRunner
from benchmark.baselines.vtracer_baseline import VTracerBaselineRunner

# Reuse the unified performance tracker format mapping if needed,
# but vectorization_service returns its own duration.


class SilukmanBackend(VectorizerBackend):
    def __init__(self):
        self.preset_manager = PresetManager.get_instance()

    def name(self) -> str:
        return "Silukman"

    def version(self) -> str:
        # Assuming current version is 1.6.0 based on latest tags
        return "1.6.0"

    def is_available(self) -> bool:
        return True

    def vectorize(
        self, input_path: str, output_path: str, preset_name: str, category: Optional[str] = None
    ) -> Dict[str, Any]:
        try:
            config = self.preset_manager.get_preset_config(preset_name)

            result = vectorize_image(input_path, output_path, config)

            return {
                "preset": preset_name,
                "status": result.status,
                "performance": {
                    "success": result.status == "success",
                    "wall_clock_time_seconds": getattr(result, "duration_seconds", 0.0),
                    "peak_memory_bytes": 0,  # vectorization_service doesn't track this currently
                    "input_bytes": getattr(result, "input_file_size", 0),
                    "output_bytes": getattr(result, "output_file_size", 0),
                    "error": getattr(result, "error_message", None),
                },
            }
        except Exception as e:
            return {
                "preset": preset_name,
                "status": "failed",
                "performance": {"success": False, "error": str(e)},
            }


class VTracerBackend(VectorizerBackend):
    def __init__(self):
        self.runner = VTracerBaselineRunner()

    def name(self) -> str:
        return "VTracer Direct"

    def version(self) -> str:
        return self.runner.vtracer_version

    def is_available(self) -> bool:
        return self.runner.vtracer_version != "unknown"

    def vectorize(
        self, input_path: str, output_path: str, preset_name: str, category: Optional[str] = None
    ) -> Dict[str, Any]:
        return self.runner.run(input_path, output_path, preset_name)


class PotraceBackend(VectorizerBackend):
    def __init__(self, timeout: int = 10):
        self.runner = PotraceBaselineRunner()
        self.timeout = timeout

    def name(self) -> str:
        return "Potrace"

    def version(self) -> str:
        return self.runner.potrace_version

    def is_available(self) -> bool:
        return self.runner.potrace_version != "not_installed"

    def vectorize(
        self, input_path: str, output_path: str, preset_name: str, category: Optional[str] = None
    ) -> Dict[str, Any]:
        # Potrace ignores preset_name since it only does BW
        cat = category or "binary_graphic"
        return self.runner.run(input_path, output_path, cat, self.timeout)


class InkscapeBackend(VectorizerBackend):
    def __init__(self, timeout: int = 60):
        self.runner = InkscapeBaselineRunner()
        self.timeout = timeout

    def name(self) -> str:
        return "Inkscape CLI"

    def version(self) -> str:
        return self.runner.inkscape_version

    def is_available(self) -> bool:
        return self.runner.inkscape_version != "not_installed"

    def vectorize(
        self, input_path: str, output_path: str, preset_name: str, category: Optional[str] = None
    ) -> Dict[str, Any]:
        # Inkscape ignores preset_name (uses GUI defaults)
        return self.runner.run(input_path, output_path, self.timeout)
