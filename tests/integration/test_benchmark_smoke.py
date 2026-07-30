import json
import os

import cv2
import numpy as np
import pytest
import yaml

from benchmark.runner.experiment_runner import ExperimentRunner


@pytest.fixture
def smoke_env(tmp_path):
    # Create 2 synthetic images
    img_dir = tmp_path / "images"
    img_dir.mkdir()

    img1 = img_dir / "img1.png"
    img2 = img_dir / "img2.png"

    square = np.zeros((20, 20, 3), dtype=np.uint8)
    square[5:15, 5:15] = [255, 255, 255]
    cv2.imwrite(str(img1), square)

    circle = np.zeros((20, 20, 3), dtype=np.uint8)
    cv2.circle(circle, (10, 10), 5, (255, 255, 255), -1)
    cv2.imwrite(str(img2), circle)

    # Create manifest
    manifest_path = tmp_path / "manifest.csv"
    with open(manifest_path, "w") as f:
        f.write("image_id,filename,split,category,complexity,dataset_role\n")
        f.write(f"img1,{img1.name},test,shape,low,testing_only\n")
        f.write(f"img2,{img2.name},test,shape,low,testing_only\n")

    # Create config
    config_data = {
        "experiment": {
            "id": "smoke-test-v1",
            "repetitions": 1,
            "warmup_runs": 0,
            "timeout_seconds": 10,
        },
        "dataset": {"manifest": str(manifest_path), "split": "test", "categories": ["shape"]},
        "backends": ["silukman"],
        "presets": ["low_complexity"],
        "metrics": ["path_count", "svg_complexity"],
    }

    config_path = tmp_path / "smoke_config.yaml"
    with open(config_path, "w") as f:
        yaml.dump(config_data, f)

    return {
        "config_path": str(config_path),
        "manifest_path": str(manifest_path),
        "out_dir": str(tmp_path),
    }


def test_benchmark_smoke(smoke_env):
    runner = ExperimentRunner(config_path=smoke_env["config_path"], base_dir=smoke_env["out_dir"])
    runner.execute()

    # Verify outputs
    runs_dir = os.path.join(smoke_env["out_dir"], runner.experiment_id)
    assert os.path.exists(runs_dir)

    # Check runs.jsonl
    runs_file = os.path.join(runs_dir, "runs.jsonl")
    assert os.path.exists(runs_file)

    lines = 0
    with open(runs_file, "r") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                assert data["status"] == "success"
                lines += 1

    # 2 images * 1 repetition = 2
    assert lines == 2
