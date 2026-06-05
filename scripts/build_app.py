from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def clean_directory(path: Path) -> None:
    """Safely remove a directory if it exists."""
    if path.exists():
        print(f"Cleaning directory: {path}")
        try:
            shutil.rmtree(path)
        except Exception as e:
            print(f"Warning: Failed to clean {path}: {e}")


def find_pyinstaller(project_root: Path) -> str | None:
    """Find PyInstaller from the local virtual environment or system PATH."""
    candidates = []
    if sys.platform == "win32":
        candidates.extend([
            project_root / ".venv" / "Scripts" / "pyinstaller.exe",
            project_root / ".venv" / "Scripts" / "pyinstaller",
        ])
    else:
        candidates.append(project_root / ".venv" / "bin" / "pyinstaller")

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    return shutil.which("pyinstaller")


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]

    build_dir = project_root / "build"
    dist_dir = project_root / "dist"
    clean_directory(build_dir)
    clean_directory(dist_dir)

    spec_file = project_root / "image_vectorizer.spec"

    if not spec_file.exists():
        print(f"Error: Specification file {spec_file} not found.")
        return 1

    print("Starting PyInstaller build process...")

    pyinstaller_cmd = find_pyinstaller(project_root)
    if pyinstaller_cmd is None:
        print("Error: PyInstaller is not installed in the virtual environment or system PATH.")
        print("Please install requirements first using: pip install -r requirements.txt")
        return 1

    cmd = [pyinstaller_cmd, "--clean", "--noconfirm", str(spec_file)]

    try:
        subprocess.run(cmd, check=True, cwd=str(project_root))
        print("Build completed successfully!")
        clean_directory(build_dir)
        return 0
    except subprocess.CalledProcessError as e:
        print(f"Build failed with error code: {e.returncode}")
        return e.returncode
    except Exception as e:
        print(f"An unexpected error occurred during build: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
