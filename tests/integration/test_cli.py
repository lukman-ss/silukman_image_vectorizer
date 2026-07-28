import json
import os
import subprocess
import sys

import cv2
import numpy as np
import pytest

CLI = [sys.executable, "-m", "app.cli_headless"]


@pytest.fixture
def synth_image(tmp_path):
    path = str(tmp_path / "img.png")
    img = np.zeros((20, 20, 3), dtype=np.uint8)
    img[5:15, 5:15] = [255, 255, 255]
    cv2.imwrite(path, img)
    return path


def test_cli_help():
    res = subprocess.run(CLI + ["-h"], capture_output=True, text=True)
    assert res.returncode == 0
    assert "Headless Command Line Interface" in res.stdout


def test_cli_invalid_command():
    res = subprocess.run(CLI + ["unknown_cmd"], capture_output=True, text=True)
    assert res.returncode != 0
    assert "invalid choice: 'unknown_cmd'" in res.stderr


def test_cli_missing_file():
    res = subprocess.run(CLI + ["vectorize", "does_not_exist.png"], capture_output=True, text=True)
    assert res.returncode != 0
    assert "Error" in res.stderr or "Error" in res.stdout


def test_cli_valid_vectorization(synth_image, tmp_path):
    out = str(tmp_path / "out.svg")
    res = subprocess.run(
        CLI + ["vectorize", synth_image, "-o", out], capture_output=True, text=True
    )
    assert res.returncode == 0
    assert "Success" in res.stdout
    assert os.path.exists(out)


def test_cli_json_output(synth_image, tmp_path):
    out = str(tmp_path / "out_json.svg")
    res = subprocess.run(
        CLI + ["vectorize", synth_image, "-o", out, "--json"], capture_output=True, text=True
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["status"] == "success"
    assert data["output_path"] == out


def test_cli_dry_run(synth_image, tmp_path):
    out = str(tmp_path / "out_dry.svg")
    res = subprocess.run(
        CLI + ["vectorize", synth_image, "-o", out, "--dry-run"], capture_output=True, text=True
    )
    assert res.returncode == 0
    assert "DRY RUN" in res.stdout
    assert not os.path.exists(out)


def test_cli_preset_listing():
    res = subprocess.run(CLI + ["presets", "--json"], capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert isinstance(data, list)
    names = [d["name"] for d in data]
    assert "balanced" in names


def test_cli_inspect(synth_image, tmp_path):
    out = str(tmp_path / "out_ins.svg")
    subprocess.run(CLI + ["vectorize", synth_image, "-o", out], check=True)

    res = subprocess.run(CLI + ["inspect", out, "--json"], capture_output=True, text=True)
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["is_valid_xml"] is True


def test_cli_batch(synth_image, tmp_path):
    in_dir = tmp_path / "inputs"
    in_dir.mkdir()
    out_dir = tmp_path / "outputs"

    import shutil

    shutil.copy(synth_image, str(in_dir / "1.png"))
    shutil.copy(synth_image, str(in_dir / "2.png"))

    res = subprocess.run(
        CLI + ["batch", str(in_dir), "-o", str(out_dir), "--json"], capture_output=True, text=True
    )
    assert res.returncode == 0
    data = json.loads(res.stdout)
    assert data["total_processed"] == 2
    assert data["success"] == 2


def test_benchmark_config_validation(tmp_path):
    # Invalid config path
    res = subprocess.run(
        CLI + ["benchmark", "run", "-c", "invalid.yaml"], capture_output=True, text=True
    )
    assert res.returncode != 0
    assert "Configuration file not found" in res.stderr
