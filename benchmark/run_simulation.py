import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from benchmark.runner.experiment_runner import ExperimentRunner
from benchmark.runner.config_schema import BenchmarkConfig

runner = ExperimentRunner("benchmark/experiment_config.yaml", base_dir="benchmark/results")
runner.execute()
