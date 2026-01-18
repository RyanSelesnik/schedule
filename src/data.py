"""
Data management with backups and comprehensive error handling.

Provides:
- Atomic file writes (write to temp, then rename)
- Automatic backups with retention policy
- Validation before save
- Detailed error messages for troubleshooting
"""

import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple

from .config import (
    TRACKER_PATH,
    COURSES_PATH,
    BACKUP_DIR,
    MAX_BACKUPS,
    COURSE_NAMES,
    CODE_TO_ALIAS,
)
from .errors import (
    DataError,
    DataNotFoundError,
    DataCorruptedError,
    DataWriteError,
    DataValidationError,
    ValidationError,
)


def _check_disk_space(path: Path, required_bytes: int = 1024 * 1024) -> bool:
    """
    Check if there's enough disk space for a write operation.

    Args:
        path: Path where we want to write
        required_bytes: Minimum required space in bytes (default 1MB)

    Returns:
        True if enough space available
    """
    try:
        stat = os.statvfs(path.parent)
        available = stat.f_frsize * stat.f_bavail
        return available >= required_bytes
    except (OSError, AttributeError):
        # statvfs not available on all platforms, assume ok
        return True


def _check_write_permission(path: Path) -> bool:
    """
    Check if we can write to a path.

    Args:
        path: Path to check

    Returns:
        True if writable
    """
    if path.exists():
        return os.access(path, os.W_OK)
    # Check parent directory
    return os.access(path.parent, os.W_OK)


def _create_backup(file_path: Path) -> Optional[Path]:
    """
    Create a timestamped backup of a file.

    Args:
        file_path: Path to file to backup

    Returns:
        Path to backup file, or None if source doesn't exist

    Raises:
        DataWriteError: If backup creation fails
    """
    if not file_path.exists():
        return None

    # Ensure backup directory exists
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        raise DataWriteError(
            str(BACKUP_DIR), "Cannot create backup directory - permission denied"
        )
    except OSError as e:
        raise DataWriteError(str(BACKUP_DIR), str(e))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
    backup_path = BACKUP_DIR / backup_name

    try:
        shutil.copy2(file_path, backup_path)
    except PermissionError:
        raise DataWriteError(
            str(backup_path), "Cannot write backup - permission denied"
        )
    except OSError as e:
        raise DataWriteError(str(backup_path), str(e))

    # Cleanup old backups (don't fail on cleanup errors)
    try:
        _cleanup_old_backups(file_path.stem)
    except Exception:
        pass  # Cleanup is best-effort

    return backup_path


def _cleanup_old_backups(prefix: str) -> int:
    """
    Remove old backups, keeping only MAX_BACKUPS most recent.

    Args:
        prefix: Backup file prefix to match

    Returns:
        Number of backups deleted
    """
    backups = sorted(
        BACKUP_DIR.glob(f"{prefix}_*.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    deleted = 0
    for old_backup in backups[MAX_BACKUPS:]:
        try:
            old_backup.unlink()
            deleted += 1
        except OSError:
            pass  # Ignore cleanup errors

    return deleted


def validate_tracker_data(data: dict) -> Tuple[bool, List[str]]:
    """
    Validate entire tracker data structure.

    Args:
        data: Tracker data dict

    Returns:
        Tuple of (is_valid, list of errors)
    """
    from .config import VALID_STATUSES

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


def load_tracker() -> dict:
    """
    Load tracker data with validation.

    Returns:
        Tracker data dict

    Raises:
        DataNotFoundError: If tracker file doesn't exist
        DataCorruptedError: If file cannot be parsed
        DataValidationError: If data structure is invalid
    """
    if not TRACKER_PATH.exists():
        raise DataNotFoundError(str(TRACKER_PATH), "Tracker file")

    # Check if file is readable
    if not os.access(TRACKER_PATH, os.R_OK):
        raise DataError(
            f"Cannot read tracker file: {TRACKER_PATH}", hint="Check file permissions"
        )

    try:
        with open(TRACKER_PATH, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                raise DataCorruptedError(str(TRACKER_PATH), "File is empty")
            data = json.loads(content)
    except json.JSONDecodeError as e:
        raise DataCorruptedError(str(TRACKER_PATH), str(e))
    except UnicodeDecodeError as e:
        raise DataCorruptedError(str(TRACKER_PATH), f"Invalid encoding: {e}")
    except PermissionError:
        raise DataError(
            f"Permission denied reading: {TRACKER_PATH}", hint="Check file permissions"
        )
    except OSError as e:
        raise DataError(f"Cannot read file: {e}")

    # Validate structure
    is_valid, errors = validate_tracker_data(data)
    if not is_valid:
        raise DataValidationError(errors)

    return data


def save_tracker(data: dict, create_backup: bool = True) -> Path:
    """
    Save tracker data with optional backup.

    Uses atomic write pattern: write to temp file, then rename.
    This prevents data corruption if the write is interrupted.

    Args:
        data: Tracker data to save
        create_backup: Whether to create a backup first

    Returns:
        Path to saved file

    Raises:
        DataValidationError: If data validation fails
        DataWriteError: If save fails
    """
    # Validate before saving
    is_valid, errors = validate_tracker_data(data)
    if not is_valid:
        raise DataValidationError(errors)

    # Check disk space
    if not _check_disk_space(TRACKER_PATH):
        raise DataWriteError(str(TRACKER_PATH), "Insufficient disk space")

    # Check write permission
    if not _check_write_permission(TRACKER_PATH):
        raise DataWriteError(str(TRACKER_PATH), "Permission denied")

    # Create backup
    if create_backup and TRACKER_PATH.exists():
        _create_backup(TRACKER_PATH)

    # Update timestamp
    data["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Write to temp file first, then rename (atomic operation)
    temp_path = TRACKER_PATH.with_suffix(".tmp")

    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush()
            os.fsync(f.fileno())  # Ensure data is written to disk
    except PermissionError:
        raise DataWriteError(str(temp_path), "Permission denied")
    except OSError as e:
        raise DataWriteError(str(temp_path), str(e))

    # Atomic rename
    try:
        temp_path.rename(TRACKER_PATH)
    except OSError as e:
        # Clean up temp file if rename fails
        try:
            temp_path.unlink()
        except OSError:
            pass
        raise DataWriteError(str(TRACKER_PATH), f"Failed to rename temp file: {e}")

    return TRACKER_PATH


def load_courses() -> dict:
    """
    Load courses data.

    Returns:
        Courses data dict

    Raises:
        DataNotFoundError: If file doesn't exist
        DataCorruptedError: If file cannot be parsed
    """
    if not COURSES_PATH.exists():
        raise DataNotFoundError(str(COURSES_PATH), "Courses file")

    try:
        with open(COURSES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise DataCorruptedError(str(COURSES_PATH), str(e))
    except PermissionError:
        raise DataError(
            f"Permission denied reading: {COURSES_PATH}", hint="Check file permissions"
        )
    except OSError as e:
        raise DataError(f"Cannot read file: {e}")


def get_course_display_name(code: str) -> str:
    """Get display name with alias for a course code."""
    alias = CODE_TO_ALIAS.get(code, "??")
    name = COURSE_NAMES.get(code, code)
    return f"[{alias}] {name}"


def list_backups() -> List[dict]:
    """
    List all available backups.

    Returns:
        List of backup info dicts, sorted by most recent first
    """
    if not BACKUP_DIR.exists():
        return []

    backups = []
    for backup in sorted(BACKUP_DIR.glob("*.json"), reverse=True):
        try:
            stat = backup.stat()
            backups.append(
                {
                    "path": backup,
                    "name": backup.name,
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime),
                }
            )
        except OSError:
            # Skip files we can't stat
            continue
    return backups


def restore_backup(backup_name: str) -> Path:
    """
    Restore a backup file.

    Args:
        backup_name: Name of backup file to restore

    Returns:
        Path to restored file

    Raises:
        DataNotFoundError: If backup doesn't exist
        DataWriteError: If restore fails
    """
    backup_path = BACKUP_DIR / backup_name
    if not backup_path.exists():
        available = [b["name"] for b in list_backups()]
        if available:
            raise DataNotFoundError(
                str(backup_path), f"backup file. Available: {', '.join(available[:5])}"
            )
        else:
            raise DataNotFoundError(str(backup_path), "backup file. No backups found.")

    # Validate the backup before restoring
    try:
        with open(backup_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        is_valid, errors = validate_tracker_data(data)
        if not is_valid:
            raise DataValidationError(errors)
    except json.JSONDecodeError as e:
        raise DataCorruptedError(str(backup_path), str(e))

    # Backup current before restore
    if TRACKER_PATH.exists():
        _create_backup(TRACKER_PATH)

    try:
        shutil.copy2(backup_path, TRACKER_PATH)
    except PermissionError:
        raise DataWriteError(str(TRACKER_PATH), "Permission denied")
    except OSError as e:
        raise DataWriteError(str(TRACKER_PATH), str(e))

    return TRACKER_PATH


# Re-export for backwards compatibility
__all__ = [
    "DataError",
    "load_tracker",
    "save_tracker",
    "load_courses",
    "get_course_display_name",
    "list_backups",
    "restore_backup",
    "validate_tracker_data",
]
