import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


def calculate_file_hash(filepath: str, chunk_size: int = 8192) -> Optional[str]:
    """Calculate the SHA256 hash of a file efficiently using streaming."""
    import os

    if not filepath or not os.path.exists(filepath):
        return None

    sha256 = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            while chunk := f.read(chunk_size):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception:
        return None


@dataclass
class VectorizationResult:
    """Structured result model for vectorization output."""

    # Metadata
    run_id: str
    schema_version: str = "1.0"
    status: str = "pending"  # "success", "failed"

    # Timing
    started_at: str = ""
    finished_at: str = ""
    duration_seconds: float = 0.0

    # Inputs
    input_path: str = ""
    input_sha256: Optional[str] = None
    input_width: int = 0
    input_height: int = 0
    input_format: str = ""
    input_file_size: int = 0

    # Outputs
    output_path: str = ""
    output_sha256: Optional[str] = None
    output_file_size: int = 0

    # SVG Metrics
    path_count: int = 0
    element_count: int = 0
    estimated_command_count: int = 0

    # Processing Context
    configuration: Dict[str, Any] = field(default_factory=dict)
    preprocessing_log: List[Dict[str, Any]] = field(default_factory=list)
    software_versions: Dict[str, str] = field(default_factory=dict)

    # Diagnostics
    warnings: List[str] = field(default_factory=list)
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def save(self, file_path: str) -> None:
        """Save the JSON result to a file."""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.to_json())
