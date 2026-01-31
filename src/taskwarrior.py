"""
Taskwarrior adapter module.

Provides functions to interact with Taskwarrior for task management.
"""

import json
import subprocess
from datetime import datetime
from typing import Dict, List, Optional

from .config import ALIAS_TO_CODE, CODE_TO_ALIAS, COURSE_NAMES


def run_task_command(args: List[str], capture_output: bool = True) -> subprocess.CompletedProcess:
    """
    Run a Taskwarrior command.

    Args:
        args: Command arguments (without 'task' prefix)
        capture_output: Whether to capture stdout/stderr

    Returns:
        CompletedProcess result
    """
    cmd = ["task"] + args
    return subprocess.run(cmd, capture_output=capture_output, text=True)


def get_all_tasks() -> List[Dict]:
    """
    Get all tasks from Taskwarrior.

    Returns:
        List of task dictionaries
    """
    result = run_task_command(["export"])
    if result.returncode != 0:
        return []
    return json.loads(result.stdout) if result.stdout.strip() else []


def get_pending_tasks() -> List[Dict]:
    """
    Get all pending (not completed) tasks.

    Returns:
        List of pending task dictionaries
    """
    result = run_task_command(["status:pending", "export"])
    if result.returncode != 0:
        return []
    return json.loads(result.stdout) if result.stdout.strip() else []


def get_tasks_by_course(course_alias: str) -> List[Dict]:
    """
    Get all tasks for a specific course.

    Args:
        course_alias: Course alias (pc, do, cv, ao)

    Returns:
        List of task dictionaries for that course
    """
    result = run_task_command([f"project.startswith:{course_alias}", "export"])
    if result.returncode != 0:
        return []
    return json.loads(result.stdout) if result.stdout.strip() else []


def get_tasks_with_due_dates() -> List[Dict]:
    """
    Get all pending tasks that have due dates.

    Returns:
        List of task dictionaries with due dates
    """
    result = run_task_command(["status:pending", "due.any:", "export"])
    if result.returncode != 0:
        return []
    return json.loads(result.stdout) if result.stdout.strip() else []


def parse_taskwarrior_date(date_str: str) -> Optional[datetime]:
    """
    Parse a Taskwarrior ISO 8601 date string.

    Taskwarrior uses format: 20260130T160000Z

    Args:
        date_str: Taskwarrior date string

    Returns:
        datetime object or None if parsing fails
    """
    if not date_str:
        return None

    try:
        # Remove 'Z' suffix and parse
        clean = date_str.rstrip("Z")
        return datetime.strptime(clean, "%Y%m%dT%H%M%S")
    except ValueError:
        try:
            # Try alternate format
            return datetime.fromisoformat(date_str.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            return None


def format_date_for_taskwarrior(dt: datetime) -> str:
    """
    Format a datetime for Taskwarrior.

    Args:
        dt: datetime object

    Returns:
        Taskwarrior-compatible date string (YYYY-MM-DD)
    """
    return dt.strftime("%Y-%m-%d")


def add_task(
    description: str,
    project: str,
    due: Optional[str] = None,
    weight: Optional[str] = None,
    score: Optional[str] = None,
    course_code: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> Optional[int]:
    """
    Add a new task to Taskwarrior.

    Args:
        description: Task description
        project: Project name (e.g., "pc.basic_part_1")
        due: Due date (YYYY-MM-DD format)
        weight: Assessment weight (e.g., "5%")
        score: Score if completed
        course_code: Full course code (e.g., "ELEC70028")
        tags: List of tags

    Returns:
        Task ID if successful, None otherwise
    """
    cmd = ["add", description, f"project:{project}"]

    if due:
        cmd.append(f"due:{due}")
    if weight:
        cmd.append(f"weight:{weight}")
    if score:
        cmd.append(f"score:{score}")
    if course_code:
        cmd.append(f"course_code:{course_code}")
    if tags:
        for tag in tags:
            cmd.append(f"+{tag}")

    result = run_task_command(cmd)
    if result.returncode == 0:
        # Parse task ID from output like "Created task 1."
        output = result.stdout.strip()
        if "Created task" in output:
            try:
                return int(output.split()[-1].rstrip("."))
            except (ValueError, IndexError):
                pass
    return None


def modify_task(task_id: int, **changes) -> bool:
    """
    Modify a task.

    Args:
        task_id: Task ID
        **changes: Key-value pairs to modify

    Returns:
        True if successful
    """
    cmd = [str(task_id), "modify"]
    for key, value in changes.items():
        if key == "tags_add":
            for tag in value:
                cmd.append(f"+{tag}")
        elif key == "tags_remove":
            for tag in value:
                cmd.append(f"-{tag}")
        else:
            cmd.append(f"{key}:{value}")

    result = run_task_command(cmd)
    return result.returncode == 0


def complete_task(task_id: int) -> bool:
    """
    Mark a task as complete.

    Args:
        task_id: Task ID

    Returns:
        True if successful
    """
    result = run_task_command([str(task_id), "done"])
    return result.returncode == 0


def get_course_from_project(project: str) -> Optional[str]:
    """
    Extract course alias from project name.

    Args:
        project: Project name (e.g., "pc.basic_part_1")

    Returns:
        Course alias (e.g., "pc") or None
    """
    if not project:
        return None
    return project.split(".")[0]


def get_assessment_key_from_project(project: str) -> Optional[str]:
    """
    Extract assessment key from project name.

    Args:
        project: Project name (e.g., "pc.basic_part_1")

    Returns:
        Assessment key (e.g., "basic_part_1") or None
    """
    if not project or "." not in project:
        return None
    parts = project.split(".", 1)
    return parts[1] if len(parts) > 1 else None
