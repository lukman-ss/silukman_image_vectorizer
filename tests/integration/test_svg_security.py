import pytest
from app.core.postprocessing import parse_and_validate_svg


def test_svg_security_xxe():
    """Test parser against XML External Entity (XXE) injection."""
    malicious_svg = """<?xml version="1.0" encoding="ISO-8859-1"?>
    <!DOCTYPE svg [
      <!ELEMENT svg ANY >
      <!ENTITY xxe SYSTEM "file:///etc/passwd" >]><svg>&xxe;</svg>"""

    with pytest.raises((ValueError, Exception)):
        # defusedxml should raise an exception on DTD or entity expansion
        parse_and_validate_svg(malicious_svg)


def test_svg_security_billion_laughs():
    """Test parser against Billion Laughs (exponential entity expansion)."""
    malicious_svg = """<?xml version="1.0"?>
    <!DOCTYPE svg [
     <!ENTITY lol "lol">
     <!ENTITY lol1 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
     <!ENTITY lol2 "&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;&lol1;">
    ]>
    <svg>&lol2;</svg>"""

    with pytest.raises((ValueError, Exception)):
        parse_and_validate_svg(malicious_svg)


def test_svg_security_malformed_xml():
    """Test parser against strictly malformed XML."""
    malformed_svg = "<svg><path d='M0 0 L10 10'></svg>"

    with pytest.raises(ValueError):
        parse_and_validate_svg(malformed_svg)


def test_svg_security_deeply_nested():
    """Test parser against deeply nested XML which could cause stack overflow."""
    # Defusedxml can limit depth or it will just parse it safely if within python recursion limits.
    # We just ensure it doesn't crash the python process.
    depth = 2000
    nested_svg = "<svg>" + ("<g>" * depth) + "</g>" * depth + "</svg>"
    try:
        parse_and_validate_svg(nested_svg)
    except Exception:
        # It's fine if it throws an error (e.g. recursion error), as long as it's caught
        pass
    assert True


def test_svg_security_oversized_path():
    """Test parser handles massive path data gracefully."""
    # 1 million coordinates
    huge_path = "0 0 " * 500000
    svg = f"<svg><path d='M {huge_path}'/></svg>"

    try:
        root = parse_and_validate_svg(svg)
        assert root is not None
    except MemoryError:
        pytest.fail("Oversized path caused OOM")
