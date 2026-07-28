import json
import os
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
        
        # Write valid manifest headers
        headers = "image_id,filename,category,license,sha256,width,height,has_alpha,format,split"
        
        yield {
            "base": base,
            "manifest": manifest_path,
            "schema": schema_path,
            "samples": samples_dir,
            "headers": headers,
            "img1": img1,
            "img2": img2
        }


@patch("benchmark.scripts.validate_dataset.get_image_info")
def test_validator_valid_row(mock_info, mock_dataset_env):
    env = mock_dataset_env
    mock_info.return_value = (100, 100, False, False)
    
    # Needs valid SHA256 of b"fake_image_data_1"
    import hashlib
    sha = hashlib.sha256(b"fake_image_data_1").hexdigest()
    
    with open(env["manifest"], "w") as f:
        f.write(env["headers"] + "\n")
        f.write(f"img_001,test1.png,logo,CC0,{sha},100,100,false,png,train\n")
        
    report = validate_manifest(env["manifest"], env["schema"], env["samples"])
    
    assert report["summary"]["total_errors"] == 0
    assert report["summary"]["total_valid"] == 1


@patch("benchmark.scripts.validate_dataset.get_image_info")
def test_validator_duplicates_and_errors(mock_info, mock_dataset_env):
    env = mock_dataset_env
    mock_info.return_value = (100, 100, False, False)
    
    import hashlib
    sha = hashlib.sha256(b"fake_image_data_1").hexdigest()
    
    with open(env["manifest"], "w") as f:
        f.write(env["headers"] + "\n")
        # Valid
        f.write(f"img_001,test1.png,logo,CC0,{sha},100,100,false,png,train\n")
        # Duplicate ID and filename, Duplicate SHA
        f.write(f"img_001,test2.png,logo,CC0,{sha},100,100,false,png,train\n")
        # Missing license, invalid category, missing file
        f.write(f"img_003,missing.png,invalid_cat,,{sha},100,100,false,png,train\n")
        
    report = validate_manifest(env["manifest"], env["schema"], env["samples"])
    
    assert report["summary"]["total_errors"] > 0
    
    error_str = " ".join(report["errors"])
    assert "Duplicate image_id" in error_str
    assert "License cannot be empty" in error_str
    assert "Invalid category" in error_str
    assert "not found in samples directory" in error_str
    
    assert len(report["warnings"]) > 0
    assert "Duplicate content detected" in report["warnings"][0]
