import argparse
import json
import os
import subprocess
import tempfile
import cv2
import numpy as np
import time

from benchmark.runner.process_utils import run_isolated_process, ProcessExecutionError
from benchmark.evaluation.performance_metrics import PerformanceTracker


class PotraceBaselineRunner:
    """
    Direct Potrace baseline runner.
    
    Installation Documentation:
    Potrace is a native command-line tool and is NOT included in Python dependencies.
    - macOS: `brew install potrace`
    - Ubuntu/Debian: `sudo apt-get install potrace`
    - Windows: Download from http://potrace.sourceforge.net/
    
    Purpose & Fairness:
    Potrace ONLY traces strictly black-and-white (binary) bitmaps. It is inherently 
    incapable of tracing multi-color logos, gradients, or photographs. Comparing 
    Potrace to VTracer/Silukman on full-color tasks is mathematically unfair and 
    fundamentally flawed. Therefore, this baseline automatically skips any image 
    category that is not explicitly 'binary_graphic' (or monochrome synthetic types).
    
    Preprocessing:
    Because Potrace only accepts PBM/BMP files, this adapter converts the input 
    raster into a 1-bit monochrome Bitmap (BMP) using OpenCV thresholding before 
    passing it to the CLI.
    """
    
    ALLOWED_CATEGORIES = {"binary_graphic", "monochrome_silhouette"}

    def __init__(self):
        self.tracker = PerformanceTracker()
        self.potrace_version = self._get_version()

    def _get_version(self) -> str:
        try:
            result = subprocess.run(["potrace", "--version"], capture_output=True, text=True, check=True)
            # Example output: "potrace 1.16. ..."
            first_line = result.stdout.split('\n')[0]
            return first_line
        except Exception:
            return "not_installed"

    def _preprocess_to_bmp(self, input_file: str, temp_bmp: str):
        """Converts image to binary BMP format for Potrace."""
        img = cv2.imread(input_file, cv2.IMREAD_UNCHANGED)
        if img is None:
            raise FileNotFoundError(f"Cannot read image: {input_file}")
            
        # Composite alpha over white if needed
        if len(img.shape) == 3 and img.shape[2] == 4:
            b, g, r, a = cv2.split(img)
            alpha_factor = a / 255.0
            bg = np.ones_like(b) * 255
            b = (b * alpha_factor + bg * (1 - alpha_factor)).astype(b.dtype)
            g = (g * alpha_factor + bg * (1 - alpha_factor)).astype(g.dtype)
            r = (r * alpha_factor + bg * (1 - alpha_factor)).astype(r.dtype)
            img = cv2.merge((b, g, r))
            
        if len(img.shape) == 3:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        else:
            gray = img
            
        # Strict Otsu Thresholding to convert to binary
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
        
        # Save as BMP (Potrace supports uncompressed BMP)
        cv2.imwrite(temp_bmp, binary)

    def _run_cli(self, bmp_path: str, svg_path: str, timeout_sec: int):
        # -s outputs SVG.
        cmd = ["potrace", bmp_path, "-s", "-o", svg_path]
        exit_code, stdout, stderr = run_isolated_process(cmd, timeout_sec)
        
        if exit_code != 0:
            raise RuntimeError(f"Potrace error (Code {exit_code}): {stderr}")
        
        if not os.path.exists(svg_path) or os.path.getsize(svg_path) == 0:
            raise RuntimeError("Potrace succeeded but generated an empty or missing SVG.")

    def run(self, input_file: str, output_file: str, category: str, timeout: int = 10) -> dict:
        if self.potrace_version == "not_installed":
            return {"error": "Potrace CLI is not installed or not in PATH."}
            
        if category.lower() not in self.ALLOWED_CATEGORIES:
            return {
                "error": f"Skipped: Category '{category}' is unfair for Potrace. Only {self.ALLOWED_CATEGORIES} allowed."
            }
            
        if not os.path.exists(input_file):
            return {"error": f"Input file not found: {input_file}"}

        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        temp_bmp = tempfile.mktemp(suffix=".bmp")
        try:
            # Preprocessing is NOT included in the core performance timing, 
            # because we only want to measure the vectorization engine speed.
            self._preprocess_to_bmp(input_file, temp_bmp)
            
            cmd = f"potrace {os.path.basename(temp_bmp)} -s -o {os.path.basename(output_file)}"
            
            # Measure strictly the CLI execution
            performance = self.tracker.measure(
                func=self._run_cli,
                input_file=temp_bmp,   # Tracking BMP size as input, not the original PNG
                output_file=output_file,
                retries=0,
                bmp_path=temp_bmp,
                svg_path=output_file,
                timeout_sec=timeout
            )
            
            return {
                "potrace_version": self.potrace_version,
                "category": category,
                "invocation": cmd,
                "performance": performance
            }
            
        except Exception as e:
            return {"error": str(e)}
        finally:
            if os.path.exists(temp_bmp):
                os.remove(temp_bmp)


def main():
    parser = argparse.ArgumentParser(description="Potrace Direct Baseline Runner")
    parser.add_argument("input", help="Input raster image")
    parser.add_argument("output", help="Output SVG image")
    parser.add_argument("--category", required=True, help="Image category (e.g. binary_graphic)")
    parser.add_argument("--timeout", type=int, default=10, help="CLI timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Output JSON result")
    
    args = parser.parse_args()
    
    runner = PotraceBaselineRunner()
    result = runner.run(args.input, args.output, args.category, args.timeout)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("=== Potrace Baseline ===")
        if "error" in result:
            print(f"ERROR/SKIP: {result['error']}")
        else:
            print(f"Version : {result.get('potrace_version')}")
            print(f"Command : {result.get('invocation')}")
            if result.get("performance", {}).get("error"):
                print(f"ERROR   : {result['performance']['error']}")
            else:
                print(f"Success : {result['performance']['success']}")
                print(f"Time (s): {result['performance']['wall_clock_time_seconds']:.3f}")
                print(f"Mem (MB): {result['performance']['peak_memory_bytes'] / (1024*1024):.2f}")


if __name__ == "__main__":
    main()
