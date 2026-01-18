"""
Data validation for study tracker.

Provides:
- Input validation with helpful error messages
- Course code resolution (aliases to full codes)
- Status normalization with common aliases
"""

from typing import Tuple, List, Optional

from .config import VALID_STATUSES, ALIAS_TO_CODE, COURSE_NAMES
from .errors import ValidationError


def resolve_course_code(code: str) -> str:
    """
    Convert short alias or full code to canonical course code.

    Args:
        code: Short alias (pc, do, cv, ao) or full code (ELEC70028)

    Returns:
        Canonical course code (e.g., ELEC70028)

    Raises:
        ValidationError: If code is not recognized
    """
    if not code or not isinstance(code, str):
        raise ValidationError(
            "Course code is required",
            field="course",
            valid_options=list(ALIAS_TO_CODE.keys()),
        )

    code_lower = code.lower().strip()
    if code_lower in ALIAS_TO_CODE:
        return ALIAS_TO_CODE[code_lower]

    code_upper = code.upper().strip()
    if code_upper in COURSE_NAMES:
        return code_upper

    valid_options = sorted(set(list(ALIAS_TO_CODE.keys()) + list(COURSE_NAMES.keys())))
    raise ValidationError(
        f"Unknown course: '{code}'", field="course", valid_options=valid_options
    )


def validate_status(status: str) -> str:
    """
    Validate and normalize status string.

    Args:
        status: Status string to validate

    Returns:
        Normalized status string

    Raises:
        ValidationError: If status is not valid
    """
    if not status or not isinstance(status, str):
        raise ValidationError(
            "Status is required", field="status", valid_options=list(VALID_STATUSES)
        )

    status_lower = status.lower().strip()

    # Common aliases - be generous with what we accept
    aliases = {
        "done": "completed",
        "finish": "completed",
        "finished": "completed",
        "complete": "completed",
        "submit": "submitted",
        "sent": "submitted",
        "turned_in": "submitted",
        "started": "in_progress",
        "working": "in_progress",
        "wip": "in_progress",
        "inprogress": "in_progress",
        "in-progress": "in_progress",
        "todo": "not_started",
        "pending": "not_started",
        "notstarted": "not_started",
        "not-started": "not_started",
        "late": "overdue",
        "missed": "overdue",
    }

    if status_lower in aliases:
        return aliases[status_lower]

    if status_lower in VALID_STATUSES:
        return status_lower

    raise ValidationError(
        f"Invalid status: '{status}'",
        field="status",
        valid_options=list(VALID_STATUSES) + ["done", "wip", "todo"],
    )


def validate_assessment_key(
    course_code: str, assessment_key: str, assessments: dict
) -> str:
    """
    Validate assessment key exists for a course.

    Args:
        course_code: The course code
        assessment_key: The assessment key to validate
        assessments: Dict of assessments for the course

    Returns:
        Validated assessment key

    Raises:
        ValidationError: If assessment key doesn't exist
    """
    if not assessment_key or not isinstance(assessment_key, str):
        raise ValidationError(
            "Assessment key is required",
            field="assessment",
            valid_options=list(assessments.keys()),
        )

    key_lower = assessment_key.lower().strip()

    # Try exact match first
    if key_lower in assessments:
        return key_lower

    # Try case-insensitive match
    for k in assessments.keys():
        if k.lower() == key_lower:
            return k

    # Try partial match
    matches = [k for k in assessments.keys() if key_lower in k.lower()]

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        raise ValidationError(
            f"Ambiguous assessment key: '{assessment_key}'. Did you mean one of: {', '.join(matches)}?",
            field="assessment",
            valid_options=matches,
        )

    # No matches found
    course_name = COURSE_NAMES.get(course_code, course_code)
    raise ValidationError(
        f"Unknown assessment: '{assessment_key}' for {course_name}",
        field="assessment",
        valid_options=list(assessments.keys()),
    )


def validate_hours(hours: str) -> float:
    """
    Validate and parse hours input.

    Args:
        hours: Hours string to validate

    Returns:
        Hours as float

    Raises:
        ValidationError: If hours is not a valid number
    """
    if not hours:
        raise ValidationError("Hours value is required", field="hours")

    # Handle string input
    hours_str = str(hours).strip()

    try:
        h = float(hours_str)
    except ValueError:
        raise ValidationError(
            f"Invalid hours: '{hours}'. Must be a number (e.g., 2.5)", field="hours"
        )

    if h < 0:
        raise ValidationError("Hours cannot be negative", field="hours")

    if h > 24:
        raise ValidationError(
            f"Hours ({h}) seems too high for a single session. Maximum is 24.",
            field="hours",
        )

    # Warn about unusually high values but don't block
    if h > 12:
        print(f"Note: Logging {h} hours - that's a long session!")

    return h


def validate_score(score: str) -> str:
    """
    Validate a score input.

    Args:
        score: Score string to validate

    Returns:
        Validated score string

    Raises:
        ValidationError: If score is invalid
    """
    if not score or not isinstance(score, str):
        raise ValidationError("Score is required", field="score")

    score = score.strip()

    if not score:
        raise ValidationError("Score cannot be empty", field="score")

    # Accept common score formats
    # - Percentages: 85%, 85.5%
    # - Fractions: 17/20
    # - Letter grades: A, B+, etc.
    # - Pass/Fail: pass, fail
    # - Raw numbers: 85, 85.5

    return score


def validate_tracker_data(data: dict) -> Tuple[bool, List[str]]:
    """
    Validate entire tracker data structure.

    Args:
        data: Tracker data dict

    Returns:
        Tuple of (is_valid, list of errors)
    """
    errors = []

    if not isinstance(data, dict):
        errors.append("Tracker data must be a dictionary")
        return False, errors

    if "courses" not in data:
        errors.append("Missing 'courses' key in tracker data")
        return False, errors

    if not isinstance(data["courses"], dict):
        errors.append("'courses' must be a dictionary")
        return False, errors

    for code, course in data["courses"].items():
        if code not in COURSE_NAMES:
            errors.append(f"Unknown course code: {code}")

        if not isinstance(course, dict):
            errors.append(f"Course {code} must be a dictionary")
            continue

        if "assessments" not in course:
            errors.append(f"Missing 'assessments' for course {code}")
            continue

        if not isinstance(course["assessments"], dict):
            errors.append(f"'assessments' for {code} must be a dictionary")
            continue

        for key, assessment in course["assessments"].items():
            if not isinstance(assessment, dict):
                errors.append(f"Assessment {code}/{key} must be a dictionary")
                continue

            status = assessment.get("status", "")
            if status and status not in VALID_STATUSES:
                errors.append(f"Invalid status '{status}' for {code}/{key}")

    return len(errors) == 0, errors
