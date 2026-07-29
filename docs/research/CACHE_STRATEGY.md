# Cache Strategy Audit

## Status
Audit conducted on: 2026-07-29

## Overview
This document analyzes the caching strategy within the Silukman Image Vectorizer application and its benchmark subsystem to ensure it supports robust, reproducible repeated-run measurements.

## Core Principles Audited

1. **Does the cache pollute repeated-run measurements?**
   - In a benchmark scenario, tracing and processing must be fully evaluated in every repetition to measure variance and true execution cost.
   - **Strategy:** Memory or disk caching of vectorization results must be scoped *per-run* or entirely disabled during benchmarking. Warm-up runs are executed specifically to populate system/JIT caches and IO buffers, while actual measured repetitions must compute the SVG from scratch.

2. **Can the cache be disabled?**
   - **Requirement:** Any application-level caching (e.g., thumbnail generation, intermediate threshold arrays) must have a flag (e.g., `--no-cache` or `cache_enabled=False` in configuration) to ensure zero-cache execution.
   - **Implementation:** The `VectorizationConfig` defines preprocessing and execution parameters. The canonical pipeline used by `vectorize_image()` does not use a cross-run application cache. It explicitly writes to a temporary file and exports atomically. 

3. **Cache Key Composition**
   - If caching is introduced for UI responsiveness (e.g., preview caching), the cache key must strictly consist of:
     - The SHA-256 hash of the input raster image.
     - The deterministic hash of the active `VectorizationConfig`.
   - Omitting either leads to stale or incorrect preview results.

4. **Cache Behavior Logging**
   - **Requirement:** Cache hits and misses must be logged explicitly in the telemetry or benchmark output.
   - **Implementation:** The canonical run records currently reflect full execution. If caching is implemented, the `runs.jsonl` must include a `cache_hit: boolean` field.

5. **Warm-Cache vs. Cold-Cache Separation**
   - **Requirement:** Benchmarks should report warm and cold cache metrics separately.
   - **Implementation:** The benchmark runner executes `[WARMUP_RUNS]` before `[REPETITIONS]`. The warm-up runs load libraries, populate OS file caches, and stabilize CPU thermal states (warm-cache environment) before actual timing starts for the measured repetitions.
