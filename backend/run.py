"""Ponto de entrada recomendado para iniciar o Jarvis Forge."""

from __future__ import annotations

import os
from pathlib import Path
import socket
import subprocess
import sys

from app.bootstrap import ensure_managed_runtime, managed_python


def main() -> None:
    ensure_managed_runtime()
    port = _available_port(int(os.getenv("JARVIS_PORT", "8000")))
    print(f"[Jarvis Forge] API iniciando em http://127.0.0.1:{port}", flush=True)
    environment = os.environ.copy()
    environment["JARVIS_FORGE_RUNTIME"] = "1"
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parent)
    environment["PORT"] = str(port)
    subprocess.check_call([
        str(managed_python()), "-m", "uvicorn", "app.main:app",
        "--host", "127.0.0.1", "--port", str(port), "--reload",
    ], cwd=Path(__file__).resolve().parent, env=environment)


def _available_port(start: int, attempts: int = 20) -> int:
    """Find a free local TCP port so a second launch self-heals port conflicts."""
    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"Nenhuma porta livre encontrada entre {start} e {start + attempts - 1}")


if __name__ == "__main__":
    main()
