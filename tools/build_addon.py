"""Workspace entry point for the verified Bingus Shared Loader packager."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / 'vendor' / 'BingusSharedLoader' / 'scripts'
sys.path.insert(0, str(UPSTREAM))
runpy.run_path(str(UPSTREAM / 'build_addon.py'), run_name='__main__')
