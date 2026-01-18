"""
History tracking for undo functionality.

Maintains a history of changes that can be undone.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from .config import BASE_DIR

HISTORY_FILE = BASE_DIR / ".study_history.json"
MAX_HISTORY = 50


def _load_history() -> List[Dict[str, Any]]:
    """Load history from file."""
    if not HISTORY_FILE.exists():
        return []

    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_history(history: List[Dict[str, Any]]) -> None:
    """Save history to file."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history[-MAX_HISTORY:], f, indent=2)
    except OSError:
        pass  # Best effort


def record_change(
    action: str,
    course_code: str,
    assessment_key: str,
    field: str,
    old_value: Any,
    new_value: Any,
    description: Optional[str] = None,
) -> None:
    """
    Record a change for potential undo.

    Args:
        action: Type of action (e.g., 'update_status', 'record_score', 'log_hours')
        course_code: The course code
        assessment_key: The assessment key
        field: The field that was changed
        old_value: Previous value
        new_value: New value
        description: Human-readable description of the change
    """
    history = _load_history()

    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "course_code": course_code,
        "assessment_key": assessment_key,
        "field": field,
        "old_value": old_value,
        "new_value": new_value,
        "description": description or f"{field}: {old_value} → {new_value}",
    }

    history.append(entry)
    _save_history(history)


def record_hours_change(
    week_num: str,
    old_hours: float,
    new_hours: float,
    added_hours: float,
    course_code: Optional[str] = None,
) -> None:
    """Record a hours logging change."""
    history = _load_history()

    entry = {
        "timestamp": datetime.now().isoformat(),
        "action": "log_hours",
        "week_num": week_num,
        "old_hours": old_hours,
        "new_hours": new_hours,
        "added_hours": added_hours,
        "course_code": course_code,
        "description": f"Logged {added_hours}h (total: {new_hours}h)",
    }

    history.append(entry)
    _save_history(history)


def get_last_change() -> Optional[Dict[str, Any]]:
    """Get the most recent change."""
    history = _load_history()
    return history[-1] if history else None


def get_recent_changes(count: int = 5) -> List[Dict[str, Any]]:
    """Get recent changes."""
    history = _load_history()
    return list(reversed(history[-count:]))


def pop_last_change() -> Optional[Dict[str, Any]]:
    """Remove and return the most recent change."""
    history = _load_history()
    if not history:
        return None

    entry = history.pop()
    _save_history(history)
    return entry


def clear_history() -> int:
    """Clear all history. Returns number of entries cleared."""
    history = _load_history()
    count = len(history)
    _save_history([])
    return count


def format_change_description(entry: Dict[str, Any]) -> str:
    """Format a history entry for display."""
    from .config import CODE_TO_ALIAS, COURSE_NAMES

    timestamp = datetime.fromisoformat(entry["timestamp"])
    time_str = timestamp.strftime("%H:%M")
    date_str = timestamp.strftime("%d %b")

    action = entry.get("action", "unknown")

    if action == "log_hours":
        hours = entry.get("added_hours", 0)
        course = entry.get("course_code")
        if course:
            alias = CODE_TO_ALIAS.get(course, "??")
            return f"{date_str} {time_str}: Logged {hours}h for [{alias}]"
        return f"{date_str} {time_str}: Logged {hours}h"

    course_code = entry.get("course_code", "")
    assessment_key = entry.get("assessment_key", "")
    alias = CODE_TO_ALIAS.get(course_code, "??")

    if action == "update_status":
        old_val = entry.get("old_value", "?")
        new_val = entry.get("new_value", "?")
        return (
            f"{date_str} {time_str}: [{alias}] {assessment_key}: {old_val} → {new_val}"
        )

    if action == "record_score":
        score = entry.get("new_value", "?")
        return f"{date_str} {time_str}: [{alias}] {assessment_key}: scored {score}"

    return f"{date_str} {time_str}: {entry.get('description', 'Unknown change')}"
