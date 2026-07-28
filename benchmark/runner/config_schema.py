import os
import yaml
from dataclasses import dataclass, field
from typing import List

class ConfigError(Exception):
    pass


@dataclass
class ExperimentConfig:
    id: str
    repetitions: int = 1
    warmup_runs: int = 1
    timeout_seconds: int = 60

@dataclass
class DatasetConfig:
    manifest: str
    split: str = "test"
    categories: List[str] = field(default_factory=lambda: ["logo", "icon", "illustration", "complex_artwork", "photograph", "binary_graphic"])

@dataclass
class BenchmarkConfig:
    experiment: ExperimentConfig
    dataset: DatasetConfig
    backends: List[str]
    presets: List[str]
    metrics: List[str]

    @classmethod
    def from_yaml(cls, filepath: str) -> "BenchmarkConfig":
        if not os.path.exists(filepath):
            raise ConfigError(f"Configuration file not found: {filepath}")
            
        with open(filepath, 'r') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ConfigError(f"Invalid YAML file: {e}")
                
        # Validate Experiment
        exp_data = data.get("experiment", {})
        if "id" not in exp_data:
            raise ConfigError("experiment.id is required.")
        experiment = ExperimentConfig(**exp_data)
        
        # Validate Dataset
        ds_data = data.get("dataset", {})
        if "manifest" not in ds_data:
            raise ConfigError("dataset.manifest is required.")
        dataset = DatasetConfig(**ds_data)
        
        # Validate Backends
        backends = data.get("backends", [])
        if not backends:
            raise ConfigError("At least one backend must be specified in 'backends'.")
            
        # Validate Presets
        presets = data.get("presets", [])
        if not presets:
            raise ConfigError("At least one preset must be specified in 'presets'.")
            
        # Validate Metrics
        metrics = data.get("metrics", [])
        
        return cls(
            experiment=experiment,
            dataset=dataset,
            backends=backends,
            presets=presets,
            metrics=metrics
        )
