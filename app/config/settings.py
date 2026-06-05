from dataclasses import dataclass, field

DEFAULT_WINDOW_WIDTH = 1200
DEFAULT_WINDOW_HEIGHT = 760

@dataclass
class VTracerSettings:
    """VTracer-specific settings."""
    colormode: str = "color"          # color / binary
    hierarchical: str = "stacked"     # stacked / cutout
    mode: str = "spline"              # spline / polygon / none
    filter_speckle: int = 4           # speckle size filter
    color_precision: int = 6          # 1 to 8 (safer default max 6 to prevent 128 colors)
    layer_difference: int = 16        # color difference threshold
    corner_threshold: int = 60        # angle threshold for corners
    length_threshold: float = 3.5     # curve length threshold
    max_iterations: int = 16          # optimizer max iteration count
    path_precision: int = 8           # SVG path output decimal precision

@dataclass
class VectorizationSettings:
    """Settings that control the vectorization process."""
    # Legacy OpenCV settings
    min_area: float = 100.0          # Minimum contour area to keep (pixels)
    approx_tolerance: float = 2.0    # Douglas-Peucker epsilon for approximation
    smoothing_enabled: bool = False  # Whether to apply Gaussian smoothing pre-detection
    invert: bool = False             # Invert binary image before detection
    color_mode: str = "Unlimited colors"
    color_count: int = 8
    preserve_edges: bool = False
    remove_background: bool = False
    bg_tolerance: float = 20.0
    threshold_val: int = 127         # Threshold value for legacy engine
    palette_replacements: list[tuple[tuple[int, int, int], tuple[int, int, int]]] = field(default_factory=list)

    # Active engine type: "VTracer" or "OpenCV Legacy"
    engine_type: str = "VTracer"

    # VTracer settings object
    vtracer: VTracerSettings = field(default_factory=VTracerSettings)
