import json
import os
import pandas as pd
from typing import Dict, Any

class TableGenerator:
    def __init__(self, exp_dir: str):
        self.exp_dir = exp_dir
        self.aggregated_file = os.path.join(exp_dir, "aggregated.json")
        self.runs_file = os.path.join(exp_dir, "runs.jsonl")
        
        with open(self.aggregated_file, 'r', encoding='utf-8') as f:
            self.agg_data = json.load(f)
            
        self.output_dir = os.path.join(exp_dir, "tables")
        os.makedirs(self.output_dir, exist_ok=True)
        
    def _save_table(self, df: pd.DataFrame, name: str):
        if df.empty: return
        df.to_csv(os.path.join(self.output_dir, f"{name}.csv"), index=False)
        with open(os.path.join(self.output_dir, f"{name}.md"), 'w') as f:
            f.write(df.to_markdown(index=False))
        with open(os.path.join(self.output_dir, f"{name}.tex"), 'w') as f:
            f.write(df.to_latex(index=False))

    def generate_overall_benchmark(self):
        records = []
        for backend, presets in self.agg_data.get("overall", {}).items():
            for preset, stats in presets.items():
                r = {"Backend": backend, "Preset": preset}
                r["Total Runs"] = stats["runs"]["total"]
                r["Success Rate (%)"] = round(stats["runs"]["success"] / max(stats["runs"]["total"], 1) * 100, 2)
                
                metrics = stats.get("metrics", {})
                
                # Quality
                if "ssim" in metrics: r["SSIM (Median)"] = round(metrics["ssim"].get("median", 0), 4)
                if "rmse" in metrics: r["RMSE (Median)"] = round(metrics["rmse"].get("median", 0), 2)
                if "edge_f1" in metrics: r["Edge F1 (Median)"] = round(metrics["edge_f1"].get("median", 0), 4)
                
                # Complexity
                if "svg_bytes" in metrics: r["SVG Size KB (Median)"] = round(metrics["svg_bytes"].get("median", 0) / 1024, 2)
                if "path_count" in metrics: r["Paths (Median)"] = metrics["path_count"].get("median", 0)
                
                # Runtime
                if "wall_clock_time_seconds" in metrics: 
                    r["Runtime s (Median)"] = round(metrics["wall_clock_time_seconds"].get("median", 0), 3)
                    
                records.append(r)
                
        df = pd.DataFrame(records)
        self._save_table(df, "overall_benchmark")
        
    def generate_per_category_benchmark(self):
        records = []
        for backend, presets in self.agg_data.get("by_category", {}).items():
            for preset, categories in presets.items():
                for cat, stats in categories.items():
                    r = {"Backend": backend, "Preset": preset, "Category": cat}
                    r["Success"] = stats["runs"]["success"]
                    
                    metrics = stats.get("metrics", {})
                    if "ssim" in metrics: r["SSIM (Median)"] = round(metrics["ssim"].get("median", 0), 4)
                    if "wall_clock_time_seconds" in metrics: r["Runtime (s)"] = round(metrics["wall_clock_time_seconds"].get("median", 0), 3)
                    
                    records.append(r)
        
        df = pd.DataFrame(records)
        self._save_table(df, "per_category_benchmark")

    def generate_failure_rates(self):
        fail_file = os.path.join(self.exp_dir, "failure_report.json")
        if not os.path.exists(fail_file): return
        with open(fail_file, 'r') as f:
            fail_data = json.load(f)
            
        records = []
        for cls, data in fail_data.get("by_class", {}).items():
            if data["count"] > 0:
                records.append({
                    "Failure Class": cls.capitalize(),
                    "Count": data["count"],
                    "% of Total Failures": round(data["count"] / max(fail_data["total_failures"], 1) * 100, 2)
                })
        self._save_table(pd.DataFrame(records), "failure_rates")
        
    def generate_environment(self):
        env_file = os.path.join(self.exp_dir, "manifest.json")
        if not os.path.exists(env_file): return
        with open(env_file, 'r') as f:
            env_data = json.load(f)
            
        records = []
        for k, v in env_data.get("environment", {}).items():
            if isinstance(v, (str, int, float)):
                records.append({"Parameter": k, "Value": v})
        self._save_table(pd.DataFrame(records), "environment")
        
    def generate_all(self):
        self.generate_overall_benchmark()
        self.generate_per_category_benchmark()
        self.generate_failure_rates()
        self.generate_environment()
        print(f"Tables generated in {self.output_dir}")
