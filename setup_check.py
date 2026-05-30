#!/usr/bin/env python
"""Backward-compatible wrapper for the setup verification script.

The actual implementation lives in `tools/setup_check.py`.
"""

from __future__ import annotations

import runpy  # noqa: I001


if __name__ == "__main__":
    runpy.run_path("tools/setup_check.py", run_name="__main__")
