#!/usr/bin/env python3

from glabng.glabng_class import GLABNG

try:
    glab = GLABNG(glab_fn="path/to/glab/file.out")
except ValueError as e:
    print(f"Validation failed: {e}")
