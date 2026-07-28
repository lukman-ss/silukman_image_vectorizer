import csv

import pytest

from benchmark.runner.config_schema import BenchmarkConfig


def test_dataset_manifest_validation(tmp_path):
    manifest_file = tmp_path / "dataset.csv"
    with open(manifest_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["image_id", "split", "category", "path"])
        writer.writerow(["img1", "test", "logo", "path/to/img1.png"])
        writer.writerow(["img2", "train", "icon", "path/to/img2.png"])

    valid_yaml = f"""
experiment:
  id: "test-dataset"
dataset:
  manifest: "{manifest_file.as_posix()}"
  split: "test"
  categories:
    - logo
backends:
  - silukman
presets:
  - balanced
metrics:
  - ssim
"""
    cfg_file = tmp_path / "valid.yaml"
    cfg_file.write_text(valid_yaml)

    cfg = BenchmarkConfig.from_yaml(str(cfg_file))

    assert str(Path(cfg.dataset.manifest)) == str(Path(manifest_file))
    assert cfg.dataset.split == "test"
    assert "logo" in cfg.dataset.categories
