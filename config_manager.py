import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path("config.json")

@dataclass
class AppConfig:
    username: str = ""
    password: str = ""
    capmonster_key: str = ""
    date_from: str = ""  # YYYY-MM-DD
    date_to: str = ""    # YYYY-MM-DD
    hour_from: str = ""  # HH:MM
    hour_to: str = ""    # HH:MM

def load_config(path: Optional[Path] = None) -> AppConfig:
    p = path or CONFIG_PATH
    if not p.exists():
        return AppConfig()
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return AppConfig(
            username=data.get("username", ""),
            password=data.get("password", ""),
            capmonster_key=data.get("capmonster_key", ""),
            date_from=data.get("date_from", ""),
            date_to=data.get("date_to", ""),
            hour_from=data.get("hour_from", ""),
            hour_to=data.get("hour_to", ""),
        )
    except Exception:
        return AppConfig()

def save_config(cfg: AppConfig, path: Optional[Path] = None) -> None:
    p = path or CONFIG_PATH
    p.write_text(json.dumps(asdict(cfg), indent=2, ensure_ascii=False), encoding="utf-8")
