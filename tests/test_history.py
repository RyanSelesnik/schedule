"""
Tests for src/history.py - History tracking for undo functionality.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from unittest.mock import patch

from src import history


class TestHistoryOperations:
    """Tests for history loading and saving."""

    def setup_method(self):
        """Create a temp history file for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_history_file = Path(self.temp_dir) / ".study_history.json"
        # Patch the HISTORY_FILE constant
        self._original_file = history.HISTORY_FILE
        history.HISTORY_FILE = self.temp_history_file

    def teardown_method(self):
        """Clean up temp files."""
        history.HISTORY_FILE = self._original_file
        if self.temp_history_file.exists():
            self.temp_history_file.unlink()

    def test_load_empty_history(self):
        """Loading non-existent history returns empty list."""
        result = history._load_history()
        assert result == []

    def test_load_invalid_json(self):
        """Loading invalid JSON returns empty list."""
        self.temp_history_file.write_text("not valid json")
        result = history._load_history()
        assert result == []

    def test_save_and_load_history(self):
        """History can be saved and loaded."""
        test_data = [{"action": "test", "timestamp": "2026-01-18T12:00:00"}]
        history._save_history(test_data)

        result = history._load_history()
        assert result == test_data

    def test_max_history_limit(self):
        """History is limited to MAX_HISTORY entries."""
        # Create more entries than MAX_HISTORY
        entries = [{"action": f"test_{i}"} for i in range(history.MAX_HISTORY + 20)]
        history._save_history(entries)

        result = history._load_history()
        assert len(result) == history.MAX_HISTORY
        # Should keep the last entries
        assert result[0]["action"] == f"test_20"


class TestRecordChange:
    """Tests for recording changes."""

    def setup_method(self):
        """Create a temp history file for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.temp_history_file = Path(self.temp_dir) / ".study_history.json"
        self._original_file = history.HISTORY_FILE
        history.HISTORY_FILE = self.temp_history_file

    def teardown_method(self):
        history.HISTORY_FILE = self._original_file
        if self.temp_history_file.exists():
            self.temp_history_file.unlink()

    def test_record_status_change(self):
        """Can record a status change."""
        history.record_change(
            action="update_status",
            course_code="ELEC60020",
            assessment_key="basic_part_1",
            field="status",
            old_value="not_started",
            new_value="in_progress",
        )

        changes = history._load_history()
        assert len(changes) == 1
        assert changes[0]["action"] == "update_status"
        assert changes[0]["old_value"] == "not_started"
        assert changes[0]["new_value"] == "in_progress"

    def test_record_change_with_description(self):
        """Can record a change with custom description."""
        history.record_change(
            action="record_score",
            course_code="ELEC60020",
            assessment_key="basic_part_1",
            field="score",
            old_value=None,
            new_value="85%",
            description="Recorded score of 85%",
        )

        changes = history._load_history()
        assert changes[0]["description"] == "Recorded score of 85%"

    def test_record_change_auto_description(self):
        """Changes without description get auto-generated one."""
        history.record_change(
            action="update_status",
            course_code="ELEC60020",
            assessment_key="basic_part_1",
            field="status",
            old_value="old",
            new_value="new",
        )

        changes = history._load_history()
        assert "old" in changes[0]["description"]
        assert "new" in changes[0]["description"]


class TestRecordHoursChange:
    """Tests for recording hours changes."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_history_file = Path(self.temp_dir) / ".study_history.json"
        self._original_file = history.HISTORY_FILE
        history.HISTORY_FILE = self.temp_history_file

    def teardown_method(self):
        history.HISTORY_FILE = self._original_file
        if self.temp_history_file.exists():
            self.temp_history_file.unlink()

    def test_record_hours(self):
        """Can record hours logged."""
        history.record_hours_change(
            week_num="2026-W03",
            old_hours=5.0,
            new_hours=7.5,
            added_hours=2.5,
        )

        changes = history._load_history()
        assert len(changes) == 1
        assert changes[0]["action"] == "log_hours"
        assert changes[0]["added_hours"] == 2.5

    def test_record_hours_with_course(self):
        """Can record hours with course attribution."""
        history.record_hours_change(
            week_num="2026-W03",
            old_hours=0,
            new_hours=2.0,
            added_hours=2.0,
            course_code="ELEC60020",
        )

        changes = history._load_history()
        assert changes[0]["course_code"] == "ELEC60020"


class TestGetChanges:
    """Tests for retrieving changes."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_history_file = Path(self.temp_dir) / ".study_history.json"
        self._original_file = history.HISTORY_FILE
        history.HISTORY_FILE = self.temp_history_file

        # Pre-populate with some changes
        for i in range(5):
            history.record_change(
                action="test",
                course_code="TEST",
                assessment_key=f"assessment_{i}",
                field="status",
                old_value="old",
                new_value="new",
            )

    def teardown_method(self):
        history.HISTORY_FILE = self._original_file
        if self.temp_history_file.exists():
            self.temp_history_file.unlink()

    def test_get_last_change(self):
        """Can get the most recent change."""
        last = history.get_last_change()
        assert last is not None
        assert last["assessment_key"] == "assessment_4"

    def test_get_last_change_empty(self):
        """Returns None when no history."""
        history.clear_history()
        last = history.get_last_change()
        assert last is None

    def test_get_recent_changes(self):
        """Can get recent changes in reverse order."""
        recent = history.get_recent_changes(3)
        assert len(recent) == 3
        # Should be in reverse order (most recent first)
        assert recent[0]["assessment_key"] == "assessment_4"
        assert recent[1]["assessment_key"] == "assessment_3"
        assert recent[2]["assessment_key"] == "assessment_2"

    def test_get_recent_changes_fewer_than_requested(self):
        """Handles case where fewer entries exist than requested."""
        history.clear_history()
        history.record_change(
            action="test",
            course_code="TEST",
            assessment_key="only_one",
            field="status",
            old_value="old",
            new_value="new",
        )

        recent = history.get_recent_changes(10)
        assert len(recent) == 1


class TestPopAndClear:
    """Tests for pop and clear operations."""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_history_file = Path(self.temp_dir) / ".study_history.json"
        self._original_file = history.HISTORY_FILE
        history.HISTORY_FILE = self.temp_history_file

        # Pre-populate
        history.record_change(
            action="test",
            course_code="TEST",
            assessment_key="first",
            field="status",
            old_value="old",
            new_value="new",
        )
        history.record_change(
            action="test",
            course_code="TEST",
            assessment_key="second",
            field="status",
            old_value="old",
            new_value="new",
        )

    def teardown_method(self):
        history.HISTORY_FILE = self._original_file
        if self.temp_history_file.exists():
            self.temp_history_file.unlink()

    def test_pop_last_change(self):
        """Pop removes and returns the last change."""
        popped = history.pop_last_change()
        assert popped["assessment_key"] == "second"

        # Should only have one left
        remaining = history._load_history()
        assert len(remaining) == 1
        assert remaining[0]["assessment_key"] == "first"

    def test_pop_empty_history(self):
        """Pop returns None when history is empty."""
        history.clear_history()
        popped = history.pop_last_change()
        assert popped is None

    def test_clear_history(self):
        """Clear removes all history and returns count."""
        count = history.clear_history()
        assert count == 2

        remaining = history._load_history()
        assert remaining == []

    def test_clear_empty_history(self):
        """Clear handles empty history."""
        history.clear_history()
        count = history.clear_history()
        assert count == 0


class TestFormatChangeDescription:
    """Tests for formatting change descriptions."""

    def test_format_status_change(self):
        """Can format a status change description."""
        entry = {
            "timestamp": "2026-01-18T16:37:00",
            "action": "update_status",
            "course_code": "ELEC60020",
            "assessment_key": "basic_part_1",
            "old_value": "not_started",
            "new_value": "in_progress",
        }

        result = history.format_change_description(entry)
        assert "18 Jan" in result
        assert "16:37" in result
        assert "not_started" in result
        assert "in_progress" in result

    def test_format_hours_change(self):
        """Can format a hours change description."""
        entry = {
            "timestamp": "2026-01-18T16:37:00",
            "action": "log_hours",
            "added_hours": 2.5,
            "course_code": "ELEC60020",
        }

        result = history.format_change_description(entry)
        assert "2.5h" in result

    def test_format_score_change(self):
        """Can format a score change description."""
        entry = {
            "timestamp": "2026-01-18T16:37:00",
            "action": "record_score",
            "course_code": "ELEC60020",
            "assessment_key": "basic_part_1",
            "new_value": "85%",
        }

        result = history.format_change_description(entry)
        assert "scored" in result
        assert "85%" in result
