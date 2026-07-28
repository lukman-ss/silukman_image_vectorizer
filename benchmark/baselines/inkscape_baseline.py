import argparse
import json
import os
import subprocess

from benchmark.evaluation.performance_metrics import PerformanceTracker


class InkscapeBaselineRunner:
    """
    Direct Inkscape Baseline Runner (CLI).
    
    Installation Documentation:
    - macOS: `brew install inkscape`
    - Linux: `sudo apt-get install inkscape`
    - Windows: Download from https://inkscape.org/
    
    LIMITATIONS & FAIRNESS (IMPORTANT):
    Inkscape's CLI (especially version 1.0+) makes it notoriously difficult and 
    unstable to precisely control the parameters of the "Trace Bitmap" engine 
    (which under the hood uses a modified multi-scan Potrace). 
    While we can trigger a trace action via CLI (`--actions="SelectionTrace"`), 
    we cannot deterministically pass variables like "color count" or "blur radius" 
    straight from the standard terminal flags without manipulating the user's 
    global XML preferences file.
    
    Therefore:
    1. This baseline will likely run using whatever Trace Bitmap settings were 
       LAST used/saved in the local Inkscape GUI preferences.
    2. It is not fully reproducible across different machines for fine-tuning.
    3. It serves strictly as a "black-box" comparison point.
    """
    
    def __init__(self):
        self.tracker = PerformanceTracker()
        self.inkscape_version = self._get_version()

    def _get_version(self) -> str:
        try:
            # Inkscape --version returns something like "Inkscape 1.3.2 (091e20e, 2023-11-25)"
            result = subprocess.run(["inkscape", "--version"], capture_output=True, text=True, check=True)
            first_line = result.stdout.strip().split('\n')[0]
            return first_line
        except (subprocess.CalledProcessError, FileNotFoundError):
            return "not_installed"

    def _run_cli(self, input_path: str, output_path: str, timeout_sec: int):
        # Modern Inkscape (1.0+) syntax for batch tracing:
        # We must select all, trace, save, and exit.
        actions = "select-all;SelectionTrace;export-filename:{};export-do".format(output_path)
        
        cmd = [
            "inkscape",
            "--without-gui",  # Deprecated in 1.0 but sometimes still required, modern is --batch-process
            "--batch-process",
            f"--actions={actions}",
            input_path
        ]
        
        subprocess.run(cmd, check=True, timeout=timeout_sec, capture_output=True)
        
        if not os.path.exists(output_path) or os.path.getsize(output_path) == 0:
            raise RuntimeError("Inkscape executed but the SVG output is missing or empty.")

    def run(self, input_file: str, output_file: str, timeout: int = 60) -> dict:
        if self.inkscape_version == "not_installed":
            return {"error": "Skipped: Inkscape CLI is not installed or not in PATH."}
            
        if not os.path.exists(input_file):
            return {"error": f"Input file not found: {input_file}"}

        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        try:
            actions = "select-all;SelectionTrace;export-filename:{};export-do".format(output_file)
            cmd = f"inkscape --batch-process --actions='{actions}' {input_file}"
            
            # Measure strictly the CLI execution
            performance = self.tracker.measure(
                func=self._run_cli,
                input_file=input_file,
                output_file=output_file,
                retries=0,
                input_path=input_file,
                output_path=output_file,
                timeout_sec=timeout
            )
            
            return {
                "inkscape_version": self.inkscape_version,
                "invocation": cmd,
                "configuration_note": "GUI preferences fallback (CLI parameter injection not stably supported)",
                "performance": performance
            }
            
        except Exception as e:
            return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Inkscape Direct Baseline Runner")
    parser.add_argument("input", help="Input raster image")
    parser.add_argument("output", help="Output SVG image")
    parser.add_argument("--timeout", type=int, default=60, help="CLI timeout in seconds")
    parser.add_argument("--json", action="store_true", help="Output JSON result")
    
    args = parser.parse_args()
    
    runner = InkscapeBaselineRunner()
    result = runner.run(args.input, args.output, args.timeout)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("=== Inkscape Baseline ===")
        if "error" in result:
            print(f"ERROR/SKIP: {result['error']}")
        else:
            print(f"Version : {result.get('inkscape_version')}")
            print(f"Command : {result.get('invocation')}")
            print(f"Config  : {result.get('configuration_note')}")
            if result.get("performance", {}).get("error"):
                print(f"ERROR   : {result['performance']['error']}")
            else:
                print(f"Success : {result['performance']['success']}")
                print(f"Time (s): {result['performance']['wall_clock_time_seconds']:.3f}")
                print(f"Mem (MB): {result['performance']['peak_memory_bytes'] / (1024*1024):.2f}")


if __name__ == "__main__":
    main()
