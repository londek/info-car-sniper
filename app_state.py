from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from infocar import InfoCarSession
    from config_manager import AppConfig


@dataclass
class Stats:
    all_checks: int = 0
    earliest_ever_time: Optional[datetime] = None
    current_earliest_time: Optional[datetime] = None
    last_found_time: Optional[datetime] = None


@dataclass
class AppState:
    """Global app state to persist across screens."""
    # Avoid runtime import cycle by using forward reference string for type hints
    session: Optional["InfoCarSession"] = None
    stats: Stats = field(default_factory=Stats)
    # Optional convenience holders
    reservation: Optional[dict[str, Any]] = None
    cfg: Optional["AppConfig"] = None
    started_checking_at: Optional[datetime] = None
