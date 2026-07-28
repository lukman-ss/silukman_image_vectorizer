import os
import cv2
from typing import Dict, Any, Optional

from benchmark.evaluation.rasterizer import SVGRasterizer
from benchmark.evaluation.pixel_metrics import PixelMetricsCalculator
from benchmark.evaluation.histogram_metrics import HistogramMetricsCalculator
from benchmark.evaluation.ssim_metrics import SSIMCalculator
from benchmark.evaluation.edge_metrics import EdgeMetricsCalculator
from benchmark.evaluation.svg_metrics import SVGComplexityCalculator


class UnifiedQualityEvaluator:
    """
    Unified evaluator that coordinates all metrics (Quality, Complexity, Performance)
    into a single standardized JSON-safe dictionary.
    """
    
    def __init__(self, temp_dir: str = "/tmp"):
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)
        
        self.rasterizer = SVGRasterizer()
        self.pixel_calc = PixelMetricsCalculator()
        self.hist_calc = HistogramMetricsCalculator()
        self.ssim_calc = SSIMCalculator()
        self.edge_calc = EdgeMetricsCalculator()
        self.svg_calc = SVGComplexityCalculator()

    def evaluate(
        self, 
        image_id: str, 
        preset: str, 
        original_raster_path: str, 
        svg_path: str, 
        performance_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Runs the full evaluation suite.
        
        If a metric fails (e.g. invalid SVG, SSIM size too small), its value 
        will be explicitly set to `null` (None in Python) and the error will be 
        appended to the metadata. Default values (like 0) are strictly avoided 
        for failed computations to prevent silent corruption of benchmark data.
        """
        record = {
            "image_id": image_id,
            "preset": preset,
            "quality": {
                "mae": None,
                "rmse": None,
                "psnr": None,
                "ssim": None,
                "histogram_correlation": None,
                "edge_f1": None
            },
            "complexity": {
                "svg_bytes": None,
                "path_count": None,
                "command_count": None
            },
            "performance": {
                "duration_seconds": None,
                "peak_memory_mb": None
            },
            "errors": []
        }
        
        # 1. Performance Formatting (if provided)
        if performance_data:
            record["performance"]["duration_seconds"] = performance_data.get("wall_clock_time_seconds")
            peak_bytes = performance_data.get("peak_memory_bytes")
            if peak_bytes is not None:
                record["performance"]["peak_memory_mb"] = peak_bytes / (1024 * 1024)
            if performance_data.get("error"):
                record["errors"].append(f"Performance Tracker Error: {performance_data['error']}")
                
        # 2. Complexity Metrics
        svg_metrics = self.svg_calc.calculate(svg_path)
        if "error" in svg_metrics:
            record["errors"].append(f"SVG Metrics Error: {svg_metrics['error']}")
        else:
            record["complexity"]["svg_bytes"] = svg_metrics.get("svg_bytes")
            record["complexity"]["path_count"] = svg_metrics.get("path_count")
            record["complexity"]["command_count"] = svg_metrics.get("total_path_command_count")
            
        # 3. Quality Metrics (Requires Rasterization)
        # Load original image to get target dimensions
        img_orig = cv2.imread(original_raster_path, cv2.IMREAD_UNCHANGED)
        if img_orig is None:
            record["errors"].append(f"Failed to load original raster: {original_raster_path}")
            return record
            
        h, w = img_orig.shape[:2]
        temp_raster_out = os.path.join(self.temp_dir, f"temp_{image_id}_{preset}.png")
        
        raster_result = self.rasterizer.rasterize(svg_path, temp_raster_out, w, h)
        if not raster_result["success"]:
            record["errors"].append(f"Rasterizer Error: {raster_result.get('error')}")
            return record
            
        # Load the newly rasterized SVG
        img_svg = cv2.imread(temp_raster_out, cv2.IMREAD_UNCHANGED)
        if img_svg is None:
            record["errors"].append("Failed to load the rasterized SVG output.")
            return record
            
        # Clean up temp file
        if os.path.exists(temp_raster_out):
            os.remove(temp_raster_out)
            
        # 3a. Pixel Metrics
        try:
            pixel_res = self.pixel_calc.calculate(img_orig, img_svg)
            record["quality"]["mae"] = pixel_res.get("mae")
            record["quality"]["rmse"] = pixel_res.get("rmse")
            record["quality"]["psnr"] = pixel_res.get("psnr")
        except Exception as e:
            record["errors"].append(f"Pixel Metrics Error: {str(e)}")
            
        # 3b. Histogram Metrics
        try:
            hist_res = self.hist_calc.calculate(img_orig, img_svg)
            record["quality"]["histogram_correlation"] = hist_res.get("aggregate_correlation")
        except Exception as e:
            record["errors"].append(f"Histogram Metrics Error: {str(e)}")
            
        # 3c. SSIM Metrics
        try:
            ssim_res = self.ssim_calc.calculate(img_orig, img_svg)
            if "error" in ssim_res:
                record["errors"].append(f"SSIM Error: {ssim_res['error']}")
            else:
                record["quality"]["ssim"] = ssim_res.get("ssim")
        except Exception as e:
            record["errors"].append(f"SSIM Exception: {str(e)}")
            
        # 3d. Edge Metrics
        try:
            edge_res = self.edge_calc.calculate(img_orig, img_svg)
            record["quality"]["edge_f1"] = edge_res.get("f1")
        except Exception as e:
            record["errors"].append(f"Edge Metrics Error: {str(e)}")
            
        return record
