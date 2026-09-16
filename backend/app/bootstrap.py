"""Inicializador autorreparável do ambiente local do Jarvis Forge.

Ele só instala dependências declaradas no próprio projeto e nunca executa
correções arbitrárias fora do diretório da aplicação.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import subprocess
import sys


BACKEND_DIR = Path(__file__).resolve().parents[1]
REQUIREMENTS = BACKEND_DIR / "requirements.txt"
VENV_DIR = BACKEND_DIR / ".venv"
MARKER = VENV_DIR / ".jarvis-forge-requirements.sha256"


def managed_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def _requirements_hash() -> str:
    return hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest()


def _create_venv(python: Path) -> None:
    if python.exists():
        return
    print("[Jarvis Forge] Ambiente virtual não encontrado. Criando .venv...")
    subprocess.check_call([sys.executable, "-m", "venv", str(VENV_DIR)])


def _install_dependencies(python: Path) -> None:
    expected = _requirements_hash()
    if MARKER.exists() and MARKER.read_text(encoding="utf-8").strip() == expected:
        return

    print("[Jarvis Forge] Dependências ausentes ou desatualizadas. Reparando...")
    try:
        subprocess.check_call([
            str(python), "-m", "pip", "install", "--upgrade", "-r", str(REQUIREMENTS)
        ])
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            "Não foi possível instalar as dependências. "
            "Verifique a internet e tente novamente."
        ) from error

    MARKER.write_text(expected, encoding="utf-8")


def ensure_managed_runtime() -> None:
    """Prepara o ambiente e relança o processo no Python gerenciado."""
    if os.environ.get("JARVIS_FORGE_RUNTIME") == "1":
        return

    python = managed_python()
    _create_venv(python)
    _install_dependencies(python)

    current = Path(sys.executable).resolve()
    if current != python.resolve():
        environment = os.environ.copy()
        environment["JARVIS_FORGE_RUNTIME"] = "1"
        environment["PYTHONPATH"] = str(BACKEND_DIR)
        command = [str(python), str(Path(__file__).resolve().parents[0] / "main.py"), *sys.argv[1:]]
        completed = subprocess.run(command, cwd=BACKEND_DIR, env=environment)
        raise SystemExit(completed.returncode)
