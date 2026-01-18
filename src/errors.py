"""
Custom exception hierarchy for the study tracker.

Exception Hierarchy:
    StudyTrackerError (base)
    ├── ValidationError - Invalid user input
    ├── DataError - Data file operations
    │   ├── DataNotFoundError - File missing
    │   ├── DataCorruptedError - JSON parse error
    │   └── DataWriteError - Save failures
    ├── CalendarError - Calendar sync issues
    │   ├── CalendarConnectionError - Can't connect to Calendar app
    │   ├── CalendarPermissionError - Permission denied
    │   └── CalendarTimeoutError - Operation timed out
    └── GitError - Git operation failures
"""

from typing import Optional, List


class StudyTrackerError(Exception):
    """Base exception for all study tracker errors."""

    def __init__(self, message: str, hint: Optional[str] = None):
        """
        Args:
            message: Error description
            hint: Optional suggestion for fixing the error
        """
        self.message = message
        self.hint = hint
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        if self.hint:
            return f"{self.message}\n  Hint: {self.hint}"
        return self.message


# ============================================================================
# Validation Errors
# ============================================================================


class ValidationError(StudyTrackerError):
    """Raised when user input validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        valid_options: Optional[List[str]] = None,
    ):
        self.field = field
        self.valid_options = valid_options

        hint = None
        if valid_options:
            hint = f"Valid options: {', '.join(valid_options[:10])}"
            if len(valid_options) > 10:
                hint += f" (and {len(valid_options) - 10} more)"

        super().__init__(message, hint)


# ============================================================================
# Data Errors
# ============================================================================


class DataError(StudyTrackerError):
    """Base class for data operation errors."""

    pass


class DataNotFoundError(DataError):
    """Raised when a required data file is missing."""

    def __init__(self, path: str, file_type: str = "file"):
        self.path = path
        super().__init__(
            f"{file_type.capitalize()} not found: {path}",
            hint="Run 'study init' to create a new tracker, or check 'study backup' for backups",
        )


class DataCorruptedError(DataError):
    """Raised when a data file cannot be parsed."""

    def __init__(self, path: str, parse_error: str):
        self.path = path
        self.parse_error = parse_error
        super().__init__(
            f"File corrupted: {path}\n  Parse error: {parse_error}",
            hint="Check 'study backup' to restore from a backup",
        )


class DataWriteError(DataError):
    """Raised when writing data fails."""

    def __init__(self, path: str, reason: str):
        self.path = path
        self.reason = reason
        super().__init__(
            f"Failed to write: {path}\n  Reason: {reason}",
            hint="Check disk space and file permissions",
        )


class DataValidationError(DataError):
    """Raised when data structure validation fails."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        message = "Data validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        super().__init__(message, hint="Fix the issues or restore from backup")


# ============================================================================
# Calendar Errors
# ============================================================================


class CalendarError(StudyTrackerError):
    """Base class for calendar operation errors."""

    pass


class CalendarConnectionError(CalendarError):
    """Raised when unable to connect to Calendar app."""

    def __init__(self, reason: str):
        super().__init__(
            f"Cannot connect to Calendar app: {reason}",
            hint="Ensure Calendar.app is installed and not corrupted",
        )


class CalendarPermissionError(CalendarError):
    """Raised when Calendar access is denied."""

    def __init__(self):
        super().__init__(
            "Calendar access denied",
            hint="Grant calendar access in System Preferences > Security & Privacy > Privacy > Calendars",
        )


class CalendarTimeoutError(CalendarError):
    """Raised when a calendar operation times out."""

    def __init__(self, operation: str, timeout_seconds: int):
        self.operation = operation
        self.timeout_seconds = timeout_seconds
        super().__init__(
            f"Calendar operation timed out after {timeout_seconds}s: {operation}",
            hint="Calendar.app may be unresponsive. Try closing and reopening it.",
        )


class CalendarEventError(CalendarError):
    """Raised when creating/modifying an event fails."""

    def __init__(self, event_name: str, reason: str):
        self.event_name = event_name
        super().__init__(f"Failed to create event '{event_name}': {reason}")


# ============================================================================
# Git Errors
# ============================================================================


class GitError(StudyTrackerError):
    """Base class for git operation errors."""

    pass


class GitNotInstalledError(GitError):
    """Raised when git is not available."""

    def __init__(self):
        super().__init__(
            "Git is not installed or not in PATH",
            hint="Install git: https://git-scm.com/downloads",
        )


class GitNotRepoError(GitError):
    """Raised when not in a git repository."""

    def __init__(self, path: str):
        self.path = path
        super().__init__(
            f"Not a git repository: {path}",
            hint="Run 'git init' to initialize a repository",
        )


class GitCommandError(GitError):
    """Raised when a git command fails."""

    def __init__(self, command: str, stderr: str, returncode: int):
        self.command = command
        self.stderr = stderr
        self.returncode = returncode
        super().__init__(
            f"Git command failed: {command}\n  Exit code: {returncode}\n  Error: {stderr.strip()}"
        )


class GitPushError(GitError):
    """Raised when git push fails."""

    def __init__(self, reason: str):
        super().__init__(
            f"Failed to push: {reason}",
            hint="Check your network connection and remote repository access",
        )


class GitPullError(GitError):
    """Raised when git pull fails."""

    def __init__(self, reason: str):
        super().__init__(
            f"Failed to pull: {reason}",
            hint="Check for uncommitted changes or merge conflicts",
        )
