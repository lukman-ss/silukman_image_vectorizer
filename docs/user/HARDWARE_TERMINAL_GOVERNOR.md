# Hardware Terminal Governor

Last updated: 2026-06-05

This project does not include a hardware terminal governor. The document exists
to make the user documentation structure explicit and to clarify that Image
Vectorizer is a local desktop GUI app.

## Current Controls

- Vectorization runs in worker threads.
- Batch processing reports progress through the UI.
- There is no GPU, hardware throttle, or terminal daemon.

## Practical Limits

- Very large photos can create high CPU load.
- Dense spline SVG output increases processing time.
- Users should prefer flat 2D inputs for clean and fast vectorization.
