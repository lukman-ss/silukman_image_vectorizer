"""
_backend_worker_cli.py

CLI wrapper around _backend_worker.run_backend_vectorize().
Used by run_scaling_pilot.py to run backends in isolated subprocesses.

Usage:
  python -m benchmark.runner._backend_worker_cli \
      --backend silukman --input foo.png --output foo.svg --preset balanced
"""
import argparse
import json
import sys


def main() -> None:
    parser = argparse.ArgumentParser(description="Backend worker CLI")
    parser.add_argument("--backend", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--preset", required=True)
    parser.add_argument("--category", default=None)
    args = parser.parse_args()

    from benchmark.runner._backend_worker import run_backend_vectorize

    result = run_backend_vectorize(
        backend_name=args.backend,
        input_path=args.input,
        output_path=args.output,
        preset=args.preset,
        category=args.category,
    )
    print(json.dumps(result))


if __name__ == "__main__":
    main()
