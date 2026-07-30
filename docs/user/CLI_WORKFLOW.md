# CLI Workflow

Last updated: 2026-07-30

Silukman Image Vectorizer provides a comprehensive headless Command Line Interface (CLI) for automation and batch processing, alongside the desktop application.

## Run Headless CLI

To see available commands:
```bash
python -m app.cli_headless --help
```

### Available Subcommands

- `gui`: Start the graphical user interface.
- `presets`: List available vectorization presets. Use `--json` for JSON output.
- `vectorize`: Vectorize a single image.
- `batch`: Batch vectorize a directory of images.

### Vectorize a Single Image

```bash
python -m app.cli_headless vectorize input.png -o output.svg -p balanced
```
Options:
- `-p, --preset`: Preset name to use (default: `balanced`).
- `-c, --config`: Path to custom JSON config file (overrides preset).
- `--json`: Output results as JSON.
- `--dry-run`: Simulate without executing.

### Batch Processing

```bash
python -m app.cli_headless batch input_dir/ -o output_dir/ -p high_fidelity --workers 4
```
Options:
- `-o, --output-dir`: Required. Path to output directory.
- `-p, --preset`: Preset name to use (default: `balanced`).
- `--workers`: Number of parallel workers (default: 2).
- `--resume`: Skip files already present in output.
- `--json`: Output summary as JSON.

## Compiling & Building

```bash
python scripts/build_app.py
```
This builds the standalone executable for distribution.
