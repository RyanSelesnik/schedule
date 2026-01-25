"""
Study session planner with timed blocks and notifications.

Allows creating multi-block study plans like "1h do, 1h pc" that:
- Schedule macOS notifications at transition times
- Auto-log hours when blocks complete
- Sync plan to calendar
"""

import json
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .config import BASE_DIR, ALIAS_TO_CODE, CODE_TO_ALIAS, COURSE_NAMES
from .errors import ValidationError, DataWriteError
from .notifications import send_study_notification

PLAN_PATH = BASE_DIR / "plan.json"


def parse_duration(duration_str: str) -> int:
    """
    Parse a duration string into minutes.

    Accepts formats:
        "1h" -> 60
        "1.5h" -> 90
        "30m" -> 30
        "1h30m" -> 90
        "90" -> 90 (assumes minutes)

    Returns:
        Duration in minutes

    Raises:
        ValidationError: If format is invalid
    """
    duration_str = duration_str.strip().lower()

    # Try combined format first (1h30m)
    combined = re.match(r"^(\d+(?:\.\d+)?)\s*h\s*(\d+)\s*m?$", duration_str)
    if combined:
        hours = float(combined.group(1))
        mins = int(combined.group(2))
        return int(hours * 60 + mins)

    # Hours only (1h, 1.5h)
    hours_match = re.match(r"^(\d+(?:\.\d+)?)\s*h$", duration_str)
    if hours_match:
        return int(float(hours_match.group(1)) * 60)

    # Minutes only (30m, 30min)
    mins_match = re.match(r"^(\d+)\s*m(?:in)?$", duration_str)
    if mins_match:
        return int(mins_match.group(1))

    # Bare number (assumes minutes)
    if duration_str.isdigit():
        return int(duration_str)

    raise ValidationError(
        f"Invalid duration format: {duration_str}. Use formats like: 1h, 30m, 1.5h, 1h30m, or 90",
    )


def resolve_course(course_input: str) -> Tuple[str, str]:
    """
    Resolve a course alias or partial name to (code, name).

    Args:
        course_input: Alias (pc, do, cv, ao) or partial name

    Returns:
        Tuple of (course_code, course_name)

    Raises:
        ValidationError: If course cannot be resolved
    """
    course_input = course_input.strip().lower()

    # Check aliases first
    if course_input in ALIAS_TO_CODE:
        code = ALIAS_TO_CODE[course_input]
        return code, COURSE_NAMES[code]

    # Check partial name match
    for code, name in COURSE_NAMES.items():
        if course_input in name.lower():
            return code, name

    # Check full code
    upper = course_input.upper()
    if upper in COURSE_NAMES:
        return upper, COURSE_NAMES[upper]

    raise ValidationError(
        f"Unknown course: {course_input}",
        valid_options=list(ALIAS_TO_CODE.keys()),
    )


def parse_plan_string(plan_str: str) -> List[Dict]:
    """
    Parse a plan string into blocks.

    Formats:
        "1h do, 1h pc"
        "1h do 1h pc"
        "1h distributed, 30m vision"

    Returns:
        List of block dicts: [{"course_code": ..., "course_name": ..., "duration_mins": ...}]
    """
    # Split by comma or just spaces with duration markers
    # First try comma-separated
    if "," in plan_str:
        parts = [p.strip() for p in plan_str.split(",")]
    else:
        # Try to split on duration patterns
        parts = re.split(r"(?=\d+(?:\.\d+)?[hm])", plan_str)
        parts = [p.strip() for p in parts if p.strip()]

    blocks = []
    for part in parts:
        # Match "duration course"
        match = re.match(r"^(\d+(?:\.\d+)?[hm]?\d*m?)\s+(.+)$", part, re.IGNORECASE)
        if not match:
            raise ValidationError(
                f"Cannot parse block: {part}. Use format: <duration> <course>, e.g., '1h do' or '30m pc'",
            )

        duration_str = match.group(1)
        course_str = match.group(2)

        duration_mins = parse_duration(duration_str)
        code, name = resolve_course(course_str)

        blocks.append(
            {
                "course_code": code,
                "course_name": name,
                "duration_mins": duration_mins,
            }
        )

    if not blocks:
        raise ValidationError("No valid blocks found in plan")

    return blocks


def load_plan() -> Optional[Dict]:
    """Load the current plan from plan.json."""
    if not PLAN_PATH.exists():
        return None

    try:
        with open(PLAN_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def save_plan(plan: Dict) -> None:
    """Save a plan to plan.json."""
    try:
        with open(PLAN_PATH, "w") as f:
            json.dump(plan, f, indent=2, default=str)
    except OSError as e:
        raise DataWriteError(str(PLAN_PATH), str(e))


def clear_plan() -> None:
    """Remove the plan file."""
    if PLAN_PATH.exists():
        PLAN_PATH.unlink()


def get_plan_status() -> Optional[Dict]:
    """
    Get the current status of the active plan.

    Returns:
        Dict with:
            - current_block: index (0-based)
            - current_course: name
            - time_remaining_mins: in current block
            - next_course: name or None
            - total_remaining_mins: total time left
            - blocks: list of all blocks
        Or None if no plan is active
    """
    plan = load_plan()
    if not plan:
        return None

    now = datetime.now()
    start = datetime.fromisoformat(plan["start_time"])

    # Find current block
    elapsed = (now - start).total_seconds() / 60
    cumulative = 0
    current_idx = 0

    for i, block in enumerate(plan["blocks"]):
        cumulative += block["duration_mins"]
        if elapsed < cumulative:
            current_idx = i
            break
    else:
        # Plan is complete
        return {
            "completed": True,
            "blocks": plan["blocks"],
            "total_mins": sum(b["duration_mins"] for b in plan["blocks"]),
        }

    current_block = plan["blocks"][current_idx]
    block_start = sum(b["duration_mins"] for b in plan["blocks"][:current_idx])
    time_in_block = elapsed - block_start
    time_remaining = current_block["duration_mins"] - time_in_block

    next_course = None
    if current_idx + 1 < len(plan["blocks"]):
        next_course = plan["blocks"][current_idx + 1]["course_name"]

    total_remaining = (
        sum(b["duration_mins"] for b in plan["blocks"][current_idx:]) - time_in_block
    )

    return {
        "completed": False,
        "current_block": current_idx,
        "current_course": current_block["course_name"],
        "current_code": current_block["course_code"],
        "time_remaining_mins": max(0, time_remaining),
        "next_course": next_course,
        "total_remaining_mins": max(0, total_remaining),
        "blocks": plan["blocks"],
        "start_time": start,
    }


def schedule_notification(when: datetime, block_idx: int) -> bool:
    """
    Schedule a notification using the 'at' command.

    Args:
        when: When to fire the notification
        block_idx: Which block just completed

    Returns:
        True if scheduled successfully
    """
    # Create the command that 'at' will run
    script_path = BASE_DIR / "scripts" / "plan_notify.py"
    python_path = subprocess.run(
        ["which", "python3"], capture_output=True, text=True
    ).stdout.strip()

    if not python_path:
        python_path = "python3"

    cmd = f'{python_path} "{script_path}" {block_idx}'

    # Format time for 'at' command
    at_time = when.strftime("%H:%M %Y-%m-%d")

    try:
        # Use 'at' to schedule the command
        result = subprocess.run(
            ["at", "-t", when.strftime("%Y%m%d%H%M")],
            input=cmd,
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def create_plan(plan_str: str) -> Dict:
    """
    Create and start a new study plan.

    Args:
        plan_str: Plan specification, e.g., "1h do, 1h pc"

    Returns:
        Dict with plan details

    Raises:
        ValidationError: If plan cannot be parsed
    """
    blocks = parse_plan_string(plan_str)
    now = datetime.now()

    plan = {
        "start_time": now.isoformat(),
        "blocks": blocks,
        "created_at": now.isoformat(),
    }

    # Schedule notifications for each block transition
    cumulative_mins = 0
    scheduled = []
    for i, block in enumerate(blocks):
        cumulative_mins += block["duration_mins"]
        notify_time = now + timedelta(minutes=cumulative_mins)

        if schedule_notification(notify_time, i):
            scheduled.append(i)

    plan["notifications_scheduled"] = scheduled

    # Add to calendar
    try:
        from .calendar_sync import add_plan_to_calendar

        calendar_events = add_plan_to_calendar(blocks, now)
        plan["calendar_events"] = calendar_events
    except Exception:
        # Calendar sync is best-effort, don't fail the plan creation
        plan["calendar_events"] = 0

    # Send start notification
    first_block = blocks[0]
    send_study_notification(
        first_block["course_name"],
        action="start",
        duration_mins=first_block["duration_mins"],
    )

    save_plan(plan)

    return plan


def stop_plan(log_partial: bool = True) -> Optional[Dict]:
    """
    Stop the current plan and optionally log partial hours.

    Args:
        log_partial: If True, log hours for completed portion

    Returns:
        Dict with summary of what was logged, or None if no plan
    """
    status = get_plan_status()
    if not status:
        return None

    logged = []

    if log_partial and not status.get("completed"):
        # Import here to avoid circular dependency
        from .tracker import log_hours

        # Log completed blocks
        for i, block in enumerate(status["blocks"]):
            if i < status["current_block"]:
                # Fully completed block
                hours = block["duration_mins"] / 60
                log_hours(
                    str(hours),
                    CODE_TO_ALIAS.get(block["course_code"], block["course_code"]),
                )
                logged.append(
                    {
                        "course": block["course_name"],
                        "hours": hours,
                        "complete": True,
                    }
                )
            elif i == status["current_block"]:
                # Partial block
                elapsed_mins = block["duration_mins"] - status["time_remaining_mins"]
                if elapsed_mins > 5:  # Only log if at least 5 mins
                    hours = elapsed_mins / 60
                    log_hours(
                        str(hours),
                        CODE_TO_ALIAS.get(block["course_code"], block["course_code"]),
                    )
                    logged.append(
                        {
                            "course": block["course_name"],
                            "hours": hours,
                            "complete": False,
                        }
                    )

    # Cancel any pending 'at' jobs (best effort)
    try:
        # List at jobs and cancel them
        result = subprocess.run(["atq"], capture_output=True, text=True, timeout=5)
        for line in result.stdout.strip().split("\n"):
            if line:
                job_id = line.split()[0]
                subprocess.run(["atrm", job_id], capture_output=True, timeout=5)
    except (subprocess.TimeoutExpired, OSError):
        pass

    clear_plan()

    return {"logged": logged, "stopped_at": datetime.now().isoformat()}
