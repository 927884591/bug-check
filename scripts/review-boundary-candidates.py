#!/usr/bin/env python3
"""Run the installable skill's manual-boundary candidate reviewer from the repo root."""

from __future__ import annotations

import runpy
from pathlib import Path


REVIEWER = Path(__file__).resolve().parents[1] / "skills" / "bug-check" / "scripts" / "review-boundary-candidates.py"

runpy.run_path(str(REVIEWER), run_name="__main__")
