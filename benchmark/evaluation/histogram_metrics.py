import cv2
import numpy as np
from typing import Dict, Union


class HistogramMetricsCalculator:
    """
    Calculates color histogram similarity between two images.
    
    Documentation & Limitations:
    - Normalization: Histograms are normalized using L1 norm (sum of all bins = 1) 
      before comparison. This ensures that the scale of the image size does not 
      skew the metrics.
    - Bin Count: 256 bins per channel (one for each possible 8-bit value).
    - Color Space: RGB (calculations are done per-channel: R, G, B).
    - Sensitivity to Spatial Changes: Histogram metrics are purely statistical and 
      SPATIALLY INVARIANT. If pixels are completely shuffled (e.g., noise), the 
      histogram similarity might still be 100%. Therefore, this metric must never 
      be used alone, but rather alongside spatial metrics like MAE or SSIM.
    - Interpreting Metrics:
      - Correlation: Ranges from 1.0 (perfect match) to -1.0 (total mismatch). 
        Usually bounded [0, 1] for similar images.
      - Bhattacharyya Distance: Ranges from 0.0 (perfect match) to 1.0 (total mismatch).
        Lower is better.
    """
    
    def __init__(self, bg_color: tuple = (255, 255, 255)):
        self.bg_color = np.array(bg_color, dtype=np.float32)

    def _composite_alpha_uint8(self, img: np.ndarray) -> np.ndarray:
        """
        Composites an RGBA or RGB image onto a solid background color.
        Returns a uint8 RGB array suitable for cv2 histogram calculations.
        """
        if img.ndim == 2:
            img = np.stack([img]*3, axis=-1)
            
        img = img.astype(np.float32)
        
        if img.shape[2] == 4:
            rgb = img[..., :3]
            alpha = img[..., 3:] / 255.0
            composited = rgb * alpha + self.bg_color * (1.0 - alpha)
            return np.clip(np.round(composited), 0, 255).astype(np.uint8)
        elif img.shape[2] == 3:
            return np.clip(np.round(img), 0, 255).astype(np.uint8)
        else:
            raise ValueError(f"Unsupported number of channels: {img.shape[2]}")

    def calculate(self, img1: np.ndarray, img2: np.ndarray) -> Dict[str, Union[float, Dict]]:
        """
        Calculates histogram correlation and Bhattacharyya distance per channel,
        as well as an aggregate score across all channels.
        
        Args:
            img1: Source/Reference image.
            img2: Rasterized SVG output image.
            
        Returns:
            Dictionary with JSON-safe float values.
        """
        comp1 = self._composite_alpha_uint8(img1)
        comp2 = self._composite_alpha_uint8(img2)
        
        results = {
            "correlation_per_channel": {},
            "bhattacharyya_per_channel": {},
            "aggregate_correlation": 0.0,
            "aggregate_bhattacharyya": 0.0
        }
        
        channels = ['R', 'G', 'B']
        total_corr = 0.0
        total_bhat = 0.0
        
        for i, ch in enumerate(channels):
            # Calculate histograms for the current channel
            hist1 = cv2.calcHist([comp1], [i], None, [256], [0, 256])
            hist2 = cv2.calcHist([comp2], [i], None, [256], [0, 256])
            
            # Normalize to L1 norm
            cv2.normalize(hist1, hist1, alpha=1, norm_type=cv2.NORM_L1)
            cv2.normalize(hist2, hist2, alpha=1, norm_type=cv2.NORM_L1)
            
            # Compute metrics
            corr = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
            bhat = cv2.compareHist(hist1, hist2, cv2.HISTCMP_BHATTACHARYYA)
            
            # Sometimes OpenCV returns slightly above 1 or below -1 due to float precision
            corr = float(np.clip(corr, -1.0, 1.0))
            bhat = float(np.clip(bhat, 0.0, 1.0))
            
            results["correlation_per_channel"][ch] = corr
            results["bhattacharyya_per_channel"][ch] = bhat
            
            total_corr += corr
            total_bhat += bhat
            
        results["aggregate_correlation"] = float(total_corr / 3.0)
        results["aggregate_bhattacharyya"] = float(total_bhat / 3.0)
        
        return results
