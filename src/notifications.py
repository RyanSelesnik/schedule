"""
macOS notification utilities for study planner.

Uses osascript to display native macOS notifications with sound.
"""

import subprocess
from typing import Optional


def send_notification(
    title: str,
    message: str,
    subtitle: Optional[str] = None,
    sound: str = "Glass",
) -> bool:
    """
    Send a macOS notification using osascript.

    Args:
        title: Notification title
        message: Main notification body
        subtitle: Optional subtitle
        sound: Sound name (default: Glass). Set to "" for silent.

    Returns:
        True if notification was sent successfully
    """
    # Escape quotes for AppleScript
    title = title.replace('"', '\\"')
    message = message.replace('"', '\\"')

    script_parts = [f'display notification "{message}" with title "{title}"']

    if subtitle:
        subtitle = subtitle.replace('"', '\\"')
        script_parts[0] = (
            f'display notification "{message}" with title "{title}" subtitle "{subtitle}"'
        )

    if sound:
        script_parts[0] += f' sound name "{sound}"'

    script = script_parts[0]

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False


def send_study_notification(
    course_name: str,
    action: str = "start",
    duration_mins: Optional[int] = None,
    next_course: Optional[str] = None,
) -> bool:
    """
    Send a study-specific notification.

    Args:
        course_name: Name of the course
        action: "start", "end", or "switch"
        duration_mins: Duration in minutes (for start/end)
        next_course: Next course name (for switch)

    Returns:
        True if notification was sent
    """
    if action == "start":
        title = "Study Session Started"
        message = f"Starting {course_name}"
        if duration_mins:
            message += f" ({duration_mins} min)"
        subtitle = "Focus time!"
    elif action == "end":
        title = "Study Block Complete"
        message = f"Finished {course_name}"
        if duration_mins:
            message += f" ({duration_mins} min logged)"
        subtitle = "Great work!"
    elif action == "switch":
        title = "Time to Switch!"
        message = f"Finished: {course_name}"
        subtitle = f"Up next: {next_course}" if next_course else "All done!"
    else:
        title = "Study Tracker"
        message = course_name
        subtitle = None

    return send_notification(title, message, subtitle)


def play_sound(sound_name: str = "Glass") -> bool:
    """
    Play a system sound.

    Args:
        sound_name: Name of sound in /System/Library/Sounds/

    Returns:
        True if sound played
    """
    try:
        subprocess.run(
            ["afplay", f"/System/Library/Sounds/{sound_name}.aiff"],
            capture_output=True,
            timeout=5,
        )
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return False
