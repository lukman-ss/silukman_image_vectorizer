## Generated Manuscript Snippets

### Dataset and Success Rate
The evaluation dataset consisted of 10 unique images.
Across all configured conditions, the overall execution success rate was 100.0%.

### Baseline Ranking (Factual)
Based on the primary quality metric, the evaluated backends achieved the following mean scores:
- silukman: mean = 0.8793, median = 0.9539 (n=20)

### Preset Trade-offs (Silukman)
For the Silukman backend, the presets yielded the following measurements:
- balanced: quality mean = 0.9053, runtime mean = 0.0613s
- low_complexity: quality mean = 0.8533, runtime mean = 0.0504s

### Category Results
Performance observed across dataset categories:
- geometric_shapes: mean quality = 0.9772, median = 0.9772
- flat_logo: mean quality = 0.9868, median = 0.9868
- gradients: mean quality = 0.9075, median = 0.9075
- thin_lines: mean quality = 0.5251, median = 0.5251
- curves: mean quality = 0.9197, median = 0.9197
- pseudo_text: mean quality = 0.8116, median = 0.8116
- transparent_shapes: mean quality = 0.7735, median = 0.7735
- noisy_edges: mean quality = 0.9586, median = 0.9586
- overlapping_objects: mean quality = 0.9602, median = 0.9602
- monochrome_silhouette: mean quality = 0.9724, median = 0.9724

### Table & Figure References
- **Table 10**: Summary of dataset dimensions, categories, and execution status.
- **Table 11**: Overall quality metrics across all backends and presets.
- **Table 13**: End-to-end runtime distributions.
- **Figure 8**: Distribution of the primary quality metric by backend.
- **Figure 14**: Pareto frontier analysis comparing quality versus SVG size.