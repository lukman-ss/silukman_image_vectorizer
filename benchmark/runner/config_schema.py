import os
from dataclasses import dataclass, field
from typing import List, Optional

import yaml


class ConfigError(Exception):
    pass


@dataclass
class ExperimentConfig:
    id: str
    repetitions: int = 1
    warmup_runs: int = 1
    timeout_seconds: int = 60
    dataset_role: str = "testing_only"
    experiment_role: str = "smoke"
    publication_eligible: bool = False


_VALID_EXPERIMENT_ROLES = {"smoke", "pilot", "full_benchmark", "stress_benchmark"}
_VALID_RESIZE_POLICIES = {"reject", "fit_within", "none"}


@dataclass
class ResourcePolicyConfig:
    max_input_pixels: Optional[int] = None
    max_width: Optional[int] = None
    max_height: Optional[int] = None
    resize_policy: str = "reject"  # reject | fit_within | none
    memory_limit_mb: Optional[int] = None


@dataclass
class DatasetConfig:
    manifest: str
    split: str = "test"
    max_samples_per_category: int = 0
    categories: List[str] = field(
        default_factory=lambda: [
            "logo",
            "icon",
            "illustration",
            "complex_artwork",
            "photograph",
            "binary_graphic",
        ]
    )


@dataclass
class BenchmarkConfig:
    experiment: ExperimentConfig
    dataset: DatasetConfig
    backends: List[str]
    presets: List[str]
    metrics: List[str]
    resource_policy: ResourcePolicyConfig = field(default_factory=ResourcePolicyConfig)

    @classmethod
    def from_yaml(cls, filepath: str) -> "BenchmarkConfig":
        if not os.path.exists(filepath):
            raise ConfigError(f"Configuration file not found: {filepath}")

        with open(filepath, "r") as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ConfigError(f"Invalid YAML file: {e}")

        # Validate Experiment
        exp_data = data.get("experiment", {})
        if "id" not in exp_data:
            raise ConfigError("experiment.id is required.")
        role = exp_data.get("experiment_role", "smoke")
        if role not in _VALID_EXPERIMENT_ROLES:
            raise ConfigError(f"experiment_role must be one of {sorted(_VALID_EXPERIMENT_ROLES)}, got: '{role}'")
        experiment = ExperimentConfig(**exp_data)

        # Validate Dataset
        ds_data = data.get("dataset", {})
        if "manifest" not in ds_data:
            raise ConfigError("dataset.manifest is required.")
        dataset = DatasetConfig(**ds_data)

        # Enforce experiment rules
        if experiment.experiment_role in {"full_benchmark", "stress_benchmark"}:
            if experiment.repetitions < 3:
                raise ConfigError("repetitions must be at least 3 for full_benchmark/stress_benchmark")
            if experiment.warmup_runs < 1:
                raise ConfigError("warmup_runs must be at least 1 for full_benchmark/stress_benchmark")
            if experiment.dataset_role == "testing_only":
                raise ConfigError("dataset_role cannot be testing_only for full_benchmark/stress_benchmark")

        if experiment.publication_eligible and "synthetic" in dataset.manifest:
            raise ConfigError("publication_eligible cannot be true with a synthetic dataset manifest")

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

        # Validate Resource Policy
        rp_data = data.get("resource_policy", {})
        resize_policy = rp_data.get("resize_policy", "reject")
        if resize_policy not in _VALID_RESIZE_POLICIES:
            raise ConfigError(f"resource_policy.resize_policy must be one of {sorted(_VALID_RESIZE_POLICIES)}, got: '{resize_policy}'")
        resource_policy = ResourcePolicyConfig(
            max_input_pixels=rp_data.get("max_input_pixels"),
            max_width=rp_data.get("max_width"),
            max_height=rp_data.get("max_height"),
            resize_policy=resize_policy,
            memory_limit_mb=rp_data.get("memory_limit_mb"),
        )

        return cls(
            experiment=experiment,
            dataset=dataset,
            backends=backends,
            presets=presets,
            metrics=metrics,
            resource_policy=resource_policy,
        )
