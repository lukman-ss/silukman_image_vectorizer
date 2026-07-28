import json
from pathlib import Path
from typing import Any, Dict, List

from app.config.settings import VectorizationConfig


class PresetManager:
    """Manages the loading and retrieval of vectorization academic presets."""

    _instance = None

    def __init__(self):
        self.presets_file = Path(__file__).parent / "presets.json"
        self._presets_data: Dict[str, Any] = {}
        self._load_presets()

    @classmethod
    def get_instance(cls) -> "PresetManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_presets(self) -> None:
        """Load and parse the presets.json file."""
        if not self.presets_file.exists():
            # Fallback to an empty dictionary if missing
            self._presets_data = {}
            return

        try:
            with open(self.presets_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            schema_version = data.get("$schema_version", "1.0")
            if schema_version != "1.0":
                raise ValueError(f"Unsupported preset schema version: {schema_version}")

            self._presets_data = data.get("presets", {})
        except Exception as e:
            raise RuntimeError(f"Failed to load presets: {str(e)}") from e

    def get_available_presets(self) -> List[str]:
        """Return a list of available preset names."""
        return list(self._presets_data.keys())

    def get_preset_info(self, preset_name: str) -> Dict[str, str]:
        """Get the purpose and trade-offs of a given preset."""
        preset = self._presets_data.get(preset_name, {})
        return {"purpose": preset.get("purpose", ""), "trade_off": preset.get("trade_off", "")}

    def get_preset_config(self, preset_name: str) -> VectorizationConfig:
        """Instantiate a VectorizationConfig object based on the requested preset."""
        if preset_name not in self._presets_data:
            raise ValueError(f"Preset '{preset_name}' not found.")

        preset = self._presets_data[preset_name]
        config_overrides = preset.get("config", {})

        # Start with default and override with preset values
        config = VectorizationConfig()

        for key, value in config_overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)

        # Re-trigger validation
        config.__post_init__()

        return config


# Convenience function for easy access
def get_preset(name: str) -> VectorizationConfig:
    return PresetManager.get_instance().get_preset_config(name)
