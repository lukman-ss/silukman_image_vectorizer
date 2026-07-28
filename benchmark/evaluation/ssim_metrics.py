from typing import Dict, Union

import numpy as np

try:
    from skimage.metrics import structural_similarity as ssim

    HAS_SKIMAGE = True
except ImportError:
    HAS_SKIMAGE = False


class SSIMCalculator:
    """
    Calculates Structural Similarity Index (SSIM).

    Dependencies:
    - Requires `scikit-image` for a validated, academic-standard implementation.
      Custom/manual implementations are avoided as they are prone to subtle bugs.

    Color Handling:
    - Images are composited onto a solid background (default: white) to resolve
      transparency, ensuring an apples-to-apples comparison in the RGB domain.

    Data Range:
    - 0 to 255 (8-bit depth).

    Minimum Size:
    - SSIM uses a default window size of 7. Images smaller than 7x7 will raise
      an error or be skipped. We validate `min(width, height) >= 7`.
    """

    def __init__(self, bg_color: tuple = (255, 255, 255)):
        self.bg_color = np.array(bg_color, dtype=np.float32)

    def _composite_alpha_uint8(self, img: np.ndarray) -> np.ndarray:
        """
        Composites an RGBA or RGB image onto a solid background color.
        Returns a uint8 RGB array.
        """
        if img.ndim == 2:
            img = np.stack([img] * 3, axis=-1)

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

    def calculate(self, img1: np.ndarray, img2: np.ndarray) -> Dict[str, Union[float, str]]:
        """
        Calculates the SSIM score.

        Returns:
            Dictionary containing the 'ssim' float score or an error string.
        """
        if not HAS_SKIMAGE:
            return {"error": "scikit-image is not installed. SSIM cannot be calculated."}

        if img1.shape[:2] != img2.shape[:2]:
            return {"error": f"Image dimensions do not match: {img1.shape[:2]} vs {img2.shape[:2]}"}

        min_dim = min(img1.shape[0], img1.shape[1])
        if min_dim < 7:
            # win_size defaults to 7, cannot compute SSIM on smaller images
            return {"error": f"Image too small for SSIM (min dimension is {min_dim}, needs 7)."}

        comp1 = self._composite_alpha_uint8(img1)
        comp2 = self._composite_alpha_uint8(img2)

        try:
            # scikit-image SSIM:
            # channel_axis=-1 specifies that the last axis contains channels (RGB).
            # data_range=255 because our images are uint8 [0, 255].
            score = ssim(comp1, comp2, channel_axis=-1, data_range=255)

            # Bound the score theoretically just in case of float precision issues
            score = float(np.clip(score, -1.0, 1.0))
            return {"ssim": score}

        except Exception as e:
            return {"error": f"SSIM calculation failed: {str(e)}"}
