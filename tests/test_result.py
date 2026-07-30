import json
import os
import tempfile


from app.core.result import VectorizationResult, calculate_file_hash


def test_calculate_file_hash_success():
    """Test streaming hash calculates correctly."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("hello world")
        temp_path = f.name

    try:
        # sha256 of "hello world"
        expected_hash = "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
        assert calculate_file_hash(temp_path) == expected_hash
    finally:
        os.remove(temp_path)


def test_calculate_file_hash_invalid_file():
    """Test hash returns None for invalid file."""
    assert calculate_file_hash("/invalid/path/that/does/not/exist.txt") is None


def test_vectorization_result_serialization():
    """Test VectorizationResult can serialize to dict and JSON."""
    result = VectorizationResult(
        run_id="test-123",
        status="success",
        input_path="in.png",
        output_path="out.svg",
        duration_seconds=1.5,
        configuration={"key": "value"},
    )

    # dict
    result_dict = result.to_dict()
    assert result_dict["run_id"] == "test-123"
    assert result_dict["duration_seconds"] == 1.5

    # json
    result_json = result.to_json()
    parsed = json.loads(result_json)
    assert parsed["status"] == "success"
    assert parsed["configuration"]["key"] == "value"


def test_vectorization_result_save_to_file(tmp_path):
    """Test VectorizationResult can save itself to a file."""
    result = VectorizationResult(
        run_id="test-save-456",
        status="failed",
        error_type="ValueError",
        error_message="Something went wrong",
    )

    output_file = tmp_path / "result.json"
    result.save(str(output_file))

    assert output_file.exists()

    with open(output_file, "r") as f:
        data = json.load(f)

    assert data["run_id"] == "test-save-456"
    assert data["status"] == "failed"
    assert data["error_type"] == "ValueError"
