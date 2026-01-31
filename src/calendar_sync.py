"""
Data-driven calendar integration using AppleScript.

Provides robust calendar synchronization with:
- Retry logic for transient failures
- Graceful degradation when Calendar.app is unavailable
- Detailed error reporting for troubleshooting
"""

import subprocess
import time
from datetime import datetime, timedelta
from functools import wraps
from typing import List, Dict, Optional, Callable, TypeVar

from .config import COURSE_NAMES, CODE_TO_ALIAS, ALIAS_TO_CODE
from .errors import (
    CalendarError,
    CalendarConnectionError,
    CalendarPermissionError,
    CalendarTimeoutError,
    CalendarEventError,
)

CALENDAR_NAME = "Study Schedule"
DEFAULT_TIMEOUT = 60
MAX_RETRIES = 3
RETRY_DELAY = 1.0  # seconds

T = TypeVar("T")


def with_retry(
    max_retries: int = MAX_RETRIES,
    delay: float = RETRY_DELAY,
    exceptions: tuple = (CalendarError,),
) -> Callable:
    """
    Decorator that retries a function on specified exceptions.

    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay between retries in seconds
        exceptions: Tuple of exception types to catch and retry
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error: Optional[Exception] = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_error = e
                    if attempt < max_retries:
                        time.sleep(delay * (attempt + 1))  # Exponential backoff
                    continue
            if last_error is not None:
                raise last_error
            raise RuntimeError("Retry logic failed unexpectedly")

        return wrapper

    return decorator


def run_applescript(script: str, timeout: int = DEFAULT_TIMEOUT) -> str:
    """
    Run AppleScript and return output with comprehensive error handling.

    Args:
        script: AppleScript code to execute
        timeout: Timeout in seconds

    Returns:
        Script output as string

    Raises:
        CalendarConnectionError: If Calendar.app cannot be accessed
        CalendarPermissionError: If calendar access is denied
        CalendarTimeoutError: If operation times out
        CalendarError: For other AppleScript errors
    """
    try:
        result = subprocess.run(
            ["osascript", "-e", script], capture_output=True, text=True, timeout=timeout
        )
    except subprocess.TimeoutExpired:
        raise CalendarTimeoutError("AppleScript execution", timeout)
    except FileNotFoundError:
        raise CalendarConnectionError("osascript not found - this tool requires macOS")
    except PermissionError:
        raise CalendarPermissionError()

    if result.returncode != 0:
        stderr = result.stderr.strip()

        # Parse common AppleScript errors
        if "Not authorized" in stderr or "not allowed" in stderr.lower():
            raise CalendarPermissionError()
        elif "Calendar got an error" in stderr:
            if "doesn't understand" in stderr:
                raise CalendarConnectionError(
                    "Calendar.app version incompatible or corrupted"
                )
            raise CalendarError(f"Calendar error: {stderr}")
        elif "Connection is invalid" in stderr:
            raise CalendarConnectionError("Calendar.app is not responding")
        elif "Application isn't running" in stderr:
            raise CalendarConnectionError(
                "Calendar.app is not running. It will be started automatically on next attempt."
            )
        else:
            raise CalendarError(f"AppleScript error: {stderr}")

    return result.stdout.strip()


def check_calendar_available() -> bool:
    """
    Check if Calendar.app is available and accessible.

    Returns:
        True if calendar is available

    Raises:
        CalendarConnectionError: If calendar is not available
        CalendarPermissionError: If access is denied
    """
    script = """
    tell application "System Events"
        return exists application process "Calendar"
    end tell
    """
    try:
        run_applescript(script, timeout=10)
        return True
    except CalendarTimeoutError:
        raise CalendarConnectionError("Calendar.app is unresponsive")


@with_retry(max_retries=2, exceptions=(CalendarConnectionError,))
def create_calendar() -> str:
    """
    Create the Study Schedule calendar if it doesn't exist.

    Returns:
        'created' if new calendar was created, 'exists' if already exists

    Raises:
        CalendarError: If calendar creation fails
    """
    script = f'''
    tell application "Calendar"
        if not (exists calendar "{CALENDAR_NAME}") then
            make new calendar with properties {{name:"{CALENDAR_NAME}"}}
            return "created"
        else
            return "exists"
        end if
    end tell
    '''
    return run_applescript(script)


def clear_calendar() -> int:
    """
    Clear all events by deleting and recreating the calendar.

    This is much faster than deleting events one by one.

    Returns:
        1 if calendar was cleared, 0 otherwise
    """
    # Delete calendar if it exists, then create fresh
    script = f'''
    tell application "Calendar"
        try
            delete calendar "{CALENDAR_NAME}"
        end try
        make new calendar with properties {{name:"{CALENDAR_NAME}"}}
        return "ok"
    end tell
    '''
    try:
        run_applescript(script, timeout=30)
        return 1
    except CalendarError as e:
        # Try just creating it
        try:
            create_calendar()
            return 0
        except CalendarError:
            print(f"Warning: Could not clear calendar: {e}")
            return 0


def _escape_applescript(s: str) -> str:
    """Escape special characters for AppleScript strings."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _format_event_script(
    summary: str,
    start: datetime,
    end: datetime,
    description: str = "",
    alerts: Optional[List[int]] = None,
) -> str:
    """Generate AppleScript commands for a single event (no tell block)."""
    start_str = start.strftime("%A, %d %B %Y at %H:%M:%S")
    end_str = end.strftime("%A, %d %B %Y at %H:%M:%S")
    summary_escaped = _escape_applescript(summary)
    description_escaped = _escape_applescript(description)

    alert_commands = ""
    if alerts:
        for mins in alerts:
            alert_commands += f"""
            make new sound alarm with properties {{trigger interval:{mins}}}"""

    script = f'''
        set newEvent to make new event at studyCal with properties {{summary:"{summary_escaped}", start date:date "{start_str}", end date:date "{end_str}", description:"{description_escaped}"}}'''

    if alert_commands:
        script += f"""
        tell newEvent{alert_commands}
        end tell"""

    return script


@with_retry(max_retries=2)
def add_events_batch(events: List[Dict]) -> int:
    """
    Add multiple events in a single AppleScript call.

    Args:
        events: List of event dicts with keys: summary, start, end, description, alerts

    Returns:
        Number of events created successfully
    """
    if not events:
        return 0

    # Build all event creation commands
    event_scripts = []
    for evt in events:
        script = _format_event_script(
            summary=evt["summary"],
            start=evt["start"],
            end=evt["end"],
            description=evt.get("description", ""),
            alerts=evt.get("alerts"),
        )
        event_scripts.append(script)

    # Combine into single AppleScript
    combined_script = f'''
    tell application "Calendar"
        set studyCal to calendar "{CALENDAR_NAME}"
        {"".join(event_scripts)}
        return {len(events)}
    end tell
    '''

    try:
        result = run_applescript(combined_script, timeout=120)
        return int(result) if result.isdigit() else len(events)
    except CalendarError as e:
        raise CalendarEventError("batch creation", str(e))


def add_plan_to_calendar(blocks: List[Dict], start_time: datetime) -> int:
    """
    Add study plan blocks to calendar.

    Args:
        blocks: List of plan blocks with keys: course_name, course_code, duration_mins
        start_time: When the plan starts

    Returns:
        Number of events created
    """
    events = []
    current_time = start_time

    for block in blocks:
        end_time = current_time + timedelta(minutes=block["duration_mins"])
        alias = CODE_TO_ALIAS.get(block["course_code"], "??")

        events.append(
            {
                "summary": f"STUDY: [{alias}] {block['course_name']}",
                "start": current_time,
                "end": end_time,
                "description": f"Study block: {block['course_name']}\nDuration: {block['duration_mins']} min",
                "alerts": [-5],  # 5 min warning before end
            }
        )

        current_time = end_time

    return add_events_batch(events)


def collect_deadline_events() -> List[Dict]:
    """
    Collect all deadline events from Taskwarrior.

    Returns:
        List of event dicts ready for batch creation
    """
    from .taskwarrior import get_tasks_with_due_dates, parse_taskwarrior_date, get_course_from_project

    tasks = get_tasks_with_due_dates()
    events = []

    for task in tasks:
        # Get due date
        due_str = task.get("due", "")
        if not due_str:
            continue

        due_date = parse_taskwarrior_date(due_str)
        if not due_date:
            continue

        # Get course from project
        project = task.get("project", "")
        alias = get_course_from_project(project) or "??"
        course_code = task.get("course_code", "")
        course_name = COURSE_NAMES.get(course_code, alias.upper())

        description = task.get("description", "")
        weight = task.get("weight", "")

        # Set event times (default to 15:00-16:00)
        start_date = due_date.replace(hour=15, minute=0, second=0, microsecond=0)
        end_date = due_date.replace(hour=16, minute=0, second=0, microsecond=0)

        # Check for exam in description
        if "exam" in description.lower():
            summary = f"EXAM: [{alias}] {description}"
        else:
            summary = f"DEADLINE: [{alias}] {description}"

        # Build description
        desc = f"{course_name}\n{description}"
        if weight:
            desc += f"\nWeight: {weight}"

        events.append(
            {
                "summary": summary,
                "start": start_date,
                "end": end_date,
                "description": desc,
                "alerts": [-1440, -120, -30],  # 1 day, 2 hours, 30 mins
            }
        )

    return events


def collect_study_sessions(
    start_date: datetime, end_date: datetime, schedule: Dict[str, Dict]
) -> List[Dict]:
    """
    Collect recurring study session events.

    Args:
        start_date: First day to generate
        end_date: Last day to generate
        schedule: Dict mapping weekday names to session configs

    Returns:
        List of event dicts ready for batch creation
    """
    events = []
    current = start_date

    while current <= end_date:
        weekday = current.strftime("%A")

        if weekday in schedule:
            session = schedule[weekday]
            start_time = datetime.strptime(session["start"], "%H:%M").time()
            end_time = datetime.strptime(session["end"], "%H:%M").time()

            event_start = current.replace(
                hour=start_time.hour, minute=start_time.minute, second=0, microsecond=0
            )
            event_end = current.replace(
                hour=end_time.hour, minute=end_time.minute, second=0, microsecond=0
            )

            events.append(
                {
                    "summary": session["title"],
                    "start": event_start,
                    "end": event_end,
                    "description": session.get("description", ""),
                }
            )

        current += timedelta(days=1)

    return events


def sync_calendar(regenerate: bool = True) -> Dict[str, int]:
    """
    Sync calendar with current tracker data.

    Uses batch event creation for performance (single AppleScript call
    instead of one per event).

    Args:
        regenerate: If True (default), clear existing events first to avoid duplicates

    Returns:
        Dict with counts of created events by type

    Raises:
        CalendarConnectionError: If Calendar.app is not available
        CalendarPermissionError: If calendar access is denied
    """
    results = {"deadlines": 0, "study_sessions": 0, "failed": 0, "cleared": 0}

    # Clear calendar by deleting and recreating (much faster than deleting events)
    results["cleared"] = clear_calendar()
    today = datetime.now()

    # Collect all events first (fast, no I/O)
    deadline_events = collect_deadline_events()
    results["deadlines"] = len(deadline_events)

    # Study session schedule
    study_schedule = {
        "Monday": {
            "title": "Study: Predictive Control",
            "start": "09:00",
            "end": "12:00",
            "description": "MATLAB Grader assignments, review lecture notes",
        },
        "Tuesday": {
            "title": "Study: Distributed Optimisation",
            "start": "09:00",
            "end": "11:00",
            "description": "Problem Sets, review lecture material",
        },
        "Wednesday": {
            "title": "Study: Computer Vision & PR",
            "start": "10:00",
            "end": "13:00",
            "description": "Coursework, review Friday lectures",
        },
        "Thursday": {
            "title": "Study: Review Session",
            "start": "12:00",
            "end": "14:00",
            "description": "Review morning lecture, prep for afternoon",
        },
        "Friday": {
            "title": "WATCH: Applied Adv. Optimisation Videos",
            "start": "09:00",
            "end": "11:00",
            "description": "MUST WATCH before class! iRAT test is based on these",
        },
        "Saturday": {
            "title": "Study: Deep Work (Deadline Priority)",
            "start": "10:00",
            "end": "13:00",
            "description": "Focus on most urgent deadline",
        },
        "Sunday": {
            "title": "Study: Weekly Review & Catch-up",
            "start": "14:00",
            "end": "17:00",
            "description": "Review week, prep for next week",
        },
    }

    # Collect study sessions for next 10 weeks
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    start = today + timedelta(days=days_until_monday - 7)  # Include this week
    end = start + timedelta(weeks=10)

    session_events = collect_study_sessions(start, end, study_schedule)
    results["study_sessions"] = len(session_events)

    # Batch create all events in a single AppleScript call
    all_events = deadline_events + session_events
    try:
        add_events_batch(all_events)
    except CalendarEventError:
        results["failed"] = len(all_events)
        results["deadlines"] = 0
        results["study_sessions"] = 0

    return results
