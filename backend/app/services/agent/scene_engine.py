from datetime import datetime, timezone
from enum import Enum


class Scene(str, Enum):
    match_day = "match_day"
    transfer_window = "transfer_window"
    daily = "daily"


# Approximate transfer windows
TRANSFER_WINDOWS = [
    (6, 1, 8, 31),   # Summer: Jun 1 - Aug 31
    (1, 1, 1, 31),    # Winter: Jan 1 - Jan 31
]


def detect_scene(team_match_schedules: list[dict] | None = None) -> Scene:
    """Detect current scene based on date and match schedules."""
    now = datetime.now(timezone.utc)

    # Check transfer window
    for start_m, start_d, end_m, end_d in TRANSFER_WINDOWS:
        start = datetime(now.year, start_m, start_d, tzinfo=timezone.utc)
        end = datetime(now.year, end_m, end_d, tzinfo=timezone.utc)
        if start <= now <= end:
            return Scene.transfer_window

    # Check match day (simplified: if within 3 hours of any match kickoff)
    if team_match_schedules:
        for match in team_match_schedules:
            kickoff = match.get("kickoff")
            if kickoff:
                kickoff_dt = datetime.fromisoformat(kickoff)
                delta = abs((now - kickoff_dt).total_seconds())
                if delta < 3 * 3600:  # within 3 hours
                    return Scene.match_day

    return Scene.daily


def is_transfer_window() -> bool:
    return detect_scene() == Scene.transfer_window
