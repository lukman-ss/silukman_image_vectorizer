import argparse
import hashlib
import json
import math
import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


def get_sha256(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


class SyntheticGenerator:
    def __init__(self, output_dir: str, seed: int = 42):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.seed = seed
        self.metadata = []
        random.seed(self.seed)

    def _save(self, img: Image.Image, name: str, params: dict):
        filepath = self.output_dir / f"{name}.png"
        img.save(filepath, "PNG")
        
        sha256 = get_sha256(str(filepath))
        
        meta = {
            "image_id": f"synth_{name}",
            "filename": f"{name}.png",
            "generator_params": params,
            "ground_truth": {
                "width": img.width,
                "height": img.height,
                "mode": img.mode,
                "type": name
            },
            "sha256": sha256
        }
        self.metadata.append(meta)
        print(f"Generated {name}.png (SHA256: {sha256[:8]}...)")

    def gen_geometric_shapes(self):
        img = Image.new("RGBA", (256, 256), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([20, 20, 100, 100], fill=(255, 0, 0, 255), outline=(0, 0, 0, 255), width=2)
        draw.ellipse([120, 20, 220, 120], fill=(0, 255, 0, 255))
        draw.polygon([(60, 140), (20, 220), (100, 220)], fill=(0, 0, 255, 255))
        self._save(img, "geometric_shapes", {"shapes": ["rectangle", "ellipse", "triangle"]})

    def gen_flat_logo(self):
        img = Image.new("RGBA", (256, 256), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.ellipse([50, 50, 206, 206], fill=(41, 128, 185, 255))
        draw.polygon([(100, 80), (100, 176), (170, 128)], fill=(236, 240, 241, 255))
        self._save(img, "flat_logo", {"style": "minimalist play button"})

    def gen_gradients(self):
        img = Image.new("RGBA", (256, 256), (0, 0, 0, 255))
        # Linear gradient
        for y in range(256):
            r = int((y / 255) * 255)
            for x in range(256):
                img.putpixel((x, y), (r, 50, 255 - r, 255))
        self._save(img, "gradients", {"type": "linear", "direction": "vertical"})

    def gen_thin_lines(self):
        img = Image.new("RGBA", (256, 256), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        for i in range(10, 250, 20):
            width = 1 if i < 128 else 2
            draw.line([(i, 10), (i, 246)], fill=(0, 0, 0, 255), width=width)
            draw.line([(10, i), (246, i)], fill=(0, 0, 0, 255), width=width)
        self._save(img, "thin_lines", {"spacing": 20, "widths": [1, 2]})

    def gen_curves(self):
        img = Image.new("RGBA", (256, 256), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        # Draw sine wave
        points = []
        for x in range(0, 256, 2):
            y = int(128 + 80 * math.sin(x / 20.0))
            points.append((x, y))
        draw.line(points, fill=(231, 76, 60, 255), width=4, joint="curve")
        draw.arc([20, 20, 236, 236], 45, 270, fill=(46, 204, 113, 255), width=5)
        self._save(img, "curves", {"types": ["sine_wave", "arc"]})

    def gen_pseudo_text(self):
        img = Image.new("RGBA", (256, 256), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        y = 20
        while y < 230:
            x = 20
            while x < 200:
                word_len = random.randint(10, 40)
                if x + word_len > 236:
                    break
                draw.rectangle([x, y, x + word_len, y + 8], fill=(50, 50, 50, 255))
                x += word_len + 10
            y += 18
        self._save(img, "pseudo_text", {"line_height": 18, "word_height": 8})

    def gen_transparent(self):
        img = Image.new("RGBA", (256, 256), (255, 255, 255, 0))
        # Draw on separate images and alpha composite
        layer1 = Image.new("RGBA", (256, 256), (0,0,0,0))
        ImageDraw.Draw(layer1).ellipse([40, 40, 160, 160], fill=(255, 0, 0, 128))
        
        layer2 = Image.new("RGBA", (256, 256), (0,0,0,0))
        ImageDraw.Draw(layer2).ellipse([96, 40, 216, 160], fill=(0, 255, 0, 128))
        
        layer3 = Image.new("RGBA", (256, 256), (0,0,0,0))
        ImageDraw.Draw(layer3).ellipse([68, 96, 188, 216], fill=(0, 0, 255, 128))
        
        img = Image.alpha_composite(img, layer1)
        img = Image.alpha_composite(img, layer2)
        img = Image.alpha_composite(img, layer3)
        self._save(img, "transparent_shapes", {"shapes": ["overlapping_circles"], "alpha": 128})

    def gen_noisy_edges(self):
        img = Image.new("RGBA", (256, 256), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        # Base shape
        draw.ellipse([64, 64, 192, 192], fill=(0, 0, 0, 255))
        # Add noise to edges
        for angle in range(0, 360):
            rad = math.radians(angle)
            r = 64 + random.randint(-5, 5)
            x = 128 + int(r * math.cos(rad))
            y = 128 + int(r * math.sin(rad))
            draw.point((x, y), fill=(0, 0, 0, 255))
            draw.point((x+1, y), fill=(0, 0, 0, 255))
        self._save(img, "noisy_edges", {"noise_level": 5})

    def gen_overlapping(self):
        img = Image.new("RGBA", (256, 256), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 150, 150], fill=(241, 196, 15, 255))
        draw.ellipse([100, 100, 200, 200], fill=(155, 89, 182, 255))
        draw.polygon([(75, 220), (150, 75), (225, 220)], fill=(52, 73, 94, 200))
        self._save(img, "overlapping_objects", {"count": 3})

    def gen_monochrome(self):
        img = Image.new("1", (256, 256), 1)  # 1-bit mode, 1=white
        draw = ImageDraw.Draw(img)
        draw.ellipse([30, 30, 226, 226], fill=0) # 0=black
        draw.rectangle([80, 80, 176, 176], fill=1)
        draw.polygon([(128, 50), (100, 100), (156, 100)], fill=1)
        self._save(img, "monochrome_silhouette", {"mode": "1-bit"})

    def generate_all(self):
        self.gen_geometric_shapes()
        self.gen_flat_logo()
        self.gen_gradients()
        self.gen_thin_lines()
        self.gen_curves()
        self.gen_pseudo_text()
        self.gen_transparent()
        self.gen_noisy_edges()
        self.gen_overlapping()
        self.gen_monochrome()
        
        # Save manifest
        manifest_path = self.output_dir / "synthetic_manifest.json"
        with open(manifest_path, "w") as f:
            json.dump({
                "seed": self.seed,
                "purpose": "regression_testing",
                "images": self.metadata
            }, f, indent=2)
        print(f"Saved manifest to {manifest_path}")

def main():
    parser = argparse.ArgumentParser(description="Synthetic Dataset Generator")
    parser.add_argument("--output", default="benchmark/synthetic", help="Output directory")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    args = parser.parse_args()
    
    generator = SyntheticGenerator(args.output, args.seed)
    generator.generate_all()
    print("Done generating synthetic dataset.")

if __name__ == "__main__":
    main()
