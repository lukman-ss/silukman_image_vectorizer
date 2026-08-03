## Generated Manuscript Snippets

### Dataset and Success Rate
The evaluation dataset consisted of 61 unique images.
Across all configured conditions, the overall execution success rate was 96.7%.

### Baseline Ranking (Factual)
Based on the primary quality metric, the evaluated backends achieved the following mean scores:
- vtracer: mean = 0.8550, median = 0.8920 (n=531)
- silukman: mean = 0.8307, median = 0.8601 (n=531)

### Preset Trade-offs (Silukman)
For the Silukman backend, the presets yielded the following measurements:
- low_complexity: quality mean = 0.7713, runtime mean = 0.0712s
- balanced: quality mean = 0.8218, runtime mean = 0.1068s
- high_fidelity: quality mean = 0.8990, runtime mean = 0.0950s

### Category Results
Performance observed across dataset categories:
- photograph: mean quality = 0.7225, median = 0.7549
- logo: mean quality = 0.9035, median = 0.9185
- binary_graphic: mean quality = 0.8805, median = 0.8927
- icon: mean quality = 0.8381, median = 0.8643
- illustration: mean quality = 0.8445, median = 0.8696

### Table & Figure References
- **Table 10**: Summary of dataset dimensions, categories, and execution status.
- **Table 11**: Overall quality metrics across all backends and presets.
- **Table 13**: End-to-end runtime distributions.
- **Figure 8**: Distribution of the primary quality metric by backend.
- **Figure 14**: Pareto frontier analysis comparing quality versus SVG size.