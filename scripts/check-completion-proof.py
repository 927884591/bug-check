#!/usr/bin/env python3
"""Run the installable skill's completion-proof checker from the repo root."""

from __future__ import annotations

import runpy
from pathlib import Path


CHECKER = Path(__file__).resolve().parents[1] / "skills" / "bug-check" / "scripts" / "check-completion-proof.py"

runpy.run_path(str(CHECKER), run_name="__main__")
