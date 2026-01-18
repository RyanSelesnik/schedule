"""
Generate markdown files from tracker data (single source of truth).

Provides safe file generation with:
- Atomic writes (write to temp, then rename)
- Graceful error handling
- Validation of generated content
"""

import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from .config import DEADLINES_PATH, COURSE_NAMES, CODE_TO_ALIAS
from .data import load_tracker
from .errors import DataError, DataWriteError


def _safe_write_file(path: Path, content: str) -> Path:
    """
    Safely write content to a file using atomic write pattern.

    Args:
        path: Destination file path
        content: Content to write

    Returns:
        Path to written file

    Raises:
        DataWriteError: If write fails
    """
    # Check parent directory exists
    if not path.parent.exists():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
        except PermissionError:
            raise DataWriteError(
                str(path), "Cannot create parent directory - permission denied"
            )
        except OSError as e:
            raise DataWriteError(str(path), f"Cannot create parent directory: {e}")

    # Check write permission
    if path.exists() and not os.access(path, os.W_OK):
        raise DataWriteError(str(path), "Permission denied")

    if not path.exists() and not os.access(path.parent, os.W_OK):
        raise DataWriteError(str(path), "Cannot write to directory - permission denied")

    # Write to temp file first
    temp_path = path.with_suffix(".tmp")

    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
    except PermissionError:
        raise DataWriteError(str(temp_path), "Permission denied")
    except OSError as e:
        raise DataWriteError(str(temp_path), str(e))

    # Atomic rename
    try:
        temp_path.rename(path)
    except OSError as e:
        try:
            temp_path.unlink()
        except OSError:
            pass
        raise DataWriteError(str(path), f"Failed to rename temp file: {e}")

    return path


def generate_deadlines_md() -> Path:
    """
    Generate deadlines.md from tracker.json.

    Returns:
        Path to generated file

    Raises:
        DataError: If tracker data cannot be loaded
        DataWriteError: If file cannot be written
    """
    data = load_tracker()
    today = datetime.now()

    lines = [
        "# Assessment Deadlines Overview",
        "",
        f"**Generated:** {today.strftime('%Y-%m-%d %H:%M')}",
        "",
        "> This file is auto-generated from tracker.json. Do not edit manually.",
        "> Run `study generate` to regenerate.",
        "",
        "## Upcoming Deadlines",
        "",
    ]

    # Collect all deadlines
    deadlines = []
    for code, course in data["courses"].items():
        for key, assessment in course["assessments"].items():
            deadline = assessment.get("deadline", "")
            status = assessment.get("status", "not_started")

            if not deadline or deadline in ("TBD", "ongoing"):
                continue

            try:
                # Handle date range
                dl_str = deadline.split(" to ")[0] if " to " in deadline else deadline
                dl_date = datetime.strptime(dl_str, "%Y-%m-%d")
                deadlines.append(
                    {
                        "date": dl_date,
                        "deadline_str": deadline,
                        "code": code,
                        "key": key,
                        "name": assessment["name"],
                        "status": status,
                        "weight": assessment.get("weight", ""),
                    }
                )
            except (ValueError, KeyError):
                # Skip entries with invalid dates or missing name
                continue

    deadlines.sort(key=lambda x: x["date"])

    # Group by month
    current_month: Optional[str] = None
    for dl in deadlines:
        month = dl["date"].strftime("%B %Y")
        if month != current_month:
            current_month = month
            lines.append(f"### {month}")
            lines.append("")
            lines.append("| Date | Time | Course | Assessment | Weight | Status |")
            lines.append("|------|------|--------|------------|--------|--------|")

        alias: str = CODE_TO_ALIAS.get(dl["code"], "??")
        course_name: str = COURSE_NAMES.get(dl["code"]) or dl["code"]
        date_str = dl["date"].strftime("%d %b")
        weight = dl["weight"] if dl["weight"] else "-"

        # Status with emoji
        status_display = {
            "not_started": "⬜ Not started",
            "in_progress": "🔄 In progress",
            "completed": "✅ Completed",
            "submitted": "📤 Submitted",
            "overdue": "🔴 Overdue",
        }.get(dl["status"], dl["status"])

        # Check if overdue
        days_left = (dl["date"] - today).days
        if days_left < 0 and dl["status"] not in ("completed", "submitted"):
            status_display = f"🔴 OVERDUE ({-days_left}d)"
        elif days_left <= 3 and dl["status"] not in ("completed", "submitted"):
            status_display = f"⚠️ {days_left}d left"

        # Extract time if present
        deadline_str = dl["deadline_str"]
        time_str = "-"
        if "T" in deadline_str:
            time_str = deadline_str.split("T")[-1]

        lines.append(
            f"| {date_str} | {time_str} | "
            f"[{alias}] {course_name[:20]} | {dl['name']} | {weight} | {status_display} |"
        )

    lines.append("")

    # Summary by course
    lines.append("## Summary by Course")
    lines.append("")

    for code, course in data["courses"].items():
        alias = CODE_TO_ALIAS.get(code, "??")
        name = COURSE_NAMES.get(code, code)
        lines.append(f"### [{alias}] {name}")
        lines.append("")

        total = 0
        completed = 0
        for key, assessment in course["assessments"].items():
            total += 1
            status = assessment.get("status", "")
            if status in ("completed", "submitted"):
                completed += 1

            status_emoji = {
                "not_started": "⬜",
                "in_progress": "🔄",
                "completed": "✅",
                "submitted": "📤",
                "overdue": "🔴",
                "ongoing": "🔁",
            }.get(status, "❓")

            deadline = assessment.get("deadline", "TBD")
            weight = assessment.get("weight", "")
            weight_str = f" ({weight})" if weight else ""
            assessment_name = assessment.get("name", key)

            lines.append(
                f"- {status_emoji} **{assessment_name}**{weight_str} — {deadline}"
            )

        lines.append(f"\nProgress: {completed}/{total} completed")
        lines.append("")

    content = "\n".join(lines)
    return _safe_write_file(DEADLINES_PATH, content)


def generate_all() -> List[Path]:
    """
    Generate all markdown files from tracker data.

    Returns:
        List of generated file paths

    Raises:
        DataError: If tracker data cannot be loaded
        DataWriteError: If any file cannot be written
    """
    generated = []
    errors = []

    # Generate each file, collecting errors
    try:
        generated.append(generate_deadlines_md())
    except DataWriteError as e:
        errors.append(f"deadlines.md: {e.message}")

    # If all generations failed, raise an error
    if errors and not generated:
        raise DataWriteError(
            "all files",
            "Failed to generate any files:\n" + "\n".join(f"  - {e}" for e in errors),
        )

    # If some failed, print warnings but return what we got
    if errors:
        print(f"\nWarnings during generation:")
        for err in errors:
            print(f"  - {err}")

    return generated
