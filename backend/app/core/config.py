from pathlib import Path
import yaml


ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "config"


def load_yaml(filename: str) -> dict:
    with (CONFIG_DIR / filename).open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}
