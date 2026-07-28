import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.cli_headless import main, _build_parser


@pytest.fixture
def parser():
    return _build_parser()


def test_parser_commands(parser):
    # Test valid commands
    args = parser.parse_args(["gui"])
    assert args.command == "gui"

    args = parser.parse_args(["presets", "--json"])
    assert args.command == "presets"
    assert args.json is True

    args = parser.parse_args(["vectorize", "input.png", "--output", "out.svg", "--preset", "high_fidelity"])
    assert args.command == "vectorize"
    assert args.input == "input.png"
    assert args.output == "out.svg"
    assert args.preset == "high_fidelity"


def test_main_no_args(capsys):
    ret = main([])
    assert ret == 1
    captured = capsys.readouterr()
    assert "usage:" in captured.out


@patch("app.cli_headless.PresetManager")
def test_cmd_presets(mock_preset_manager_class, capsys):
    mock_instance = mock_preset_manager_class.get_instance.return_value
    mock_instance.get_available_presets.return_value = ["balanced", "high_fidelity"]
    
    # Text mode
    ret = main(["presets"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "balanced" in captured.out
    assert "high_fidelity" in captured.out

    # JSON mode
    mock_config = MagicMock()
    mock_config.to_json.return_value = '{"threshold_val": 128}'
    mock_instance.get_preset_config.return_value = mock_config
    
    ret = main(["presets", "--json"])
    assert ret == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert len(data) == 2
    assert data[0]["name"] == "balanced"
    assert data[0]["config"]["threshold_val"] == 128


@patch("app.cli_headless.vectorize_image")
@patch("app.cli_headless._load_settings")
def test_cmd_vectorize_success(mock_load_settings, mock_vectorize, capsys):
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.path_count = 100
    mock_result.element_count = 150
    mock_result.duration_seconds = 1.5
    mock_result.to_json.return_value = '{"success": true}'
    mock_vectorize.return_value = mock_result
    
    ret = main(["vectorize", "input.png"])
    assert ret == 0
    mock_vectorize.assert_called_once()
    
    # JSON output
    ret = main(["vectorize", "input.png", "--json"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "true" in captured.out


@patch("app.cli_headless.vectorize_image")
@patch("app.cli_headless._load_settings")
def test_cmd_vectorize_fail(mock_load_settings, mock_vectorize, capsys):
    mock_result = MagicMock()
    mock_result.success = False
    mock_result.error_message = "Test error"
    mock_vectorize.return_value = mock_result
    
    ret = main(["vectorize", "input.png"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "Test error" in captured.out


@patch("app.cli_headless.vectorize_image")
@patch("app.cli_headless._load_settings")
def test_cmd_vectorize_dry_run(mock_load_settings, mock_vectorize, capsys):
    mock_settings = MagicMock()
    mock_settings.engine_type = "VTracer"
    mock_settings.threshold_val = 127
    mock_settings.remove_background = False
    mock_settings.to_json.return_value = '{"test": 123}'
    mock_load_settings.return_value = mock_settings
    
    ret = main(["vectorize", "input.png", "--dry-run"])
    assert ret == 0
    mock_vectorize.assert_not_called()
    captured = capsys.readouterr()
    assert "--- DRY RUN ---" in captured.out
    assert "VTracer" in captured.out
    assert "Grayscale threshold: 127" in captured.out
    
    ret = main(["vectorize", "input.png", "--dry-run", "--json"])
    assert ret == 0
    mock_vectorize.assert_not_called()
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert data["mode"] == "dry-run"
    assert data["backend"] == "VTracer"


@patch("app.core.postprocessing.calculate_svg_metrics")
@patch("app.core.postprocessing.parse_and_validate_svg")
@patch("builtins.open", new_callable=MagicMock)
def test_cmd_inspect(mock_open, mock_parse, mock_calc, capsys):
    mock_root = MagicMock()
    mock_root.get.side_effect = lambda key, default=None: "800" if key == "width" else "600" if key == "height" else default
    mock_parse.return_value = mock_root
    mock_calc.return_value = {
        "path_count": 10,
        "total_elements": 15
    }
    
    ret = main(["inspect", "output.svg"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "800x600" in captured.out
    assert "Path Count: 10" in captured.out


def test_cmd_batch_invalid_dir(capsys):
    ret = main(["batch", "nonexistent_dir_123", "--output-dir", "out_dir"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "does not exist" in captured.err


@patch("app.cli_headless.vectorize_image")
@patch("app.cli_headless._load_settings")
@patch("pathlib.Path.iterdir")
@patch("pathlib.Path.is_dir")
@patch("pathlib.Path.mkdir")
@patch("builtins.open", new_callable=MagicMock)
def test_cmd_batch_success(mock_open, mock_mkdir, mock_is_dir, mock_iterdir, mock_load, mock_vec, capsys):
    mock_is_dir.return_value = True
    
    mock_file1 = MagicMock()
    mock_file1.is_file.return_value = True
    mock_file1.suffix = ".png"
    mock_file1.stem = "image1"
    mock_file1.resolve.return_value = "/mock/image1.png"
    
    mock_iterdir.return_value = [mock_file1]
    
    mock_result = MagicMock()
    mock_result.success = True
    mock_result.to_json.return_value = '{"success": true}'
    mock_vec.return_value = mock_result
    
    ret = main(["batch", "input_dir", "--output-dir", "out_dir", "--workers", "1"])
    assert ret == 0
    mock_vec.assert_called_once()
