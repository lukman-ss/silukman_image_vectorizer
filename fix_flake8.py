import re

files_to_fix = [
    ("app/cli_headless.py", [
        ('parser_gui = subparsers.add_parser("gui", help="Start the graphical user interface")', 'subparsers.add_parser("gui", help="Start the graphical user interface")'),
        ('print(f"Batch processing complete.")', 'print("Batch processing complete.")'),
        ('logger = setup_logger("silukman", as_json=as_json)', 'setup_logger("silukman", as_json=as_json)')
    ]),
    ("app/core/logging.py", [
        ('"preset", "duration", "error_category" ', '"preset", "duration", "error_category"')
    ]),
    ("app/core/study_logger.py", [
        ('Requirements satisfied:\n    \n    A local', 'Requirements satisfied:\n\n    A local')
    ]),
    ("benchmark/analysis/plot_generator.py", [
        ('ax = sns.scatterplot(\n            data=df', 'sns.scatterplot(\n            data=df')
    ]),
    ("benchmark/analysis/qualitative_generator.py", [
        ('md_lines.append(f"<i>(Output SVG linked here)</i>")', 'md_lines.append("<i>(Output SVG linked here)</i>")')
    ]),
    ("benchmark/runner/env_capture.py", [
        ('    unsafe_substrings = {"KEY", "TOKEN", "PASS", "SECRET", "AUTH", "CRED"}\n\n', '')
    ]),
    ("benchmark/scripts/validate_dataset.py", [
        ('    schema_file = Path(schema_path)\n', '')
    ]),
    ("paper/scripts/restore_manuscript.py", [
        ('synthetic_section = f"""\n## Synthetic Smoke-Test Validation', 'synthetic_section = """\n## Synthetic Smoke-Test Validation')
    ]),
    ("scripts/run_color_benchmark.py", [
        ('\n\n\ndef run_benchmark():', '\n\ndef run_benchmark():')
    ]),
    ("scripts/run_dev.py", [
        ('\n\n\nif __name__ == "__main__":', '\n\nif __name__ == "__main__":')
    ]),
    ("scripts/validate_research_artifacts.py", [
        ("links = re.findall(r'\\[([^\\]]+)\\]\\(([^)]+)\\)', content)", "_ = re.findall(r'\\[([^\\]]+)\\]\\(([^)]+)\\)', content)")
    ]),
    ("tests/integration/test_svg_security.py", [
        ('except Exception as e:', 'except Exception:')
    ])
]

for filepath, replacements in files_to_fix:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

print("Fixes applied.")
