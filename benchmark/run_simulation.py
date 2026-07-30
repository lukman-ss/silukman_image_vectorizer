import argparse
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from benchmark.runner.config_schema import BenchmarkConfig
from benchmark.runner.experiment_runner import ExperimentRunner

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run vectorization benchmark simulation.")
    parser.add_argument("--config", default="benchmark/experiment_config.yaml", help="Path to experiment config YAML.")
    args = parser.parse_args()

    config = BenchmarkConfig.from_yaml(args.config)
    subfolder = "smoke" if config.experiment.experiment_role == "smoke" else "evaluation"
    base_dir = os.path.join("benchmark/results", subfolder)

    runner = ExperimentRunner(args.config, base_dir=base_dir)
    runner.execute()
