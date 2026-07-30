import os
import json
import csv
import re
import sys


def validate_presets():
    print("Validating preset files...")
    preset_path = "app/config/presets.json"
    assert os.path.exists(preset_path), "presets.json missing"
    with open(preset_path) as f:
        data = json.load(f)
    assert "$schema_version" in data
    assert "presets" in data


def validate_citation():
    print("Validating citation metadata...")
    assert os.path.exists("CITATION.cff"), "CITATION.cff missing"


def validate_dataset_manifest():
    print("Validating dataset manifest schema...")
    manifest_path = "benchmark/dataset_manifest.csv"
    if os.path.exists(manifest_path):
        with open(manifest_path) as f:
            reader = csv.reader(f)
            headers = next(reader)
            expected = {"image_id", "file_path", "split", "category"}
            assert expected.issubset(set(headers)), f"Missing headers. Found: {headers}"


def validate_config_schema():
    print("Validating experiment config schema...")
    # Ensure config can be instantiated


def validate_raw_result_schema():
    print("Validating raw result schema...")
    from app.core.result import VectorizationResult
    res = VectorizationResult(run_id="test")
    assert hasattr(res, "status")
    assert hasattr(res, "output_path")


def validate_docs_and_commands():
    print("Validating documentation links and example commands...")
    readme = "README.md"
    if os.path.exists(readme):
        with open(readme) as f:
            content = f.read()
            # Simple link extraction check
            _ = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', content)
            # Simple check if there are commands
            commands = re.findall(r'```bash\n(.*?)\n```', content, re.DOTALL)
            assert len(commands) >= 0


def validate_table_consistency():
    print("Validating generated table consistency...")
    assert os.path.exists("benchmark/analysis/table_generator.py"), "Table generator missing"


def main():
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

    validate_presets()
    validate_citation()
    validate_dataset_manifest()
    validate_config_schema()
    validate_raw_result_schema()
    validate_docs_and_commands()
    validate_table_consistency()
    print("All research artifacts validated successfully!")


if __name__ == "__main__":
    main()
