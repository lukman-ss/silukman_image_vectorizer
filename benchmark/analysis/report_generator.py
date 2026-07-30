import json
import os
import shutil

from benchmark.analysis.aggregator import BenchmarkAggregator
from benchmark.analysis.failure_analysis import FailureAnalyzer
from benchmark.analysis.plot_generator import PlotGenerator
from benchmark.analysis.qualitative_generator import QualitativeGenerator
from benchmark.analysis.table_generator import TableGenerator


class ReportGenerator:
    def __init__(self, exp_dir: str):
        self.exp_dir = exp_dir
        self.report_dir = os.path.join(exp_dir, "report")

        # Output subdirectories
        self.tables_dir = os.path.join(self.report_dir, "tables")
        self.figures_dir = os.path.join(self.report_dir, "figures")
        self.qualitative_dir = os.path.join(self.report_dir, "qualitative")
        self.failures_dir = os.path.join(self.report_dir, "failures")

        for d in [self.tables_dir, self.figures_dir, self.qualitative_dir, self.failures_dir]:
            os.makedirs(d, exist_ok=True)

    def _run_prerequisites(self):
        # 1. Aggregate runs -> aggregated.json
        agg = BenchmarkAggregator(os.path.join(self.exp_dir, "runs.jsonl"))
        agg_path = os.path.join(self.exp_dir, "aggregated.json")
        agg.save(agg_path)

        # 2. Failure Analysis -> failure_report.json
        fail = FailureAnalyzer(os.path.join(self.exp_dir, "runs.jsonl"))
        fail_path = os.path.join(self.exp_dir, "failure_report.json")
        fail.save_report(fail_path)

        # Move failures to failures dir
        shutil.copy(fail_path, os.path.join(self.failures_dir, "failure_report.json"))

    def _generate_tables(self):
        tabs = TableGenerator(self.exp_dir)
        # Override output dir to match report spec
        tabs.output_dir = self.tables_dir
        tabs.generate_all()

    def _generate_figures(self):
        try:
            plots = PlotGenerator(self.exp_dir)
            plots.output_dir = self.figures_dir
            plots.generate_all()
        except ImportError:
            print(
                "Warning: Skipping plot generation because matplotlib/seaborn/pandas are missing."
            )

    def _generate_qualitative(self):
        qual = QualitativeGenerator(self.exp_dir)
        qual.output_dir = self.qualitative_dir
        qual.generate_sheets()

    def _generate_summary_and_repro(self):
        # Read env data
        manifest_file = os.path.join(self.exp_dir, "manifest.json")
        git_commit = "unknown"
        if os.path.exists(manifest_file):
            with open(manifest_file, "r") as f:
                man = json.load(f)
                git_commit = man.get("environment", {}).get("git_commit", "unknown")

        # summary.md
        summary = f"""# Benchmark Experiment Summary
Generated from raw data in `{self.exp_dir}`.

## Overview
This report contains fully automated statistical aggregations, qualitative sheets, and performance metrics.

## Artifacts
- **Tables**: See `tables/` for CSV, Markdown, and LaTeX representations of overall and per-category stats.
- **Figures**: See `figures/` for publication-ready PNG/PDF plots mapping trade-offs (e.g. Quality vs Complexity).
- **Qualitative**: See `qualitative/` for side-by-side visual assessments using unbiased selection rules.
- **Failures**: See `failures/` for transparency into crashed or timed-out conversions.
"""
        with open(os.path.join(self.report_dir, "summary.md"), "w") as f:
            f.write(summary)

        # reproducibility.md
        repro = f"""# Reproducibility Statement

## Source Integrity
- **Git Commit**: `{git_commit}`
- **Data Provenance**: All tables and figures in this report are deterministically derived from `runs.jsonl`.
- **Exclusion Rule**: Failed runs are strictly isolated but NOT hidden. Mean/Median metrics naturally ignore failed subsets.
- **Environment**: Full OS, hardware, and dependency snapshots are stored in `manifest.json`.

To rerun this exact experiment:
`silukman-vectorizer benchmark run --resume-id {os.path.basename(self.exp_dir)} --retry-failed`
"""
        with open(os.path.join(self.report_dir, "reproducibility.md"), "w") as f:
            f.write(repro)

    def run(self):
        print("Generating prerequisites...")
        self._run_prerequisites()
        print("Generating tables...")
        self._generate_tables()
        print("Generating figures...")
        self._generate_figures()
        print("Generating qualitative sheets...")
        self._generate_qualitative()
        print("Writing summaries...")
        self._generate_summary_and_repro()
        print(f"Report generated successfully at: {self.report_dir}")
