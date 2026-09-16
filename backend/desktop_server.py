"""Packaged backend entrypoint for the desktop application."""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("JARVIS_FORGE_RUNTIME", "1")
if getattr(sys, "frozen", False):
    asset_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    os.environ.setdefault("JARVIS_ASSET_ROOT", str(asset_root))
    os.environ.setdefault("JARVIS_CONFIG_DIR", str(asset_root / "config"))
    os.environ.setdefault("JARVIS_DASHBOARD", str(asset_root / "dashboard" / "index.html"))

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=int(os.getenv("PORT", "8000")), log_level="info")
