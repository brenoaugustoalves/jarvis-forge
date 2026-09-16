"""Safe local code repair pipeline: isolated worktree, Codex patch, tests, report."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class RepairEngine:
    def __init__(self, workspace: Path):
        self.workspace = workspace.resolve()
        if not (self.workspace / ".git").exists():
            raise ValueError("O workspace precisa ser um repositório Git")

    def repair(self, error: str, test_command: list[str] | None = None) -> dict:
        repair_id = str(uuid4())
        branch = f"autorepair/{repair_id[:8]}"
        worktree = Path(tempfile.mkdtemp(prefix="jarvis-autorepair-"))
        try:
            self._git(["worktree", "add", "-b", branch, str(worktree), "HEAD"])
            prompt = f"""Analise este erro do projeto e proponha uma correção mínima e segura.
Erro:
{error}

Regras obrigatórias: altere somente arquivos deste projeto, não use credenciais,
não faça deploy, não remova dados, preserve APIs públicas quando possível e
adicione/ajuste testes. Depois deixe o patch aplicado no workspace para revisão."""
            codex = subprocess.run(["codex", "exec", "--ephemeral", "--sandbox", "workspace-write", "--color", "never", "-C", str(worktree), prompt], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
            report = {"id": repair_id, "branch": branch, "status": "proposed", "error": error, "created_at": datetime.now(timezone.utc).isoformat(), "codex_output": codex.stdout[-12000:]}
            if codex.returncode:
                report["status"] = "failed"
                report["failure"] = codex.stderr[-4000:]
                return report
            diff = subprocess.run(["git", "diff", "--check"], cwd=worktree, capture_output=True, text=True)
            report["diff_check"] = diff.stdout or "ok"
            command = test_command or ["python", "-m", "pytest", "-q"]
            tests = subprocess.run(command, cwd=worktree, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900)
            report["tests"] = {"command": command, "returncode": tests.returncode, "output": (tests.stdout + tests.stderr)[-12000:]}
            report["status"] = "validated" if tests.returncode == 0 and diff.returncode == 0 else "needs_review"
            report["diff"] = subprocess.run(["git", "diff", "--stat"], cwd=worktree, capture_output=True, text=True).stdout
            patch_path = self.workspace / f"jarvis-repair-{repair_id[:8]}.patch"
            patch = subprocess.run(["git", "diff", "--binary"], cwd=worktree, capture_output=True, text=True)
            patch_path.write_text(patch.stdout, encoding="utf-8")
            report["patch_file"] = str(patch_path)
            return report
        finally:
            subprocess.run(["git", "worktree", "remove", "--force", str(worktree)], cwd=self.workspace, capture_output=True)
            shutil.rmtree(worktree, ignore_errors=True)

    def _git(self, args: list[str]):
        result = subprocess.run(["git", *args], cwd=self.workspace, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stderr.strip() or "Falha no Git")
