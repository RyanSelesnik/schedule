"""
UI utilities for the study tracker CLI.

Provides:
- ANSI color support with automatic detection
- Confirmation prompts
- Consistent formatting helpers
- Progress bars and summaries
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional, List, Tuple


# ============================================================================
# Color Support
# ============================================================================


def _supports_color() -> bool:
    """Check if the terminal supports color output."""
    # Respect NO_COLOR environment variable (https://no-color.org/)
    if os.environ.get("NO_COLOR"):
        return False

    # Check FORCE_COLOR
    if os.environ.get("FORCE_COLOR"):
        return True

    # Check if stdout is a TTY
    if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
        return False

    # Check TERM
    term = os.environ.get("TERM", "")
    if term == "dumb":
        return False

    return True


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""

    _enabled = _supports_color()

    # Reset
    RESET = "\033[0m" if _enabled else ""

    # Regular colors
    RED = "\033[31m" if _enabled else ""
    GREEN = "\033[32m" if _enabled else ""
    YELLOW = "\033[33m" if _enabled else ""
    BLUE = "\033[34m" if _enabled else ""
    MAGENTA = "\033[35m" if _enabled else ""
    CYAN = "\033[36m" if _enabled else ""
    WHITE = "\033[37m" if _enabled else ""
    GRAY = "\033[90m" if _enabled else ""

    # Bold colors
    BOLD = "\033[1m" if _enabled else ""
    BOLD_RED = "\033[1;31m" if _enabled else ""
    BOLD_GREEN = "\033[1;32m" if _enabled else ""
    BOLD_YELLOW = "\033[1;33m" if _enabled else ""
    BOLD_BLUE = "\033[1;34m" if _enabled else ""
    BOLD_CYAN = "\033[1;36m" if _enabled else ""

    # Dim
    DIM = "\033[2m" if _enabled else ""

    @classmethod
    def disable(cls):
        """Disable all colors."""
        cls._enabled = False
        for attr in dir(cls):
            if attr.isupper() and not attr.startswith("_"):
                setattr(cls, attr, "")

    @classmethod
    def enable(cls):
        """Re-enable colors if terminal supports them."""
        if _supports_color():
            cls._enabled = True
            # Re-initialize colors
            cls.RESET = "\033[0m"
            cls.RED = "\033[31m"
            cls.GREEN = "\033[32m"
            cls.YELLOW = "\033[33m"
            cls.BLUE = "\033[34m"
            cls.MAGENTA = "\033[35m"
            cls.CYAN = "\033[36m"
            cls.WHITE = "\033[37m"
            cls.GRAY = "\033[90m"
            cls.BOLD = "\033[1m"
            cls.BOLD_RED = "\033[1;31m"
            cls.BOLD_GREEN = "\033[1;32m"
            cls.BOLD_YELLOW = "\033[1;33m"
            cls.BOLD_BLUE = "\033[1;34m"
            cls.BOLD_CYAN = "\033[1;36m"
            cls.DIM = "\033[2m"


# Convenience functions
def red(text: str) -> str:
    return f"{Colors.RED}{text}{Colors.RESET}"


def green(text: str) -> str:
    return f"{Colors.GREEN}{text}{Colors.RESET}"


def yellow(text: str) -> str:
    return f"{Colors.YELLOW}{text}{Colors.RESET}"


def blue(text: str) -> str:
    return f"{Colors.BLUE}{text}{Colors.RESET}"


def cyan(text: str) -> str:
    return f"{Colors.CYAN}{text}{Colors.RESET}"


def gray(text: str) -> str:
    return f"{Colors.GRAY}{text}{Colors.RESET}"


def bold(text: str) -> str:
    return f"{Colors.BOLD}{text}{Colors.RESET}"


def dim(text: str) -> str:
    return f"{Colors.DIM}{text}{Colors.RESET}"


def bold_red(text: str) -> str:
    return f"{Colors.BOLD_RED}{text}{Colors.RESET}"


def bold_green(text: str) -> str:
    return f"{Colors.BOLD_GREEN}{text}{Colors.RESET}"


def bold_yellow(text: str) -> str:
    return f"{Colors.BOLD_YELLOW}{text}{Colors.RESET}"


def bold_blue(text: str) -> str:
    return f"{Colors.BOLD_BLUE}{text}{Colors.RESET}"


# ============================================================================
# Status Formatting
# ============================================================================


def format_status(status: str, with_emoji: bool = True) -> str:
    """Format a status string with color and optional emoji."""
    status_config = {
        "not_started": ("⬜", "", "Not started"),
        "in_progress": ("🔄", Colors.YELLOW, "In progress"),
        "completed": ("✅", Colors.GREEN, "Completed"),
        "submitted": ("📤", Colors.GREEN, "Submitted"),
        "overdue": ("🔴", Colors.RED, "OVERDUE"),
        "ongoing": ("🔁", Colors.CYAN, "Ongoing"),
    }

    emoji, color, label = status_config.get(status, ("❓", "", status))

    if with_emoji:
        return f"{emoji} {color}{label}{Colors.RESET}" if color else f"{emoji} {label}"
    else:
        return f"{color}{label}{Colors.RESET}" if color else label


def format_status_emoji(status: str) -> str:
    """Get just the emoji for a status."""
    emojis = {
        "not_started": "⬜",
        "in_progress": "🔄",
        "completed": "✅",
        "submitted": "📤",
        "overdue": "🔴",
        "ongoing": "🔁",
    }
    return emojis.get(status, "❓")


def format_days_remaining(days: int, short: bool = False) -> str:
    """Format days remaining with appropriate urgency coloring."""
    if days < 0:
        text = f"OVERDUE by {-days}d" if short else f"OVERDUE by {-days} days!"
        return bold_red(text)
    elif days == 0:
        text = "TODAY!" if short else "DUE TODAY!"
        return bold_red(text)
    elif days == 1:
        text = "TOMORROW" if short else "DUE TOMORROW!"
        return bold_yellow(text)
    elif days <= 3:
        text = f"{days}d left" if short else f"{days} days left"
        return yellow(text)
    elif days <= 7:
        text = f"{days}d left" if short else f"{days} days left"
        return cyan(text)
    else:
        text = f"{days}d" if short else f"{days} days"
        return text


def format_date(dt: datetime, style: str = "short") -> str:
    """
    Format a date consistently.

    Styles:
        'short': '30 Jan'
        'medium': 'Jan 30, 2026'
        'long': 'Thursday, January 30, 2026'
        'iso': '2026-01-30'
    """
    if style == "short":
        return dt.strftime("%d %b")
    elif style == "medium":
        return dt.strftime("%b %d, %Y")
    elif style == "long":
        return dt.strftime("%A, %B %d, %Y")
    elif style == "iso":
        return dt.strftime("%Y-%m-%d")
    else:
        return dt.strftime("%d %b")


# ============================================================================
# Progress Display
# ============================================================================


def format_progress_bar(completed: int, total: int, width: int = 20) -> str:
    """Create a text-based progress bar."""
    if total == 0:
        return f"[{'─' * width}] 0%"

    pct = completed / total
    filled = int(width * pct)
    empty = width - filled

    bar = f"[{green('█' * filled)}{'─' * empty}]"
    pct_str = f"{int(pct * 100)}%"

    return f"{bar} {pct_str}"


def format_progress_summary(completed: int, total: int) -> str:
    """Format a progress summary like '4/19 complete (21%)'."""
    if total == 0:
        return "No assessments"

    pct = int((completed / total) * 100)

    if pct == 100:
        return bold_green(f"{completed}/{total} complete (100%)")
    elif pct >= 75:
        return green(f"{completed}/{total} complete ({pct}%)")
    elif pct >= 50:
        return cyan(f"{completed}/{total} complete ({pct}%)")
    elif pct >= 25:
        return yellow(f"{completed}/{total} complete ({pct}%)")
    else:
        return f"{completed}/{total} complete ({pct}%)"


# ============================================================================
# Confirmation Prompts
# ============================================================================


def confirm(message: str, default: bool = False, skip_confirm: bool = False) -> bool:
    """
    Ask for user confirmation.

    Args:
        message: The question to ask
        default: Default answer if user just presses Enter
        skip_confirm: If True, return True without asking (for --yes flag)

    Returns:
        True if user confirms, False otherwise
    """
    if skip_confirm:
        return True

    if default:
        prompt = f"{message} [{bold('Y')}/n]: "
    else:
        prompt = f"{message} [y/{bold('N')}]: "

    try:
        response = input(prompt).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()  # New line after ^C
        return False

    if not response:
        return default

    return response in ("y", "yes", "true", "1")


def prompt_choice(
    message: str,
    choices: List[str],
    default: Optional[str] = None,
    allow_skip: bool = False,
) -> Optional[str]:
    """
    Prompt user to choose from a list of options.

    Args:
        message: The question to ask
        choices: List of valid choices
        default: Default choice if user just presses Enter
        allow_skip: If True, allow empty response to skip

    Returns:
        Selected choice, or None if skipped
    """
    choices_lower = [c.lower() for c in choices]

    if default:
        prompt = f"{message} [{'/'.join(choices)}] (default: {default}): "
    elif allow_skip:
        prompt = f"{message} [{'/'.join(choices)} or Enter to skip]: "
    else:
        prompt = f"{message} [{'/'.join(choices)}]: "

    try:
        response = input(prompt).strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return None

    if not response:
        if default:
            return default
        if allow_skip:
            return None
        # Re-prompt
        print(f"  Please choose: {', '.join(choices)}")
        return prompt_choice(message, choices, default, allow_skip)

    response_lower = response.lower()

    # Exact match
    if response_lower in choices_lower:
        idx = choices_lower.index(response_lower)
        return choices[idx]

    # Partial match
    matches = [c for c in choices if c.lower().startswith(response_lower)]
    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        print(f"  Ambiguous: {', '.join(matches)}")
        return prompt_choice(message, choices, default, allow_skip)

    print(f"  Invalid choice. Options: {', '.join(choices)}")
    return prompt_choice(message, choices, default, allow_skip)


# ============================================================================
# Output Helpers
# ============================================================================


def print_header(title: str, width: int = 60):
    """Print a formatted header."""
    print()
    print(bold("=" * width))
    print(bold(title.center(width)))
    print(bold("=" * width))


def print_subheader(title: str, width: int = 50):
    """Print a formatted subheader."""
    print()
    print(bold(title))
    print("-" * width)


def print_success(message: str):
    """Print a success message."""
    print(f"{green('✓')} {message}")


def print_error(message: str, hint: Optional[str] = None):
    """Print an error message."""
    print(f"\n{red('✗')} {message}")
    if hint:
        print(f"  {dim('Hint:')} {hint}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"{yellow('⚠')} {message}")


def print_info(message: str):
    """Print an info message."""
    print(f"{cyan('ℹ')} {message}")


# ============================================================================
# Table Formatting
# ============================================================================


def print_table(
    headers: List[str], rows: List[List[str]], alignments: Optional[List[str]] = None
):
    """
    Print a formatted table.

    Args:
        headers: Column headers
        rows: List of rows (each row is a list of cell values)
        alignments: List of 'l', 'r', or 'c' for each column
    """
    if not rows:
        return

    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            # Strip ANSI codes for width calculation
            clean = cell
            for code in [
                Colors.RED,
                Colors.GREEN,
                Colors.YELLOW,
                Colors.BLUE,
                Colors.CYAN,
                Colors.GRAY,
                Colors.BOLD,
                Colors.DIM,
                Colors.RESET,
                Colors.BOLD_RED,
                Colors.BOLD_GREEN,
                Colors.BOLD_YELLOW,
                Colors.BOLD_BLUE,
                Colors.BOLD_CYAN,
                Colors.MAGENTA,
                Colors.WHITE,
            ]:
                clean = clean.replace(code, "")
            if i < len(widths):
                widths[i] = max(widths[i], len(clean))

    if alignments is None:
        alignments = ["l"] * len(headers)

    def format_cell(text: str, width: int, align: str) -> str:
        # Strip ANSI for padding calculation
        clean = text
        for code in [
            Colors.RED,
            Colors.GREEN,
            Colors.YELLOW,
            Colors.BLUE,
            Colors.CYAN,
            Colors.GRAY,
            Colors.BOLD,
            Colors.DIM,
            Colors.RESET,
            Colors.BOLD_RED,
            Colors.BOLD_GREEN,
            Colors.BOLD_YELLOW,
            Colors.BOLD_BLUE,
            Colors.BOLD_CYAN,
            Colors.MAGENTA,
            Colors.WHITE,
        ]:
            clean = clean.replace(code, "")

        padding = width - len(clean)
        if align == "r":
            return " " * padding + text
        elif align == "c":
            left = padding // 2
            right = padding - left
            return " " * left + text + " " * right
        else:
            return text + " " * padding

    # Print header
    header_line = " | ".join(
        format_cell(bold(h), widths[i], alignments[i]) for i, h in enumerate(headers)
    )
    print(header_line)
    print("-" * (sum(widths) + 3 * (len(widths) - 1)))

    # Print rows
    for row in rows:
        row_line = " | ".join(
            format_cell(cell, widths[i], alignments[i]) for i, cell in enumerate(row)
        )
        print(row_line)
