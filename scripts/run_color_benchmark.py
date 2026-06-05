import os
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from app.config.settings import VectorizationSettings
from app.core.vectorizer_backend import VTracerVectorizerBackend

def run_benchmark():
    input_dir = project_root / "samples" / "color_benchmark"
    output_dir = project_root / "samples" / "color_benchmark_result"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    supported_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    image_files = sorted([
        p for p in input_dir.iterdir()
        if p.is_file() and p.suffix.lower() in supported_extensions
    ])
    
    if not image_files:
        print(f"No image files found in {input_dir}")
        return
        
    print(f"Found {len(image_files)} images to process.")
    
    backend = VTracerVectorizerBackend()
    settings = VectorizationSettings(engine_type="VTracer")
    
    for img_path in image_files:
        output_name = f"{img_path.stem}_vectorized.svg"
        out_path = output_dir / output_name
        
        print(f"Processing: {img_path.name} -> {output_name}...", end="", flush=True)
        try:
            result = backend.vectorize(str(img_path), settings)
            if hasattr(result, "svg_data") and result.svg_data:
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(result.svg_data)
                print(" Success!")
            else:
                print(" Failed (No SVG data returned).")
        except Exception as e:
            print(f" Error: {str(e)}")

if __name__ == "__main__":
    run_benchmark()
