#!/usr/bin/env python3
"""
Resolve manuscript placeholders from the final benchmark experiment config.

Usage:
    python paper/scripts/resolve_placeholders.py \
        --config experiments/configs/benchmark-v1.yaml \
        --manuscript paper/manuscript.md \
        --output paper/manuscript_resolved.md

Or check consistency only (dry-run):
    python paper/scripts/resolve_placeholders.py \
        --config experiments/configs/benchmark-v1.yaml \
        --check
"""
import argparse
import sys
import os
import yaml


PLACEHOLDER_MAP = {
    "[REPETITION_COUNT]": ("experiment", "repetitions"),
    "[WARMUP_COUNT]": ("experiment", "warmup_runs"),
    "[PRESET_COUNT]": ("presets", None),  # special: length of list
}


def load_config(config_path: str) -> dict:
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def resolve_value(data: dict, section: str, key) -> str:
    if key is None:
        # It's a list; return its length
        return str(len(data.get(section, [])))
    return str(data.get(section, {}).get(key, f"MISSING:{section}.{key}"))


def check_consistency(config_path: str) -> int:
    """Verify the config values match the manuscript protocol requirements."""
    data = load_config(config_path)
    exp = data.get("experiment", {})
    errors = []

    repetitions = exp.get("repetitions", 0)
    warmup = exp.get("warmup_runs", 0)
    presets = data.get("presets", [])

    if repetitions < 3:
        errors.append(
            f"repetitions={repetitions} < 3 (protocol requires >= 3 for full_benchmark)"
        )
    if warmup < 1:
        errors.append(
            f"warmup_runs={warmup} < 1 (protocol requires >= 1)"
        )
    if len(presets) < 1:
        errors.append("No presets configured")

    if errors:
        print("CONSISTENCY ERRORS:")
        for e in errors:
            print(f"  [!] {e}")
        return 1

    print(f"Config consistency OK: repetitions={repetitions}, warmup={warmup}, presets={len(presets)}")
    return 0


def resolve_manuscript(config_path: str, manuscript_path: str, output_path: str) -> int:
    data = load_config(config_path)

    resolved = {}
    for placeholder, (section, key) in PLACEHOLDER_MAP.items():
        resolved[placeholder] = resolve_value(data, section, key)

    with open(manuscript_path, "r", encoding="utf-8") as f:
        content = f.read()

    for placeholder, value in resolved.items():
        count = content.count(placeholder)
        if count > 0:
            content = content.replace(placeholder, value)
            print(f"Resolved {placeholder} -> {value} ({count} occurrences)")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"\nResolved manuscript written to: {output_path}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve manuscript placeholders from experiment config")
    parser.add_argument("--config", required=True, help="Path to YAML experiment config")
    parser.add_argument("--manuscript", default="paper/manuscript.md", help="Path to manuscript")
    parser.add_argument("--output", default="paper/manuscript_resolved.md", help="Output path")
    parser.add_argument("--check", action="store_true", help="Only check consistency, do not resolve")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"Error: config not found: {args.config}")
        return 1

    if args.check:
        return check_consistency(args.config)

    return resolve_manuscript(args.config, args.manuscript, args.output)


if __name__ == "__main__":
    sys.exit(main())
