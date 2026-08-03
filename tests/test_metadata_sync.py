import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_metadata_sync():
    """Verify that version, date, repo URL, and license are perfectly synced."""
    # 1. pyproject.toml
    pyproject_path = REPO_ROOT / "pyproject.toml"
    pyproject_content = pyproject_path.read_text(encoding="utf-8")
    version_match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject_content, re.MULTILINE)
    assert version_match, "Version not found in pyproject.toml"
    primary_version = version_match.group(1)

    # 2. app/core/constants.py
    constants_path = REPO_ROOT / "app/core/constants.py"
    constants_content = constants_path.read_text(encoding="utf-8")
    app_version_match = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', constants_content, re.MULTILINE)
    assert app_version_match, "APP_VERSION not found in constants.py"
    assert app_version_match.group(1) == primary_version, "constants.py version mismatch"

    # 3. CITATION.cff
    citation_path = REPO_ROOT / "CITATION.cff"
    citation_content = citation_path.read_text(encoding="utf-8")
    cit_version_match = re.search(r'^version:\s*"([^"]+)"', citation_content, re.MULTILINE)
    assert cit_version_match and cit_version_match.group(
        1) == primary_version, "CITATION.cff version mismatch"
    cit_date_match = re.search(r'^date-released:\s*"([^"]+)"', citation_content, re.MULTILINE)
    assert cit_date_match, "date-released not found in CITATION.cff"
    primary_date = cit_date_match.group(1)
    cit_repo_match = re.search(r'^repository-code:\s*"([^"]+)"', citation_content, re.MULTILINE)
    primary_repo = cit_repo_match.group(
        1) if cit_repo_match else "https://github.com/lukman-ss/silukman_image_vectorizer"

    # 4. .zenodo.json
    zenodo_path = REPO_ROOT / ".zenodo.json"
    zenodo_data = json.loads(zenodo_path.read_text(encoding="utf-8"))
    assert zenodo_data["version"] == primary_version, ".zenodo.json version mismatch"
    assert zenodo_data["publication_date"] == primary_date, ".zenodo.json date mismatch"

    # 5. codemeta.json
    codemeta_path = REPO_ROOT / "codemeta.json"
    codemeta_data = json.loads(codemeta_path.read_text(encoding="utf-8"))
    assert codemeta_data["version"] == primary_version, "codemeta.json version mismatch"
    assert codemeta_data["datePublished"] == primary_date, "codemeta.json date mismatch"
    assert codemeta_data["codeRepository"] == primary_repo, "codemeta.json repo mismatch"
    assert codemeta_data["license"] == "https://spdx.org/licenses/MIT", "codemeta.json license mismatch"
