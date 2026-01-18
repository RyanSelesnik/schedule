"""
Core tracker operations with improved UX.

Provides all the main tracker commands with:
- Color-coded output
- Progress summaries
- Undo history tracking
- Consistent date formatting
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Tuple

from .config import COURSE_NAMES, CODE_TO_ALIAS, ALIAS_TO_CODE, VALID_STATUSES
from .data import load_tracker, save_tracker, get_course_display_name
from .errors import ValidationError, DataError
from .validation import (
    resolve_course_code,
    validate_status,
    validate_assessment_key,
    validate_hours,
)
from .ui import (
    Colors,
    bold,
    green,
    yellow,
    red,
    cyan,
    gray,
    dim,
    format_status_emoji,
    format_days_remaining,
    format_date,
    format_progress_summary,
    format_progress_bar,
    print_header,
    print_subheader,
    print_success,
    print_warning,
    print_error,
)
from . import history


def _get_all_assessments(data: dict) -> List[Tuple[str, str, dict]]:
    """Get all assessments as (course_code, key, assessment) tuples."""
    assessments = []
    for code, course in data["courses"].items():
        for key, assessment in course["assessments"].items():
            assessments.append((code, key, assessment))
    return assessments


def _get_progress_stats(data: dict) -> Tuple[int, int]:
    """Get (completed, total) counts for all assessments."""
    total = 0
    completed = 0

    for code, course in data["courses"].items():
        for key, assessment in course["assessments"].items():
            status = assessment.get("status", "not_started")
            # Don't count ongoing items in total
            if status != "ongoing":
                total += 1
                if status in ("completed", "submitted"):
                    completed += 1

    return completed, total


def _get_next_deadline(data: dict) -> Optional[Tuple[datetime, str]]:
    """Get the next upcoming deadline as (date, name) or None."""
    today = datetime.now()
    next_dl = None

    for code, course in data["courses"].items():
        for key, assessment in course["assessments"].items():
            status = assessment.get("status", "")
            deadline = assessment.get("deadline", "")

            if status in ("completed", "submitted"):
                continue
            if not deadline or deadline in ("TBD", "ongoing"):
                continue

            try:
                if " to " in deadline:
                    deadline = deadline.split(" to ")[0]
                dl_date = datetime.strptime(deadline, "%Y-%m-%d")

                if dl_date >= today:
                    if next_dl is None or dl_date < next_dl[0]:
                        next_dl = (dl_date, assessment["name"])
            except ValueError:
                continue

    return next_dl


def _build_assessment_index(data: dict) -> Dict[str, List[Tuple[str, str]]]:
    """
    Build an index for numbered assessment shortcuts.

    Returns dict mapping course_code to list of (key, name) in order.
    """
    index = {}
    for code, course in data["courses"].items():
        index[code] = []
        for key, assessment in course["assessments"].items():
            index[code].append((key, assessment.get("name", key)))
    return index


def resolve_assessment_shortcut(
    course_code: str, shortcut: str, assessments: dict
) -> str:
    """
    Resolve a numbered shortcut (like '1', '2') to an assessment key.

    Args:
        course_code: The course code
        shortcut: Either a number ('1') or partial key name
        assessments: Dict of assessments

    Returns:
        The resolved assessment key
    """
    # Try as a number first
    if shortcut.isdigit():
        idx = int(shortcut) - 1  # 1-indexed for users
        keys = list(assessments.keys())
        if 0 <= idx < len(keys):
            return keys[idx]
        raise ValidationError(
            f"Assessment #{shortcut} out of range (1-{len(keys)})",
            field="assessment",
            valid_options=[f"{i + 1}: {k}" for i, k in enumerate(keys)],
        )

    # Fall back to normal validation
    return validate_assessment_key(course_code, shortcut, assessments)


def show_status() -> None:
    """Display all assessment statuses with progress summary."""
    data = load_tracker()

    # Calculate overall progress
    completed, total = _get_progress_stats(data)
    next_dl = _get_next_deadline(data)

    # Header with progress
    print_header("STUDY TRACKER")

    # Overall summary line
    progress = format_progress_summary(completed, total)
    if next_dl:
        days = (next_dl[0] - datetime.now()).days
        next_str = f"Next: {format_days_remaining(days, short=True)}"
        print(f"\n{progress}  |  {next_str}")
    else:
        print(f"\n{progress}")

    print(dim(f"Last updated: {data.get('last_updated', 'Unknown')}"))

    # Each course
    for code, course in data["courses"].items():
        alias = CODE_TO_ALIAS.get(code, "??")
        name = COURSE_NAMES.get(code, code)

        # Course progress
        course_completed = sum(
            1
            for a in course["assessments"].values()
            if a.get("status") in ("completed", "submitted")
        )
        course_total = sum(
            1 for a in course["assessments"].values() if a.get("status") != "ongoing"
        )

        print_subheader(f"[{alias}] {name}")

        # Numbered list of assessments
        for i, (key, assessment) in enumerate(course["assessments"].items(), 1):
            status = assessment.get("status", "not_started")
            deadline = assessment.get("deadline", "TBD")
            weight = assessment.get("weight", "")
            score = assessment.get("score")

            emoji = format_status_emoji(status)

            # Format deadline with urgency
            if deadline not in ("TBD", "ongoing", ""):
                try:
                    dl_str = (
                        deadline.split(" to ")[0] if " to " in deadline else deadline
                    )
                    dl_date = datetime.strptime(dl_str, "%Y-%m-%d")
                    days = (dl_date - datetime.now()).days

                    if status not in ("completed", "submitted"):
                        date_display = format_date(dl_date, "short")
                        if days < 0:
                            deadline_str = red(f"{date_display} (OVERDUE)")
                        elif days <= 3:
                            deadline_str = yellow(f"{date_display} ({days}d)")
                        elif days <= 7:
                            deadline_str = cyan(f"{date_display} ({days}d)")
                        else:
                            deadline_str = f"{date_display}"
                    else:
                        deadline_str = dim(format_date(dl_date, "short"))
                except ValueError:
                    deadline_str = deadline
            else:
                deadline_str = dim(deadline)

            # Build the line
            num_str = dim(f"{i}.")
            score_str = f" {green('[' + score + ']')}" if score else ""
            weight_str = dim(f" ({weight})") if weight else ""
            name_str = assessment["name"]

            # Dim completed items
            if status in ("completed", "submitted"):
                name_str = dim(name_str)

            print(
                f"  {num_str} {emoji} {name_str}{weight_str}: {deadline_str}{score_str}"
            )

        # Course progress bar
        if course_total > 0:
            print(
                f"      {format_progress_bar(course_completed, course_total, width=15)}"
            )


def show_courses() -> None:
    """Show course codes and assessment keys (simplified)."""
    data = load_tracker()

    print_header("QUICK REFERENCE")

    # Course codes
    print(f"\n{bold('Course Codes:')}")
    for alias, code in sorted(ALIAS_TO_CODE.items(), key=lambda x: x[1]):
        print(f"  {bold(alias):6} {COURSE_NAMES[code]}")

    # Assessments by course with numbers
    for code, course in data["courses"].items():
        alias = CODE_TO_ALIAS.get(code, "??")
        print_subheader(f"[{alias}] Assessments")

        for i, (key, assessment) in enumerate(course["assessments"].items(), 1):
            status = assessment.get("status", "not_started")
            emoji = format_status_emoji(status)

            # Show both number and key
            num = dim(f"{i}.")
            key_display = cyan(key)

            print(f"  {num} {emoji} {key_display:22} {assessment['name']}")

    print(f"\n{dim('Tip: Use numbers as shortcuts, e.g., study u pc 2 done')}")


def show_next_deadlines(count: Optional[int] = None, weeks: int = 2) -> None:
    """
    Show upcoming deadlines.

    Args:
        count: Max number to show (None = show all within timeframe)
        weeks: Show deadlines within this many weeks (default 2)
    """
    data = load_tracker()
    deadlines = []
    today = datetime.now()
    cutoff = today + timedelta(weeks=weeks) if count is None else None

    for code, course in data["courses"].items():
        for key, assessment in course["assessments"].items():
            deadline = assessment.get("deadline", "")
            status = assessment.get("status", "")

            if status in ("completed", "submitted"):
                continue
            if not deadline or deadline in ("TBD", "ongoing"):
                continue

            try:
                if " to " in deadline:
                    deadline = deadline.split(" to ")[0]
                deadline_date = datetime.strptime(deadline, "%Y-%m-%d")

                # Filter by cutoff if no count specified
                if cutoff and deadline_date > cutoff:
                    continue

                deadlines.append(
                    {
                        "date": deadline_date,
                        "code": code,
                        "key": key,
                        "name": assessment["name"],
                        "status": status,
                        "weight": assessment.get("weight", ""),
                    }
                )
            except ValueError:
                pass

    deadlines.sort(key=lambda x: x["date"])

    # Apply count limit
    if count:
        deadlines = deadlines[:count]

    print_header("UPCOMING DEADLINES")

    if not deadlines:
        print(f"\n{green('No upcoming deadlines!')} 🎉")
        return

    # Group by urgency
    overdue = []
    this_week = []
    next_week = []
    later = []

    week_start = today - timedelta(days=today.weekday())
    next_week_start = week_start + timedelta(weeks=1)
    week_after_start = week_start + timedelta(weeks=2)

    for dl in deadlines:
        days = (dl["date"] - today).days
        if days < 0:
            overdue.append(dl)
        elif dl["date"] < next_week_start:
            this_week.append(dl)
        elif dl["date"] < week_after_start:
            next_week.append(dl)
        else:
            later.append(dl)

    def print_deadline(dl):
        days = (dl["date"] - today).days
        alias = CODE_TO_ALIAS.get(dl["code"], "??")

        date_str = format_date(dl["date"], "short")
        days_str = format_days_remaining(days, short=True)
        weight_str = dim(f" ({dl['weight']})") if dl["weight"] else ""

        print(f"  {date_str:8} {bold(dl['name'])}{weight_str}")
        print(f"           [{alias}] {days_str}")

    if overdue:
        print(f"\n{bold_red('⚠ OVERDUE:')}")
        for dl in overdue:
            print_deadline(dl)

    if this_week:
        print(f"\n{bold_yellow('This Week:')}")
        for dl in this_week:
            print_deadline(dl)

    if next_week:
        print(f"\n{bold('Next Week:')}")
        for dl in next_week:
            print_deadline(dl)

    if later:
        print(f"\n{dim('Later:')}")
        for dl in later:
            print_deadline(dl)


def update_status(course_input: str, assessment_input: str, new_status: str) -> None:
    """Update assessment status with validation and history tracking."""
    course_code = resolve_course_code(course_input)
    new_status = validate_status(new_status)

    data = load_tracker()

    if course_code not in data["courses"]:
        raise ValidationError(f"Course {course_code} not in tracker", field="course")

    course = data["courses"][course_code]

    # Support numbered shortcuts
    assessment_key = resolve_assessment_shortcut(
        course_code, assessment_input, course["assessments"]
    )

    old_status = course["assessments"][assessment_key].get("status", "not_started")

    # Don't update if same
    if old_status == new_status:
        print_warning(f"Status already '{new_status}'")
        return

    course["assessments"][assessment_key]["status"] = new_status

    # Record in history for undo
    history.record_change(
        action="update_status",
        course_code=course_code,
        assessment_key=assessment_key,
        field="status",
        old_value=old_status,
        new_value=new_status,
        description=f"[{CODE_TO_ALIAS.get(course_code, '??')}] {assessment_key}: {old_status} → {new_status}",
    )

    save_tracker(data)

    alias = CODE_TO_ALIAS.get(course_code, "??")
    assessment_name = course["assessments"][assessment_key]["name"]

    print_success(f"[{alias}] {assessment_name}")

    old_emoji = format_status_emoji(old_status)
    new_emoji = format_status_emoji(new_status)
    print(f"  {old_emoji} {dim(old_status)} → {new_emoji} {bold(new_status)}")


def record_score(course_input: str, assessment_input: str, score: str) -> None:
    """Record a score for an assessment."""
    course_code = resolve_course_code(course_input)

    data = load_tracker()

    if course_code not in data["courses"]:
        raise ValidationError(f"Course {course_code} not in tracker")

    course = data["courses"][course_code]
    assessment_key = resolve_assessment_shortcut(
        course_code, assessment_input, course["assessments"]
    )

    old_score = course["assessments"][assessment_key].get("score")
    old_status = course["assessments"][assessment_key].get("status", "not_started")

    course["assessments"][assessment_key]["score"] = score
    course["assessments"][assessment_key]["status"] = "completed"

    # Record in history
    history.record_change(
        action="record_score",
        course_code=course_code,
        assessment_key=assessment_key,
        field="score",
        old_value=old_score,
        new_value=score,
    )

    save_tracker(data)

    alias = CODE_TO_ALIAS.get(course_code, "??")
    assessment_name = course["assessments"][assessment_key]["name"]

    print_success(f"[{alias}] {assessment_name}")
    print(f"  Score: {green(score)}")


def log_hours(hours_input: str, course_input: Optional[str] = None) -> None:
    """
    Log study hours for current week.

    Args:
        hours_input: Hours to log
        course_input: Optional course to attribute hours to
    """
    hours = validate_hours(hours_input)

    course_code = None
    if course_input:
        course_code = resolve_course_code(course_input)

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
            "hours_by_course": {},
            "completed_tasks": [],
            "notes": "",
        }

    week_log = data["weekly_log"][week_num]
    old_total = week_log["study_hours"]
    week_log["study_hours"] += hours
    new_total = week_log["study_hours"]

    # Track by course if specified
    if course_code:
        if "hours_by_course" not in week_log:
            week_log["hours_by_course"] = {}

        course_hours = week_log["hours_by_course"].get(course_code, 0)
        week_log["hours_by_course"][course_code] = course_hours + hours

    # Record in history
    history.record_hours_change(
        week_num=week_num,
        old_hours=old_total,
        new_hours=new_total,
        added_hours=hours,
        course_code=course_code,
    )

    save_tracker(data)

    # Output
    if course_code:
        alias = CODE_TO_ALIAS.get(course_code, "??")
        print_success(f"Logged {bold(str(hours))}h for [{alias}]")
    else:
        print_success(f"Logged {bold(str(hours))}h")

    print(f"  This week: {bold(str(new_total))}h total")

    # Show breakdown if there's course-specific hours
    if week_log.get("hours_by_course"):
        print(f"\n  {dim('Breakdown:')}")
        for c, h in week_log["hours_by_course"].items():
            alias = CODE_TO_ALIAS.get(c, "??")
            print(f"    [{alias}] {h}h")


def show_weekly_summary() -> None:
    """Show summary for current week."""
    data = load_tracker()
    today = datetime.now()
    week_num = today.strftime("%Y-W%W")

    print_header("WEEKLY SUMMARY")

    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)
    print(f"\n{format_date(week_start, 'short')} - {format_date(week_end, 'short')}")

    # Hours logged
    week_log = data.get("weekly_log", {}).get(week_num, {})
    hours = week_log.get("study_hours", 0)

    print(f"\n{bold('Study Hours:')}")
    print(f"  {bold(str(hours))}h logged this week")

    if week_log.get("hours_by_course"):
        for c, h in week_log["hours_by_course"].items():
            alias = CODE_TO_ALIAS.get(c, "??")
            name = COURSE_NAMES.get(c, c)
            print(f"    [{alias}] {h}h - {name}")

    # Deadlines this week
    print(f"\n{bold('Deadlines This Week:')}")

    deadlines_this_week = []
    for code, course in data["courses"].items():
        for key, assessment in course["assessments"].items():
            deadline = assessment.get("deadline", "")
            status = assessment.get("status", "")

            if status in ("completed", "submitted"):
                continue
            if not deadline or deadline in ("TBD", "ongoing"):
                continue

            try:
                dl_str = deadline.split(" to ")[0] if " to " in deadline else deadline
                dl_date = datetime.strptime(dl_str, "%Y-%m-%d")

                if week_start <= dl_date <= week_end:
                    deadlines_this_week.append(
                        {
                            "date": dl_date,
                            "code": code,
                            "name": assessment["name"],
                            "status": status,
                        }
                    )
            except ValueError:
                continue

    if deadlines_this_week:
        for dl in sorted(deadlines_this_week, key=lambda x: x["date"]):
            alias = CODE_TO_ALIAS.get(dl["code"], "??")
            date_str = format_date(dl["date"], "short")
            days = (dl["date"] - today).days
            days_str = format_days_remaining(days, short=True)
            print(f"  {date_str}: [{alias}] {dl['name']} - {days_str}")
    else:
        print(f"  {green('No deadlines this week!')}")

    # Recent activity
    print(f"\n{bold('Recent Activity:')}")
    recent = history.get_recent_changes(5)
    if recent:
        for entry in recent:
            desc = history.format_change_description(entry)
            print(f"  {dim('•')} {desc}")
    else:
        print(f"  {dim('No recent activity')}")

    # Overall progress
    completed, total = _get_progress_stats(data)
    print(f"\n{bold('Overall Progress:')}")
    print(f"  {format_progress_bar(completed, total)}")


def undo_last_change() -> bool:
    """
    Undo the last change.

    Returns:
        True if undo was successful, False otherwise
    """
    last = history.get_last_change()

    if not last:
        print_warning("Nothing to undo")
        return False

    data = load_tracker()
    action = last.get("action")

    try:
        if action == "update_status":
            course_code = last["course_code"]
            assessment_key = last["assessment_key"]
            old_value = last["old_value"]

            if course_code in data["courses"]:
                if assessment_key in data["courses"][course_code]["assessments"]:
                    data["courses"][course_code]["assessments"][assessment_key][
                        "status"
                    ] = old_value
                    save_tracker(data, create_backup=False)  # Don't backup for undo
                    history.pop_last_change()

                    alias = CODE_TO_ALIAS.get(course_code, "??")
                    print_success(f"Reverted [{alias}] {assessment_key}")
                    print(f"  Status restored to: {old_value}")
                    return True

        elif action == "record_score":
            course_code = last["course_code"]
            assessment_key = last["assessment_key"]
            old_value = last["old_value"]

            if course_code in data["courses"]:
                if assessment_key in data["courses"][course_code]["assessments"]:
                    if old_value is None:
                        del data["courses"][course_code]["assessments"][assessment_key][
                            "score"
                        ]
                    else:
                        data["courses"][course_code]["assessments"][assessment_key][
                            "score"
                        ] = old_value
                    save_tracker(data, create_backup=False)
                    history.pop_last_change()

                    alias = CODE_TO_ALIAS.get(course_code, "??")
                    print_success(f"Reverted [{alias}] {assessment_key} score")
                    return True

        elif action == "log_hours":
            week_num = last["week_num"]
            old_hours = last["old_hours"]

            if week_num in data.get("weekly_log", {}):
                data["weekly_log"][week_num]["study_hours"] = old_hours
                save_tracker(data, create_backup=False)
                history.pop_last_change()

                print_success(f"Reverted hours for {week_num}")
                print(f"  Hours restored to: {old_hours}h")
                return True

        print_warning("Cannot undo this action")
        return False

    except Exception as e:
        print_error(f"Undo failed: {e}")
        return False


def show_history(count: int = 10) -> None:
    """Show recent change history."""
    print_header("RECENT CHANGES")

    recent = history.get_recent_changes(count)

    if not recent:
        print(f"\n{dim('No changes recorded yet')}")
        return

    print()
    for i, entry in enumerate(recent, 1):
        desc = history.format_change_description(entry)
        marker = bold("→") if i == 1 else dim("•")
        print(f"  {marker} {desc}")

    if recent:
        print(f"\n{dim('Tip: Use')} study undo {dim('to revert the last change')}")


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
    print_success(f"Set CV&PR coursework partner: {bold(partner_name)}")


def set_paper(title: str) -> None:
    """Set Distributed Optimisation paper study topic."""
    data = load_tracker()
    course_code = "ELEC70082"

    if course_code not in data["courses"]:
        raise ValidationError("Distributed Optimisation course not found in tracker")

    data["courses"][course_code]["assessments"]["paper_study"]["paper_chosen"] = title

    save_tracker(data)
    print_success(f"Set paper study topic: {bold(title)}")


# Helper for bold colors (used above)
def bold_red(text: str) -> str:
    return f"{Colors.BOLD_RED}{text}{Colors.RESET}"


def bold_yellow(text: str) -> str:
    return f"{Colors.BOLD_YELLOW}{text}{Colors.RESET}"
