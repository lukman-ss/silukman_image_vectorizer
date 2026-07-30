import hashlib
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from benchmark.scripts.validate_dataset import validate_manifest


@pytest.fixture
def mock_dataset_env():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        manifest_path = base / "manifest.csv"
        schema_path = base / "schema.json"
        samples_dir = base / "samples"
        samples_dir.mkdir()

        # Create a valid test image
        img1 = samples_dir / "test1.png"
        img1.write_bytes(b"fake_image_data_1")

        # Create a duplicate image
        img2 = samples_dir / "test2.png"
        img2.write_bytes(b"fake_image_data_1")

        headers = "image_id,filename,category,source,license,redistribution_allowed,sha256,dataset_role,format"

        yield {
            "base": base,
            "manifest": manifest_path,
            "schema": schema_path,
            "samples": samples_dir,
            "headers": headers,
            "img1": img1,
            "img2": img2,
        }


@patch("benchmark.scripts.validate_dataset.check_image_properties")
def test_validator_valid_file(mock_info, mock_dataset_env):
    env = mock_dataset_env
    mock_info.return_value = (100, 100, False, False)

    sha = hashlib.sha256(b"fake_image_data_1").hexdigest()

    with open(env["manifest"], "w") as f:
        f.write(env["headers"] + "\n")
        f.write(f"img_001,test1.png,logo,Wikimedia,CC0,true,{sha},evaluation,png\n")

    report = validate_manifest(env["manifest"], env["schema"], env["samples"])
    assert report["summary"]["total_errors"] == 0
    assert report["summary"]["total_valid"] == 1


@patch("benchmark.scripts.validate_dataset.check_image_properties")
def test_validator_missing_file(mock_info, mock_dataset_env):
    env = mock_dataset_env
    mock_info.return_value = (100, 100, False, False)
    sha = hashlib.sha256(b"fake_image_data_1").hexdigest()

    with open(env["manifest"], "w") as f:
        f.write(env["headers"] + "\n")
        f.write(f"img_002,missing.png,logo,Wikimedia,CC0,true,{sha},evaluation,png\n")

    report = validate_manifest(env["manifest"], env["schema"], env["samples"])
    assert report["summary"]["total_errors"] > 0
    assert any("not found in samples directory" in e for e in report["errors"])


@patch("benchmark.scripts.validate_dataset.check_image_properties")
def test_validator_invalid_checksum(mock_info, mock_dataset_env):
    env = mock_dataset_env
    mock_info.return_value = (100, 100, False, False)

    with open(env["manifest"], "w") as f:
        f.write(env["headers"] + "\n")
        f.write("img_001,test1.png,logo,Wikimedia,CC0,true,wrong_hash,evaluation,png\n")

    report = validate_manifest(env["manifest"], env["schema"], env["samples"])
    assert report["summary"]["total_errors"] > 0
    assert any("Checksum mismatch" in e for e in report["errors"])


@patch("benchmark.scripts.validate_dataset.check_image_properties")
def test_validator_invalid_metadata(mock_info, mock_dataset_env):
    env = mock_dataset_env
    mock_info.return_value = (100, 100, False, False)
    sha = hashlib.sha256(b"fake_image_data_1").hexdigest()

    with open(env["manifest"], "w") as f:
        f.write(env["headers"] + "\n")
        # Empty license
        f.write(f"img_001,test1.png,logo,Wikimedia,,true,{sha},evaluation,png\n")
        # Invalid category
        f.write(f"img_002,test2.png,invalid_cat,Wikimedia,CC0,true,{sha},evaluation,png\n")
        # Invalid dataset role
        f.write(f"img_003,test1.png,logo,Wikimedia,CC0,true,{sha},invalid_role,png\n")

    report = validate_manifest(env["manifest"], env["schema"], env["samples"])
    assert report["summary"]["total_errors"] == 4
    error_str = " ".join(report["errors"])
    assert "License cannot be empty" in error_str
    assert "Invalid category" in error_str
    assert "Invalid dataset_role" in error_str
