from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class VectorizationState:
    """Application-level mutable state for the vectorization workflow."""

    input_path: Optional[Path] = None
    output_path: Optional[Path] = None
    source_image: Any = None  # QPixmap — held as Any to avoid Qt imports at model level
    thresholded_array: Any = None  # numpy ndarray
    vector_result: Any = None  # VectorResult from engine
    is_processing: bool = False
    is_vectorizing: bool = False
    progress: int = 0
    error_message: Optional[str] = None
    palette_colors: list = field(default_factory=list)
    palette_replacements: dict = field(default_factory=dict)
    is_palette_pick_mode: bool = False
    batch_files: list = field(default_factory=list)
