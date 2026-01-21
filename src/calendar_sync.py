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

from .config import COURSE_NAMES, CODE_TO_ALIAS
from .data import load_tracker, load_courses
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


def clear_calendar_events(start_date: datetime, end_date: datetime) -> int:
    """
    Clear events in date range (for regeneration).

    Args:
        start_date: Start of date range
        end_date: End of date range

    Returns:
        Number of events deleted

    Raises:
        CalendarError: If clearing fails
    """
    script = f'''
    tell application "Calendar"
        set studyCal to calendar "{CALENDAR_NAME}"
        set startDate to date "{start_date.strftime("%A, %d %B %Y")}"
        set endDate to date "{end_date.strftime("%A, %d %B %Y")}"
        set eventsToDelete to (every event of studyCal whose start date >= startDate and start date <= endDate)
        set deletedCount to count of eventsToDelete
        repeat with evt in eventsToDelete
            delete evt
        end repeat
        return deletedCount
    end tell
    '''
    try:
        result = run_applescript(script)
        return int(result) if result.isdigit() else 0
    except CalendarError as e:
        # Log but don't fail - clearing is optional
        print(f"Warning: Could not clear existing events: {e}")
        return 0


@with_retry(max_retries=2)
def add_event(
    summary: str,
    start: datetime,
    end: datetime,
    description: str = "",
    alerts: Optional[List[int]] = None,
) -> bool:
    """
    Add a single event to the calendar.

    Args:
        summary: Event title
        start: Start datetime
        end: End datetime
        description: Event description
        alerts: List of alert times in minutes before event (negative values)

    Returns:
        True if event was created successfully

    Raises:
        CalendarEventError: If event creation fails after retries
    """
    if alerts is None:
        alerts = []

    start_str = start.strftime("%A, %d %B %Y at %H:%M:%S")
    end_str = end.strftime("%A, %d %B %Y at %H:%M:%S")

    # Escape special characters in strings for AppleScript
    summary_escaped = summary.replace("\\", "\\\\").replace('"', '\\"')
    description_escaped = description.replace("\\", "\\\\").replace('"', '\\"')

    alert_commands = ""
    if alerts:
        for mins in alerts:
            alert_commands += f"""
                make new sound alarm with properties {{trigger interval:{mins}}}
            """

    script = f'''
    tell application "Calendar"
        set studyCal to calendar "{CALENDAR_NAME}"
        set newEvent to make new event at studyCal with properties {{summary:"{summary_escaped}", start date:date "{start_str}", end date:date "{end_str}", description:"{description_escaped}"}}
        tell newEvent
            {alert_commands}
        end tell
        return "success"
    end tell
    '''

    try:
        run_applescript(script)
        return True
    except CalendarError as e:
        raise CalendarEventError(summary, str(e))


def generate_deadline_events() -> Dict[str, int]:
    """
    Generate calendar events for all deadlines from tracker.json.

    Returns:
        Dict with 'created' and 'failed' counts
    """
    data = load_tracker()
    results = {"created": 0, "failed": 0, "skipped": 0}
    errors = []

    for code, course in data["courses"].items():
        alias = CODE_TO_ALIAS.get(code, "??")
        course_name = COURSE_NAMES.get(code, code)

        for key, assessment in course["assessments"].items():
            deadline = assessment.get("deadline", "")
            status = assessment.get("status", "")

            # Skip completed, submitted, or no deadline
            if status in ("completed", "submitted"):
                results["skipped"] += 1
                continue
            if not deadline or deadline in ("TBD", "ongoing"):
                results["skipped"] += 1
                continue

            try:
                # Parse deadline
                if " to " in deadline:
                    # Date range (e.g., oral exam)
                    start_str, end_str = deadline.split(" to ")
                    start_date = datetime.strptime(start_str, "%Y-%m-%d")
                    end_date = datetime.strptime(end_str, "%Y-%m-%d")
                    end_date = end_date.replace(hour=17, minute=0)
                    start_date = start_date.replace(hour=9, minute=0)
                    summary = f"EXAM: [{alias}] {assessment['name']}"
                else:
                    dl_date = datetime.strptime(deadline, "%Y-%m-%d")
                    # Check if it has a time component in the notes
                    assessment_str = str(assessment)
                    if "16:00" in assessment_str:
                        dl_date = dl_date.replace(hour=15, minute=0)
                        end_date = dl_date.replace(hour=16, minute=0)
                    elif "23:00" in assessment_str:
                        dl_date = dl_date.replace(hour=22, minute=0)
                        end_date = dl_date.replace(hour=23, minute=0)
                    else:
                        dl_date = dl_date.replace(hour=15, minute=0)
                        end_date = dl_date.replace(hour=16, minute=0)

                    start_date = dl_date
                    summary = f"DEADLINE: [{alias}] {assessment['name']}"

                # Add event with alerts
                weight = assessment.get("weight", "")
                desc = f"{course_name}\n{assessment['name']}"
                if weight:
                    desc += f"\nWeight: {weight}"

                if add_event(
                    summary=summary,
                    start=start_date,
                    end=end_date,
                    description=desc,
                    alerts=[-1440, -120, -30],  # 1 day, 2 hours, 30 mins
                ):
                    results["created"] += 1

            except ValueError as e:
                errors.append(f"{key}: invalid date format ({deadline})")
                results["failed"] += 1
            except CalendarEventError as e:
                errors.append(f"{key}: {e.message}")
                results["failed"] += 1

    # Report errors if any
    if errors:
        print(f"\nWarnings during deadline sync:")
        for err in errors[:5]:  # Show first 5
            print(f"  - {err}")
        if len(errors) > 5:
            print(f"  ... and {len(errors) - 5} more")

    return results


def generate_study_sessions(
    start_date: datetime, end_date: datetime, schedule: Dict[str, Dict]
) -> Dict[str, int]:
    """
    Generate recurring study sessions.

    Args:
        start_date: First day to generate
        end_date: Last day to generate
        schedule: Dict mapping weekday names to session configs

    Returns:
        Dict with 'created' and 'failed' counts
    """
    results = {"created": 0, "failed": 0}
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

            try:
                if add_event(
                    summary=session["title"],
                    start=event_start,
                    end=event_end,
                    description=session.get("description", ""),
                ):
                    results["created"] += 1
            except CalendarEventError:
                results["failed"] += 1

        current += timedelta(days=1)

    return results


def sync_calendar(regenerate: bool = True) -> Dict[str, int]:
    """
    Sync calendar with current tracker data.

    Args:
        regenerate: If True (default), clear existing events first to avoid duplicates

    Returns:
        Dict with counts of created events by type

    Raises:
        CalendarConnectionError: If Calendar.app is not available
        CalendarPermissionError: If calendar access is denied
    """
    # First, ensure we can access the calendar
    create_calendar()

    results = {"deadlines": 0, "study_sessions": 0, "failed": 0, "cleared": 0}

    # Always clear existing events to avoid duplicates
    today = datetime.now()
    end = today + timedelta(days=90)
    results["cleared"] = clear_calendar_events(today, end)

    # Generate deadline events
    deadline_results = generate_deadline_events()
    results["deadlines"] = deadline_results["created"]
    results["failed"] += deadline_results["failed"]

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

    # Generate for next 10 weeks
    today = datetime.now()
    # Start from next occurrence of Monday
    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    start = today + timedelta(days=days_until_monday - 7)  # Include this week
    end = start + timedelta(weeks=10)

    session_results = generate_study_sessions(start, end, study_schedule)
    results["study_sessions"] = session_results["created"]
    results["failed"] += session_results["failed"]

    return results
