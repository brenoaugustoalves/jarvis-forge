"""Ponto de entrada recomendado para iniciar o Jarvis Forge."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

from app.bootstrap import ensure_managed_runtime, managed_python


def main() -> None:
    ensure_managed_runtime()
    environment = os.environ.copy()
    environment["JARVIS_FORGE_RUNTIME"] = "1"
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parent)
    subprocess.check_call([
        str(managed_python()), "-m", "uvicorn", "app.main:app",
        "--host", "127.0.0.1", "--port", "8000", "--reload",
    ], cwd=Path(__file__).resolve().parent, env=environment)


if __name__ == "__main__":
    main()
