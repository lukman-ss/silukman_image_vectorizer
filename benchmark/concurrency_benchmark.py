#!/usr/bin/env python3
"""
Concurrency benchmark for parallel batch processing.
Measures throughput, memory usage, failure rates, and determinism across
different worker counts without defaulting to exhausting all available cores.
"""

import time
import argparse
import psutil
import hashlib
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed
from pathlib import Path
from app.core.vectorization_service import vectorize_image
from app.config.settings import VectorizationConfig


def create_dummy_images(num_images, tmp_dir):
    import cv2
    import numpy as np
    paths = []
    tmp_dir = Path(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    for i in range(num_images):
        p = tmp_dir / f"dummy_{i}.png"
        img = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
        cv2.imwrite(str(p), img)
        paths.append(str(p))
    return paths


def hash_file(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def run_benchmark(worker_count, input_paths, output_dir, use_processes=False):
    config = VectorizationConfig(engine="opencv_legacy")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    start_time = time.time()
    process = psutil.Process()
    start_memory = process.memory_info().rss

    ExecutorClass = ProcessPoolExecutor if use_processes else ThreadPoolExecutor

    futures = []
    results = []

    # Do not automatically use all cores. Explicitly use worker_count.
    with ExecutorClass(max_workers=worker_count) as executor:
        for p in input_paths:
            out_p = output_dir / (Path(p).stem + ".svg")
            futures.append(executor.submit(vectorize_image, p, str(out_p), config))

        for f in as_completed(futures):
            try:
                res = f.result()
                results.append(res)
            except Exception as e:
                results.append({"status": "failed", "error": str(e)})

    duration = time.time() - start_time
    end_memory = process.memory_info().rss
    mem_diff_mb = (end_memory - start_memory) / (1024 * 1024)

    success_count = sum(1 for r in results if getattr(r, "status", None) == "success")
    failure_count = len(results) - success_count
    throughput = len(input_paths) / duration if duration > 0 else 0

    # Measure determinism (hash of outputs)
    hashes = [hash_file(output_dir / (Path(p).stem + ".svg")) for p in input_paths if (output_dir / (Path(p).stem + ".svg")).exists()]

    return {
        "workers": worker_count,
        "duration_s": duration,
        "throughput_img_per_s": throughput,
        "memory_growth_mb": mem_diff_mb,
        "success": success_count,
        "failure": failure_count,
        "output_hashes": hashes
    }


def main():
    parser = argparse.ArgumentParser(description="Audit parallel batch processing.")
    parser.add_argument("--images", type=int, default=20, help="Number of dummy images to process")
    parser.add_argument("--process-pool", action="store_true", help="Use multiprocessing instead of threads")
    args = parser.parse_args()

    tmp_in = Path("tmp_bench_in")
    tmp_out = Path("tmp_bench_out")

    print(f"Creating {args.images} dummy images for benchmark...")
    input_paths = create_dummy_images(args.images, tmp_in)

    # Reasonable CPU counts to test
    worker_counts = [1, 2, 4]

    results = {}

    for wc in worker_counts:
        print(f"\nRunning benchmark with {wc} workers...")
        res = run_benchmark(wc, input_paths, tmp_out / f"run_{wc}", use_processes=args.process_pool)
        results[wc] = res
        print(f"Throughput: {res['throughput_img_per_s']:.2f} img/s")
        print(f"Memory Growth: {res['memory_growth_mb']:.2f} MB")
        print(f"Success/Fail: {res['success']}/{res['failure']}")

    print("\nDeterminism Check:")
    base_hashes = results[1]['output_hashes']
    for wc in [2, 4]:
        match = (results[wc]['output_hashes'] == base_hashes)
        print(f"Output hashes match between 1 worker and {wc} workers: {match}")

    # Cleanup logic can be added here if needed


if __name__ == "__main__":
    main()
