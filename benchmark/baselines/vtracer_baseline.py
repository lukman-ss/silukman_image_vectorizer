import argparse
import json
import os
import sys
import vtracer

from benchmark.evaluation.performance_metrics import PerformanceTracker

# Add root directory to sys.path if needed, but we can assume it's run from root
# using `python -m benchmark.baselines.vtracer_baseline`


class VTracerBaselineRunner:
    """
    Direct VTracer baseline runner.
    
    Purpose: 
    To evaluate the bare VTracer performance and output quality WITHOUT 
    Silukman's preprocessing (blur, quantization, edge-preservation, etc.) 
    and post-processing pipelines. This ensures we can measure the exact 
    contribution of the Silukman pipeline.
    
    Parameter Mapping:
    Silukman Config -> VTracer Parameter:
    - colormode -> colormode
    - hierarchical -> hierarchical
    - mode -> mode
    - filter_speckle -> filter_speckle
    - color_precision -> color_precision
    - layer_difference -> layer_difference
    - corner_threshold -> corner_threshold
    - length_threshold -> length_threshold
    - max_iterations -> max_iterations
    - splice_threshold -> splice_threshold
    - path_precision -> path_precision
    
    [UNMAPPED PARAMETERS - Silukman Exclusive]
    - engine_type
    - color_mode (the enum string)
    - color_count (K-means quantization is skipped)
    - preserve_edges (Preprocessing step is skipped)
    - remove_background (Preprocessing step is skipped)
    - bg_tolerance (Preprocessing step is skipped)
    """
    
    def __init__(self):
        self.tracker = PerformanceTracker()
        self.vtracer_version = vtracer.__version__ if hasattr(vtracer, '__version__') else "unknown"

    def get_preset_config(self, preset_name: str, presets_path: str = "app/config/presets.json") -> dict:
        with open(presets_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if preset_name not in data["presets"]:
                raise ValueError(f"Preset '{preset_name}' not found.")
            return data["presets"][preset_name]["config"]

    def extract_vtracer_params(self, silukman_config: dict) -> dict:
        """Extracts only the parameters native to VTracer."""
        vtracer_keys = [
            "colormode", "hierarchical", "mode", "filter_speckle",
            "color_precision", "layer_difference", "corner_threshold",
            "length_threshold", "max_iterations", "splice_threshold",
            "path_precision"
        ]
        
        params = {}
        for k in vtracer_keys:
            if k in silukman_config:
                params[k] = silukman_config[k]
        return params

    def run(self, input_file: str, output_file: str, preset_name: str) -> dict:
        if not os.path.exists(input_file):
            return {"error": f"Input file not found: {input_file}"}

        try:
            silukman_config = self.get_preset_config(preset_name)
        except Exception as e:
            return {"error": str(e)}

        vtracer_params = self.extract_vtracer_params(silukman_config)
        
        # Unmapped parameters (for logging purposes)
        unmapped = {k: v for k, v in silukman_config.items() if k not in vtracer_params}

        # Ensure output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
        
        # Warmup (on a dummy call or the same call? Warmup might overwrite or take long)
        # We will just do a dry import warmup
        
        # Build the exact kwargs to pass
        kwargs = vtracer_params.copy()
        
        # Measure
        performance = self.tracker.measure(
            func=vtracer.convert_image_to_svg_py,
            input_file=input_file,
            output_file=output_file,
            retries=0, # Baselines don't retry by default
            image_path=input_file,
            out_path=output_file,
            **kwargs
        )
        
        return {
            "vtracer_version": self.vtracer_version,
            "preset": preset_name,
            "invocation": f"vtracer.convert_image_to_svg_py('{input_file}', '{output_file}', **{vtracer_params})",
            "vtracer_parameters": vtracer_params,
            "unmapped_silukman_parameters": unmapped,
            "performance": performance
        }


def main():
    parser = argparse.ArgumentParser(description="VTracer Direct Baseline Runner")
    parser.add_argument("input", help="Input raster image")
    parser.add_argument("output", help="Output SVG image")
    parser.add_argument("--preset", default="balanced", help="Silukman preset to map from")
    parser.add_argument("--json", action="store_true", help="Output JSON result")
    
    args = parser.parse_args()
    
    runner = VTracerBaselineRunner()
    result = runner.run(args.input, args.output, args.preset)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("=== VTracer Baseline ===")
        print(f"Version : {result.get('vtracer_version')}")
        print(f"Preset  : {result.get('preset')}")
        print(f"Command : {result.get('invocation')}")
        if result.get("performance", {}).get("error"):
            print(f"ERROR   : {result['performance']['error']}")
        else:
            print(f"Success : {result['performance']['success']}")
            print(f"Time (s): {result['performance']['wall_clock_time_seconds']:.3f}")
            print(f"Mem (MB): {result['performance']['peak_memory_bytes'] / (1024*1024):.2f}")


if __name__ == "__main__":
    main()
