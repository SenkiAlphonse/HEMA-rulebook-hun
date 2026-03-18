#!/usr/bin/env python
"""Backward-compatible wrapper for the build script.

The actual implementation lives in `tools/build.py`. Keeping this file
allows existing docs/CI/deploy configs that run `python build.py` to
continue working after the repo re-org.
"""

from __future__ import annotations

import runpy


if __name__ == "__main__":
    runpy.run_path("tools/build.py", run_name="__main__")
