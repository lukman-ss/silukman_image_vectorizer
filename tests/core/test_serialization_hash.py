

from app.core.result import calculate_file_hash
from benchmark.runner.env_capture import generate_config_hash


def test_config_hash(tmp_path):
    # Two identical configs should have the same hash
    cfg1 = tmp_path / "1.yaml"
    cfg1.write_text("a: 1\nb: 2")
    cfg2 = tmp_path / "2.yaml"
    cfg2.write_text("a: 1\nb: 2")

    hash1 = generate_config_hash(str(cfg1))
    hash2 = generate_config_hash(str(cfg2))
    assert hash1 == hash2


def test_image_hash(tmp_path):
    img = tmp_path / "img.png"
    img.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")

    h = calculate_file_hash(str(img))
    assert len(h) == 64  # SHA256 hex digest length
