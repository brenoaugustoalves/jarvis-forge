"""CLI for safe local autorepair."""
import argparse
import json
from pathlib import Path

from app.core.repair_engine import RepairEngine

parser = argparse.ArgumentParser(description="Analisa e valida uma correção em branch temporária")
parser.add_argument("error", help="Erro, traceback ou falha observada")
parser.add_argument("--workspace", type=Path, default=Path.cwd())
parser.add_argument("--output", type=Path, default=Path("jarvis-repair-report.json"))
args = parser.parse_args()
report = RepairEngine(args.workspace).repair(args.error)
args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"id": report["id"], "status": report["status"], "report": str(args.output.resolve())}, ensure_ascii=False))
