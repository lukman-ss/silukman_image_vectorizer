import json
from dataclasses import dataclass, field, asdict
from typing import Any, Tuple, List

DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 760


@dataclass
class VectorizationConfig:
    """Centralized, typed configuration model for vectorization parameters."""
    
    # Global Settings
    engine_type: str = "VTracer"          # "VTracer" or "OpenCV Legacy"
    
    # Preprocessing Settings
    color_mode: str = "Unlimited colors"  # "Unlimited colors" or "Custom colors"
    color_count: int = 8                  # Number of colors to quantize if Custom colors (1-256)
    preserve_edges: bool = False          # Whether to use edge-preserving filter in quantization
    remove_background: bool = False       # Whether to apply background removal
    bg_tolerance: float = 20.0            # Distance tolerance for background removal (0.0 - 255.0)
    palette_replacements: List[Tuple[Tuple[int, int, int], Tuple[int, int, int]]] = field(default_factory=list)
    
    # OpenCV Legacy Settings
    min_area: float = 100.0               # Minimum contour area to keep (pixels) (>= 0.0)
    approx_tolerance: float = 2.0         # Douglas-Peucker epsilon for approximation (>= 0.0)
    smoothing_enabled: bool = False       # Whether to apply Gaussian smoothing pre-detection
    invert: bool = False                  # Invert binary image before detection
    threshold_val: int = 127              # Threshold value for legacy engine (0-255)
    
    # VTracer Specific Settings
    colormode: str = "color"              # "color" or "binary"
    hierarchical: str = "stacked"         # "stacked" or "cutout"
    mode: str = "spline"                  # "spline", "polygon", or "none"
    filter_speckle: int = 4               # Speckle size filter (0-1024)
    color_precision: int = 6              # 1 to 8
    layer_difference: int = 16            # Color difference threshold (0-255)
    corner_threshold: int = 60            # Angle threshold for corners (0-180)
    length_threshold: float = 3.5         # Curve length threshold (3.5 - 10.0)
    max_iterations: int = 16              # Optimizer max iteration count (1-100)
    splice_threshold: int = 45            # Splice threshold for VTracer (0-180)
    path_precision: int = 8               # SVG path output decimal precision (0-16)

    def __post_init__(self):
        """Validates configuration parameters after initialization."""
        self._validate_choices("engine_type", self.engine_type, ["VTracer", "OpenCV Legacy"])
        self._validate_choices("color_mode", self.color_mode, ["Unlimited colors", "Custom colors"])
        self._validate_range("color_count", self.color_count, 1, 256)
        self._validate_range("bg_tolerance", self.bg_tolerance, 0.0, 255.0)
        self._validate_range("min_area", self.min_area, 0.0, float('inf'))
        self._validate_range("approx_tolerance", self.approx_tolerance, 0.0, float('inf'))
        self._validate_range("threshold_val", self.threshold_val, 0, 255)
        
        self._validate_choices("colormode", self.colormode, ["color", "binary"])
        self._validate_choices("hierarchical", self.hierarchical, ["stacked", "cutout"])
        self._validate_choices("mode", self.mode, ["spline", "polygon", "none"])
        
        self._validate_range("filter_speckle", self.filter_speckle, 0, 1024)
        self._validate_range("color_precision", self.color_precision, 1, 8)
        self._validate_range("layer_difference", self.layer_difference, 0, 255)
        self._validate_range("corner_threshold", self.corner_threshold, 0, 180)
        self._validate_range("length_threshold", self.length_threshold, 3.5, 10.0)
        self._validate_range("max_iterations", self.max_iterations, 1, 100)
        self._validate_range("splice_threshold", self.splice_threshold, 0, 180)
        self._validate_range("path_precision", self.path_precision, 0, 16)

    @staticmethod
    def _validate_choices(field_name: str, value: Any, choices: list):
        if value not in choices:
            raise ValueError(f"Invalid value for {field_name}: '{value}'. Must be one of {choices}.")

    @staticmethod
    def _validate_range(field_name: str, value: Any, min_val: float, max_val: float):
        if not (min_val <= value <= max_val):
            raise ValueError(f"Invalid value for {field_name}: {value}. Must be between {min_val} and {max_val}.")

    def to_dict(self) -> dict:
        """Serialize configuration to a dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "VectorizationConfig":
        """Deserialize configuration from a dictionary."""
        # Provide backward compatibility for older settings dicts
        kwargs = dict(data)
        if "vtracer" in kwargs and isinstance(kwargs["vtracer"], dict):
            vt_settings = kwargs.pop("vtracer")
            for k, v in vt_settings.items():
                if k not in kwargs:
                    kwargs[k] = v
        
        # Filter out unknown keys to allow forward compatibility
        valid_keys = {f for f in cls.__dataclass_fields__.keys()}
        filtered_kwargs = {k: v for k, v in kwargs.items() if k in valid_keys}
        
        # Fix tuples in palette replacements if they were converted to lists
        if "palette_replacements" in filtered_kwargs:
            replacements = filtered_kwargs["palette_replacements"]
            try:
                filtered_kwargs["palette_replacements"] = [
                    (tuple(src), tuple(dst)) for src, dst in replacements
                ]
            except Exception:
                pass

        return cls(**filtered_kwargs)

    def to_json(self) -> str:
        """Serialize configuration to a JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "VectorizationConfig":
        """Deserialize configuration from a JSON string."""
        return cls.from_dict(json.loads(json_str))

    @property
    def vtracer(self):
        """Backward compatibility for legacy config.vtracer accesses."""
        return self


# Backward compatibility alias
VectorizationSettings = VectorizationConfig
