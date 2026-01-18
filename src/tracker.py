"""
Core tracker operations.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict

from .config import COURSE_NAMES, CODE_TO_ALIAS, ALIAS_TO_CODE, VALID_STATUSES
from .data import load_tracker, save_tracker, get_course_display_name
from .errors import ValidationError, DataError
from .validation import (
    resolve_course_code,
    validate_status,
    validate_assessment_key,
    validate_hours,
)


def show_status() -> None:
    """Display all assessment statuses."""
    data = load_tracker()

    print("\n" + "=" * 60)
    print("STUDY TRACKER STATUS")
    print(f"Last updated: {data.get('last_updated', 'Unknown')}")
    print("=" * 60)

    for code, course in data["courses"].items():
        print(f"\n{get_course_display_name(code)}")
        print("-" * 45)

        for key, assessment in course["assessments"].items():
            status = assessment.get("status", "unknown")
            deadline = assessment.get("deadline", "TBD")
            weight = assessment.get("weight", "")
            score = assessment.get("score")

            status_emoji = {
                "not_started": "⬜",
                "in_progress": "🔄",
                "completed": "✅",
                "submitted": "📤",
                "overdue": "🔴",
                "ongoing": "🔁",
            }.get(status, "❓")

            score_str = f" [{score}]" if score else ""
            weight_str = f" ({weight})" if weight else ""
            print(
                f"  {status_emoji} {key:20} {assessment['name']}{weight_str}: {deadline}{score_str}"
            )


def show_courses() -> None:
    """Show all course codes and assessment keys."""
    data = load_tracker()

    print("\n" + "=" * 70)
    print("COURSE CODES & ASSESSMENT KEYS")
    print("=" * 70)

    print("\nShort codes (use these for quick commands):")
    print("-" * 45)
    for alias, code in sorted(ALIAS_TO_CODE.items(), key=lambda x: x[1]):
        print(f"  {alias:4} = {code}  ({COURSE_NAMES[code]})")

    print("\n" + "=" * 70)
    print("ASSESSMENT KEYS BY COURSE")
    print("=" * 70)

    for code, course in data["courses"].items():
        alias = CODE_TO_ALIAS.get(code, "??")
        print(f"\n[{alias}] {code} - {course['name']}")
        print("-" * 50)
        for key, assessment in course["assessments"].items():
            deadline = assessment.get("deadline", "TBD")
            status = assessment.get("status", "not_started")
            status_emoji = {"completed": "✅", "submitted": "📤"}.get(status, "  ")
            print(f"  {status_emoji} {key:20} - {assessment['name']} ({deadline})")


def show_next_deadlines(count: int = 5) -> None:
    """Show upcoming deadlines."""
    data = load_tracker()
    deadlines = []

    for code, course in data["courses"].items():
        for key, assessment in course["assessments"].items():
            deadline = assessment.get("deadline", "")
            status = assessment.get("status", "")

            if status in ["completed", "submitted"]:
                continue
            if deadline in ["TBD", "ongoing", ""]:
                continue

            try:
                if " to " in deadline:
                    deadline = deadline.split(" to ")[0]
                deadline_date = datetime.strptime(deadline, "%Y-%m-%d")
                deadlines.append(
                    {
                        "date": deadline_date,
                        "code": code,
                        "key": key,
                        "name": assessment["name"],
                        "status": status,
                    }
                )
            except ValueError:
                pass

    deadlines.sort(key=lambda x: x["date"])

    print("\n" + "=" * 55)
    print("NEXT DEADLINES")
    print("=" * 55)

    if not deadlines:
        print("\nNo upcoming deadlines! 🎉")
        return

    today = datetime.now()
    for dl in deadlines[:count]:
        days_left = (dl["date"] - today).days

        if days_left < 0:
            days_str = f"🔴 OVERDUE by {-days_left} days!"
        elif days_left == 0:
            days_str = "⚠️  DUE TODAY!"
        elif days_left == 1:
            days_str = "⚠️  DUE TOMORROW!"
        elif days_left <= 3:
            days_str = f"⚠️  {days_left} days left"
        else:
            days_str = f"{days_left} days left"

        print(f"\n{dl['date'].strftime('%d %b')}: {dl['name']}")
        print(f"  {get_course_display_name(dl['code'])}")
        print(f"  {days_str}")


def update_status(course_input: str, assessment_key: str, new_status: str) -> None:
    """Update assessment status with validation."""
    # Validate inputs
    course_code = resolve_course_code(course_input)
    new_status = validate_status(new_status)

    data = load_tracker()

    if course_code not in data["courses"]:
        raise ValidationError(f"Course {course_code} not in tracker")

    course = data["courses"][course_code]
    assessment_key = validate_assessment_key(
        course_code, assessment_key, course["assessments"]
    )

    old_status = course["assessments"][assessment_key].get("status", "not_started")
    course["assessments"][assessment_key]["status"] = new_status

    save_tracker(data)

    print(f"✓ Updated: {COURSE_NAMES[course_code]} / {assessment_key}")
    print(f"  {old_status} → {new_status}")


def record_score(course_input: str, assessment_key: str, score: str) -> None:
    """Record a score for an assessment."""
    course_code = resolve_course_code(course_input)

    data = load_tracker()

    if course_code not in data["courses"]:
        raise ValidationError(f"Course {course_code} not in tracker")

    course = data["courses"][course_code]
    assessment_key = validate_assessment_key(
        course_code, assessment_key, course["assessments"]
    )

    course["assessments"][assessment_key]["score"] = score
    course["assessments"][assessment_key]["status"] = "completed"

    save_tracker(data)

    print(f"✓ Recorded score: {COURSE_NAMES[course_code]} / {assessment_key}")
    print(f"  Score: {score}")


def log_hours(hours_input: str) -> None:
    """Log study hours for current week."""
    hours = validate_hours(hours_input)

    data = load_tracker()

    today = datetime.now()
    week_num = today.strftime("%Y-W%W")
    week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")

    if "weekly_log" not in data:
        data["weekly_log"] = {}

    if week_num not in data["weekly_log"]:
        data["weekly_log"][week_num] = {
            "week_of": week_start,
            "study_hours": 0,
            "completed_tasks": [],
            "notes": "",
        }

    data["weekly_log"][week_num]["study_hours"] += hours
    total = data["weekly_log"][week_num]["study_hours"]

    save_tracker(data)

    print(f"✓ Logged {hours} hours")
    print(f"  Total this week: {total} hours")


def set_partner(partner_name: str) -> None:
    """Set CV&PR coursework partner."""
    data = load_tracker()
    course_code = "ELEC70073"

    if course_code not in data["courses"]:
        raise ValidationError("CV&PR course not found in tracker")

    for key in ["pr_coursework", "cv_coursework"]:
        if key in data["courses"][course_code]["assessments"]:
            data["courses"][course_code]["assessments"][key]["partner"] = partner_name

    save_tracker(data)
    print(f"✓ Set CV&PR coursework partner: {partner_name}")


def set_paper(title: str) -> None:
    """Set Distributed Optimisation paper study topic."""
    data = load_tracker()
    course_code = "ELEC70082"

    if course_code not in data["courses"]:
        raise ValidationError("Distributed Optimisation course not found in tracker")

    data["courses"][course_code]["assessments"]["paper_study"]["paper_chosen"] = title

    save_tracker(data)
    print(f"✓ Set paper study topic: {title}")
