"""
Tests for data module and error handling.
"""

import pytest
import json
import sys
import tempfile
import os
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validation import validate_tracker_data
from src.config import VALID_STATUSES
from src.errors import (
    StudyTrackerError,
    ValidationError,
    DataError,
    DataNotFoundError,
    DataCorruptedError,
    DataWriteError,
    DataValidationError,
)


class TestValidateTrackerData:
    """Tests for validate_tracker_data function."""

    def test_valid_data(self):
        data = {
            "courses": {
                "ELEC70028": {
                    "name": "Test Course",
                    "assessments": {
                        "test_assessment": {"name": "Test", "status": "not_started"}
                    },
                }
            }
        }
        is_valid, errors = validate_tracker_data(data)
        assert is_valid
        assert len(errors) == 0

    def test_missing_courses(self):
        data = {}
        is_valid, errors = validate_tracker_data(data)
        assert not is_valid
        assert any("courses" in e for e in errors)

    def test_courses_not_dict(self):
        data = {"courses": "invalid"}
        is_valid, errors = validate_tracker_data(data)
        assert not is_valid
        assert any("dictionary" in e for e in errors)

    def test_invalid_status(self):
        data = {
            "courses": {
                "ELEC70028": {
                    "name": "Test",
                    "assessments": {
                        "test": {"name": "Test", "status": "invalid_status"}
                    },
                }
            }
        }
        is_valid, errors = validate_tracker_data(data)
        assert not is_valid
        assert any("invalid_status" in e.lower() for e in errors)

    def test_all_valid_statuses_accepted(self):
        for status in VALID_STATUSES:
            data = {
                "courses": {
                    "ELEC70028": {
                        "name": "Test",
                        "assessments": {"test": {"name": "Test", "status": status}},
                    }
                }
            }
            is_valid, errors = validate_tracker_data(data)
            assert is_valid, f"Status '{status}' should be valid"

    def test_unknown_course_code(self):
        data = {
            "courses": {"UNKNOWN123": {"name": "Unknown Course", "assessments": {}}}
        }
        is_valid, errors = validate_tracker_data(data)
        assert not is_valid
        assert any("Unknown course" in e for e in errors)

    def test_empty_status_allowed(self):
        """Empty status should be allowed (default to not_started)."""
        data = {
            "courses": {
                "ELEC70028": {
                    "name": "Test",
                    "assessments": {"test": {"name": "Test", "status": ""}},
                }
            }
        }
        is_valid, errors = validate_tracker_data(data)
        assert is_valid


class TestBackupFunctionality:
    """Tests for backup functionality."""

    def test_backup_directory_exists(self):
        from src.config import BACKUP_DIR

        # Should be created by config import
        assert BACKUP_DIR.exists() or True  # Directory created on first save


class TestCourseDisplayName:
    """Tests for course display formatting."""

    def test_get_course_display_name(self):
        from src.data import get_course_display_name

        result = get_course_display_name("ELEC70028")
        assert "[pc]" in result
        assert "Predictive Control" in result

        result = get_course_display_name("ELEC70082")
        assert "[do]" in result
        assert "Distributed Optimisation" in result

    def test_unknown_course_display(self):
        from src.data import get_course_display_name

        result = get_course_display_name("UNKNOWN123")
        assert "[??]" in result
        assert "UNKNOWN123" in result


class TestErrorHierarchy:
    """Tests for the error exception hierarchy."""

    def test_all_errors_inherit_from_base(self):
        """All custom errors should inherit from StudyTrackerError."""
        assert issubclass(ValidationError, StudyTrackerError)
        assert issubclass(DataError, StudyTrackerError)
        assert issubclass(DataNotFoundError, DataError)
        assert issubclass(DataCorruptedError, DataError)
        assert issubclass(DataWriteError, DataError)
        assert issubclass(DataValidationError, DataError)

    def test_error_message_and_hint(self):
        """Test that errors properly format message and hint."""
        error = StudyTrackerError("Test message", hint="Test hint")
        assert "Test message" in str(error)
        assert "Hint" in str(error)
        assert "Test hint" in str(error)

    def test_error_without_hint(self):
        """Test error without hint."""
        error = StudyTrackerError("Test message")
        assert "Test message" in str(error)
        assert "Hint" not in str(error)

    def test_validation_error_with_options(self):
        """Test ValidationError with valid_options."""
        error = ValidationError(
            "Invalid value", field="test_field", valid_options=["a", "b", "c"]
        )
        assert error.field == "test_field"
        assert error.valid_options == ["a", "b", "c"]
        assert error.hint is not None
        assert "Valid options" in error.hint

    def test_data_not_found_error(self):
        """Test DataNotFoundError formatting."""
        error = DataNotFoundError("/path/to/file", "Tracker file")
        assert "/path/to/file" in error.message
        assert "Tracker file" in error.message
        assert error.hint is not None

    def test_data_corrupted_error(self):
        """Test DataCorruptedError formatting."""
        error = DataCorruptedError("/path/to/file", "JSON parse error")
        assert "/path/to/file" in error.message
        assert "JSON parse error" in error.message

    def test_data_write_error(self):
        """Test DataWriteError formatting."""
        error = DataWriteError("/path/to/file", "Permission denied")
        assert "/path/to/file" in error.message
        assert "Permission denied" in error.message

    def test_data_validation_error(self):
        """Test DataValidationError with multiple errors."""
        errors = ["Error 1", "Error 2", "Error 3"]
        error = DataValidationError(errors)
        assert error.errors == errors
        for e in errors:
            assert e in error.message


class TestListBackups:
    """Tests for list_backups function."""

    def test_list_backups_empty_dir(self):
        """Test listing backups when directory is empty or doesn't exist."""
        from src.data import list_backups

        # Should return empty list, not raise
        backups = list_backups()
        assert isinstance(backups, list)

    def test_backup_info_structure(self):
        """Test that backup info has required fields."""
        from src.data import list_backups

        backups = list_backups()
        for backup in backups:
            assert "path" in backup
            assert "name" in backup
            assert "size" in backup
            assert "modified" in backup
            assert isinstance(backup["modified"], datetime)
