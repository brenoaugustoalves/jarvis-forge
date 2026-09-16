"""Persistence boundary for projects, workflow versions, runs and audit events."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PersistentStore:
    """Small repository backed by SQLite locally and PostgreSQL in production.

    SQLite is intentionally the zero-config fallback so the API remains useful
    before Docker is started. PostgreSQL is selected with DATABASE_URL.
    """

    def __init__(self, url: str | None = None):
        self.url = url or os.getenv("DATABASE_URL", "sqlite:///./jarvis-forge.db")
        self.is_postgres = self.url.startswith("postgres")
        if self.is_postgres:
            import psycopg
            self._psycopg = psycopg
            self.path = None
            self._init_postgres()
            return
        self.path = Path(self.url.removeprefix("sqlite:///"))
        if not self.path.is_absolute():
            self.path = Path.cwd() / self.path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_sqlite()

    def _connect(self):
        if self.is_postgres:
            return self._psycopg.connect(self.url)
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_sqlite(self):
        with self._connect() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS workflows (id TEXT PRIMARY KEY, version INTEGER NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, status TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS artifacts (id TEXT PRIMARY KEY, run_id TEXT NOT NULL, data TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, resource_type TEXT NOT NULL, resource_id TEXT, metadata TEXT NOT NULL, created_at TEXT NOT NULL);
            """)

    def _init_postgres(self):
        with self._connect() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, data JSONB NOT NULL);
            CREATE TABLE IF NOT EXISTS workflows (id TEXT NOT NULL, version INTEGER NOT NULL, data JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL, PRIMARY KEY (id, version));
            CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, project_id TEXT NOT NULL, status TEXT NOT NULL, data JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL);
            CREATE TABLE IF NOT EXISTS artifacts (id TEXT PRIMARY KEY, run_id TEXT NOT NULL, data JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL);
            CREATE TABLE IF NOT EXISTS audit_logs (id BIGSERIAL PRIMARY KEY, action TEXT NOT NULL, resource_type TEXT NOT NULL, resource_id TEXT, metadata JSONB NOT NULL, created_at TIMESTAMPTZ NOT NULL);
            """)

    @staticmethod
    def _decode(row):
        return json.loads(row["data"]) if row else None

    def create_project(self, project: dict) -> dict:
        with self._connect() as conn:
            if self.is_postgres:
                conn.execute("INSERT INTO projects VALUES (%s, %s)", (project["id"], json.dumps(project)))
            else:
                conn.execute("INSERT INTO projects VALUES (?, ?)", (project["id"], json.dumps(project)))
        self.audit("project.created", "project", project["id"])
        return project

    def list_projects(self) -> list[dict]:
        with self._connect() as conn:
            query = "SELECT data FROM projects ORDER BY id DESC" if self.is_postgres else "SELECT data FROM projects ORDER BY rowid DESC"
            return [row[0] if self.is_postgres else self._decode(row) for row in conn.execute(query)]

    def get_project(self, project_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT data FROM projects WHERE id=%s" if self.is_postgres else "SELECT data FROM projects WHERE id=?", (project_id,)).fetchone()
            return (row[0] if self.is_postgres else self._decode(row)) if row else None

    def save_workflow(self, workflow: dict) -> dict:
        with self._connect() as conn:
            previous_row = conn.execute("SELECT MAX(version) FROM workflows WHERE id=%s" if self.is_postgres else "SELECT MAX(version) AS version FROM workflows WHERE id=?", (workflow["id"],)).fetchone()
            previous = (previous_row[0] if self.is_postgres else previous_row["version"]) or 0
            workflow["version"] = previous + 1
            workflow["created_at"] = workflow.get("created_at", utc_now())
            conn.execute("INSERT INTO workflows VALUES (%s, %s, %s, %s)" if self.is_postgres else "INSERT INTO workflows VALUES (?, ?, ?, ?)", (workflow["id"], workflow["version"], json.dumps(workflow), workflow["created_at"]))
        self.audit("workflow.saved", "workflow", workflow["id"], {"version": workflow["version"]})
        return workflow

    def list_workflows(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT data FROM workflows w WHERE version=(SELECT MAX(version) FROM workflows x WHERE x.id=w.id) ORDER BY created_at DESC")
            return [row[0] if self.is_postgres else self._decode(row) for row in rows]

    def save_run(self, run: dict) -> dict:
        with self._connect() as conn:
            conn.execute("INSERT INTO runs VALUES (%s, %s, %s, %s, %s)" if self.is_postgres else "INSERT INTO runs VALUES (?, ?, ?, ?, ?)", (run["id"], run["project_id"], run["status"], json.dumps(run), run["created_at"]))
        self.audit("run.created", "run", run["id"], {"project_id": run["project_id"]})
        return run

    def get_run(self, run_id: str) -> dict | None:
        with self._connect() as conn:
            row = conn.execute("SELECT data FROM runs WHERE id=%s" if self.is_postgres else "SELECT data FROM runs WHERE id=?", (run_id,)).fetchone()
            return (row[0] if self.is_postgres else self._decode(row)) if row else None

    def update_run(self, run: dict) -> dict:
        with self._connect() as conn:
            query = "UPDATE runs SET status=%s, data=%s WHERE id=%s" if self.is_postgres else "UPDATE runs SET status=?, data=? WHERE id=?"
            conn.execute(query, (run["status"], json.dumps(run), run["id"]))
        self.audit("run.updated", "run", run["id"], {"status": run["status"]})
        return run

    def list_runs(self, project_id: str | None = None) -> list[dict]:
        with self._connect() as conn:
            query = "SELECT data FROM runs ORDER BY created_at DESC"
            args: tuple[Any, ...] = ()
            if project_id:
                query = "SELECT data FROM runs WHERE project_id=%s ORDER BY created_at DESC" if self.is_postgres else "SELECT data FROM runs WHERE project_id=? ORDER BY created_at DESC"
                args = (project_id,)
            return [row[0] if self.is_postgres else self._decode(row) for row in conn.execute(query, args)]

    def audit(self, action: str, resource_type: str, resource_id: str | None = None, metadata: dict | None = None):
        with self._connect() as conn:
            conn.execute("INSERT INTO audit_logs(action, resource_type, resource_id, metadata, created_at) VALUES (%s, %s, %s, %s, %s)" if self.is_postgres else "INSERT INTO audit_logs(action, resource_type, resource_id, metadata, created_at) VALUES (?, ?, ?, ?, ?)", (action, resource_type, resource_id, json.dumps(metadata or {}), utc_now()))

    def list_audit(self, limit: int = 100) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT %s" if self.is_postgres else "SELECT * FROM audit_logs ORDER BY id DESC LIMIT ?", (limit,))
            if self.is_postgres:
                return [{"id": r[0], "action": r[1], "resource_type": r[2], "resource_id": r[3], "metadata": r[4], "created_at": r[5]} for r in rows]
            return [dict(row) | {"metadata": json.loads(row["metadata"])} for row in rows]
