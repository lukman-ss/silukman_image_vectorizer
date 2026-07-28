import os
import json
from collections import defaultdict
from typing import Dict, Any, List

class QualitativeGenerator:
    def __init__(self, exp_dir: str):
        self.exp_dir = exp_dir
        self.runs_file = os.path.join(exp_dir, "runs.jsonl")
        self.output_dir = os.path.join(exp_dir, "report", "qualitative")
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.raw_data = self._load_data()
        
    def _load_data(self) -> List[Dict[str, Any]]:
        data = []
        if not os.path.exists(self.runs_file): return data
        with open(self.runs_file, 'r', encoding='utf-8') as f:
            for line in f:
                if not line.strip(): continue
                try:
                    data.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return data

    def _select_samples(self) -> List[str]:
        """
        Fair selection rule:
        For each category, we pick the images with the Best, Median, and Worst 
        SSIM scores (across the 'silukman:balanced' baseline if available).
        This guarantees we don't cherry-pick only the best looking results.
        """
        # Group by category -> image -> median SSIM for a standard config
        cat_img_scores = defaultdict(lambda: defaultdict(list))
        
        for r in self.raw_data:
            if r.get("status") == "success" and r.get("backend") == "silukman" and r.get("preset") == "balanced":
                cat = r.get("category", "unknown")
                img = r.get("image_id", "unknown")
                ssim = r.get("quality", {}).get("ssim")
                if ssim is not None:
                    cat_img_scores[cat][img].append(ssim)
                    
        selected_images = set()
        
        for cat, img_scores in cat_img_scores.items():
            # average the ssim if there were multiple repetitions
            avg_scores = {}
            for img, scores in img_scores.items():
                avg_scores[img] = sum(scores) / len(scores)
                
            sorted_imgs = sorted(avg_scores.items(), key=lambda x: x[1])
            if not sorted_imgs: continue
            
            worst_img = sorted_imgs[0][0]
            best_img = sorted_imgs[-1][0]
            median_img = sorted_imgs[len(sorted_imgs)//2][0]
            
            selected_images.update([worst_img, median_img, best_img])
            
        return list(selected_images)

    def generate_sheets(self):
        selected_images = self._select_samples()
        if not selected_images:
            return
            
        # Group runs by image ID
        img_runs = defaultdict(list)
        for r in self.raw_data:
            img = r.get("image_id")
            if img in selected_images and r.get("status") == "success":
                # We only need the first repetition for qualitative visual sheet
                if r.get("repetition", 1) == 1:
                    img_runs[img].append(r)
                    
        md_lines = [
            "# Qualitative Comparison Sheet",
            "",
            "**Selection Rule Documented**: Samples were explicitly chosen to represent the spectrum of vectorization quality. "
            "For each category, the images representing the Best, Median, and Worst SSIM scores were chosen. "
            "This prevents cherry-picking and shows the tool's limitations transparently.",
            ""
        ]
        
        for img_id, runs in img_runs.items():
            md_lines.append(f"## Sample: {img_id}")
            
            # Create an HTML table for side-by-side comparison
            md_lines.append("<table><tr>")
            
            # Since we can't easily embed original raster without the manifest paths in this isolated context, 
            # we will just list the SVGs side by side.
            for run in runs:
                backend = run.get("backend")
                preset = run.get("preset")
                
                metrics = {}
                metrics.update(run.get("quality", {}))
                metrics.update(run.get("complexity", {}))
                metrics.update(run.get("performance", {}))
                
                ssim = round(metrics.get("ssim", 0), 3)
                runtime = round(metrics.get("wall_clock_time_seconds", 0), 2)
                size_kb = round(metrics.get("svg_bytes", 0) / 1024, 1)
                paths = metrics.get("path_count", 0)
                
                md_lines.append('<td valign="top">')
                md_lines.append(f"<b>{backend} ({preset})</b><br>")
                md_lines.append(f"SSIM: {ssim}<br>")
                md_lines.append(f"Size: {size_kb} KB<br>")
                md_lines.append(f"Paths: {paths}<br>")
                md_lines.append(f"Time: {runtime} s<br>")
                # Placeholder for SVG embedding
                md_lines.append(f"<i>(Output SVG linked here)</i>")
                md_lines.append('</td>')
                
            md_lines.append("</tr></table>\n")
            
        with open(os.path.join(self.output_dir, "qualitative_sheet.md"), 'w', encoding='utf-8') as f:
            f.write("\n".join(md_lines))
            
        print(f"Qualitative sheet generated in {self.output_dir}")
