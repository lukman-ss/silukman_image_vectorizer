import json
import re
from pathlib import Path

def test_versions_are_synchronized():
    base_dir = Path(__file__).parent.parent
    
    # pyproject.toml
    pyproject_text = (base_dir / "pyproject.toml").read_text()
    pyproject_match = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', pyproject_text, re.MULTILINE)
    assert pyproject_match is not None, "Version not found in pyproject.toml"
    reference_version = pyproject_match.group(1)
    
    # CITATION.cff
    citation_text = (base_dir / "CITATION.cff").read_text()
    citation_match = re.search(r'^version:\s*["\']([^"\']+)["\']', citation_text, re.MULTILINE)
    assert citation_match is not None, "Version not found in CITATION.cff"
    assert citation_match.group(1) == reference_version, f"CITATION.cff version {citation_match.group(1)} != {reference_version}"
    
    # .zenodo.json
    zenodo_data = json.loads((base_dir / ".zenodo.json").read_text())
    assert zenodo_data.get("version") == reference_version, f".zenodo.json version {zenodo_data.get('version')} != {reference_version}"
    
    # codemeta.json
    codemeta_data = json.loads((base_dir / "codemeta.json").read_text())
    assert codemeta_data.get("version") == reference_version, f"codemeta.json version {codemeta_data.get('version')} != {reference_version}"
    
    # app/core/constants.py
    constants_text = (base_dir / "app" / "core" / "constants.py").read_text()
    constants_match = re.search(r'^APP_VERSION\s*=\s*["\']([^"\']+)["\']', constants_text, re.MULTILINE)
    assert constants_match is not None, "APP_VERSION not found in constants.py"
    assert constants_match.group(1) == reference_version, f"constants.py APP_VERSION {constants_match.group(1)} != {reference_version}"
