import cv2
import numpy as np
from typing import Dict, Union


class EdgeMetricsCalculator:
    """
    Calculates edge similarity metrics between two images.
    
    Disclaimer:
    This metric is only a PROXY for contour preservation. Edge detection algorithms 
    (like Canny) are sensitive to local contrast and noise. A low edge F1 score 
    does not necessarily mean the vector shapes are wrong; it might just mean the 
    rasterization aliasing or sub-pixel rendering shifted the hard edges slightly.
    
    Pipeline:
    1. Composite over background and convert to Grayscale.
    2. Extract edges using Canny edge detector with fixed thresholds.
    3. Calculate Pixel-level Precision, Recall, and F1 score on the binary edge maps.
    4. (Optional) Compute average Distance Transform error: how far off is each 
       detected edge pixel from the nearest true edge pixel.
    """
    
    def __init__(
        self, 
        bg_color: tuple = (255, 255, 255),
        canny_thresh1: int = 100,
        canny_thresh2: int = 200,
        compute_distance_transform: bool = True
    ):
        self.bg_color = np.array(bg_color, dtype=np.float32)
        self.params = {
            "canny_thresh1": canny_thresh1,
            "canny_thresh2": canny_thresh2,
            "compute_distance_transform": compute_distance_transform
        }

    def _composite_to_gray(self, img: np.ndarray) -> np.ndarray:
        """Composites image and returns an 8-bit grayscale array."""
        if img.ndim == 2:
            return img.astype(np.uint8)
            
        img_f = img.astype(np.float32)
        if img.shape[2] == 4:
            rgb = img_f[..., :3]
            alpha = img_f[..., 3:] / 255.0
            composited = rgb * alpha + self.bg_color * (1.0 - alpha)
        else:
            composited = img_f
            
        composited_uint8 = np.clip(np.round(composited), 0, 255).astype(np.uint8)
        gray = cv2.cvtColor(composited_uint8, cv2.COLOR_RGB2GRAY)
        return gray

    def calculate(self, img1: np.ndarray, img2: np.ndarray) -> Dict[str, Union[float, Dict]]:
        """
        Calculates Edge Precision, Recall, F1, and Distance Transform error.
        
        Args:
            img1: Reference image (Ground Truth edges).
            img2: Target image (Predicted edges).
        """
        if img1.shape[:2] != img2.shape[:2]:
            raise ValueError(f"Dimensions mismatch: {img1.shape[:2]} vs {img2.shape[:2]}")
            
        gray1 = self._composite_to_gray(img1)
        gray2 = self._composite_to_gray(img2)
        
        edges1 = cv2.Canny(gray1, self.params["canny_thresh1"], self.params["canny_thresh2"])
        edges2 = cv2.Canny(gray2, self.params["canny_thresh1"], self.params["canny_thresh2"])
        
        # Convert to boolean arrays
        e1_bool = edges1 > 0
        e2_bool = edges2 > 0
        
        true_positives = np.sum(e1_bool & e2_bool)
        false_positives = np.sum((~e1_bool) & e2_bool)
        false_negatives = np.sum(e1_bool & (~e2_bool))
        
        # Precision, Recall, F1
        precision = 1.0
        if (true_positives + false_positives) > 0:
            precision = float(true_positives / (true_positives + false_positives))
            
        recall = 1.0
        if (true_positives + false_negatives) > 0:
            recall = float(true_positives / (true_positives + false_negatives))
            
        f1 = 0.0
        if (precision + recall) > 0:
            f1 = float(2 * (precision * recall) / (precision + recall))
            
        result = {
            "parameters": self.params,
            "precision": precision,
            "recall": recall,
            "f1": f1
        }
        
        # Distance Transform Metric
        # How far is each predicted edge pixel from the nearest true edge pixel?
        if self.params["compute_distance_transform"]:
            if np.sum(e1_bool) == 0:
                # If there are no true edges, distance is defined as 0 if no pred edges, else penalty
                avg_dist = 0.0 if np.sum(e2_bool) == 0 else float(np.max(gray1.shape))
            else:
                # Invert edges1: 0 means edge, 255 means background
                inv_edges1 = 255 - edges1
                # Compute distance to nearest zero pixel
                dist_map = cv2.distanceTransform(inv_edges1, cv2.DIST_L2, 5)
                # Average distance only at locations where img2 has edges
                if np.sum(e2_bool) > 0:
                    avg_dist = float(np.mean(dist_map[e2_bool]))
                else:
                    avg_dist = 0.0
            
            result["mean_distance_error"] = avg_dist
            
        return result
