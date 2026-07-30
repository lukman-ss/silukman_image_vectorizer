import math
from typing import Dict, Union

import numpy as np


class PixelMetricsCalculator:
    """
    Calculates pixel-level difference metrics between two images.

    IMPORTANT DISCLAIMER:
    Pixel-level metrics such as MAE, MSE, RMSE, and PSNR measure absolute mathematical
    differences. They do NOT perfectly correlate with human visual perception.
    A single metric (or even this entire suite) is never sufficient to fully judge
    the visual quality of a vectorization. They should be used alongside structural
    metrics (like SSIM) and subjective evaluation.

    Interpretation:
    - MAE (Mean Absolute Error): Average absolute pixel difference (0 to 255).
    - MSE (Mean Squared Error): Average squared difference, penalizes large errors.
    - RMSE (Root Mean Squared Error): Square root of MSE, in the same unit as pixels (0 to 255).
    - PSNR (Peak Signal-to-Noise Ratio): Ratio of maximum possible power to noise power (in dB).
      Higher is better. Identical images approach infinity (capped at 100 in this implementation).
    - Normalized Error: MAE divided by 255, represented as a fraction (0.0 to 1.0).
    """

    def __init__(self, bg_color: tuple = (255, 255, 255)):
        """
        Args:
            bg_color: RGB tuple to use for alpha compositing. Default is white.
        """
        self.bg_color = np.array(bg_color, dtype=np.float32)

    def _composite_alpha(self, img: np.ndarray) -> np.ndarray:
        """
        Composites an RGBA or RGB image onto a solid background color.
        Always returns a float32 RGB array.
        """
        if img.ndim == 2:
            # Grayscale to RGB
            img = np.stack([img] * 3, axis=-1)

        img = img.astype(np.float32)

        if img.shape[2] == 4:
            # Has alpha channel
            rgb = img[..., :3]
            alpha = img[..., 3:] / 255.0
            composited = rgb * alpha + self.bg_color * (1.0 - alpha)
            return composited  # type: ignore[no-any-return] # complex typing/external library
        elif img.shape[2] == 3:
            return img
        else:
            raise ValueError(f"Unsupported number of channels: {img.shape[2]}")

    def calculate(self, img1: np.ndarray, img2: np.ndarray) -> Dict[str, Union[float, str]]:
        """
        Calculates MAE, MSE, RMSE, PSNR, and normalized error.
        Both images must be numpy arrays of the same width and height.

        Args:
            img1: Source/Reference image.
            img2: Rasterized SVG output image.

        Returns:
            Dictionary with JSON-safe float values.
        """
        if img1.shape[:2] != img2.shape[:2]:
            raise ValueError(f"Image dimensions do not match: {img1.shape[:2]} vs {img2.shape[:2]}")

        # Standardize arrays to RGB float32 by compositing alpha
        comp1 = self._composite_alpha(img1)
        comp2 = self._composite_alpha(img2)

        # Calculate differences
        diff = comp1 - comp2

        # MAE
        mae = float(np.mean(np.abs(diff)))

        # MSE
        mse = float(np.mean(diff**2))

        # RMSE
        rmse = float(math.sqrt(mse))

        # PSNR (cap at 100 for perfectly identical images to avoid division by zero)
        if mse == 0:
            psnr = 100.0
        else:
            psnr = float(20 * math.log10(255.0 / rmse))

        # Normalized Error
        normalized_mae = float(mae / 255.0)

        return {
            "mae": mae,
            "mse": mse,
            "rmse": rmse,
            "psnr": psnr,
            "normalized_mae": normalized_mae,
        }
