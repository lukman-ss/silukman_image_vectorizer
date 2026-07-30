import os
import json
import pytest
import tempfile
from benchmark.analysis.aggregator import BenchmarkAggregator


def test_aggregator_rejects_smoke_test():
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_file = os.path.join(tmpdir, "runs.jsonl")
        manifest_file = os.path.join(tmpdir, "manifest.json")

        with open(runs_file, "w") as f:
            f.write('{"status": "success"}\n')

        with open(manifest_file, "w") as f:
            json.dump({"publication_eligible": False}, f)

        with pytest.raises(ValueError, match="is not publication eligible"):
            BenchmarkAggregator(runs_file)


def test_aggregator_accepts_publication_eligible():
    with tempfile.TemporaryDirectory() as tmpdir:
        runs_file = os.path.join(tmpdir, "runs.jsonl")
        manifest_file = os.path.join(tmpdir, "manifest.json")

        with open(runs_file, "w") as f:
            f.write('{"status": "success"}\n')

        with open(manifest_file, "w") as f:
            json.dump({"publication_eligible": True}, f)

        agg = BenchmarkAggregator(runs_file)
        assert agg.runs_file == runs_file
