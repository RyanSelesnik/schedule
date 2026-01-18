"""
Tests for src/ui.py - UI utilities.
"""

import pytest
from datetime import datetime
from unittest.mock import patch

from src.ui import (
    Colors,
    red,
    green,
    yellow,
    blue,
    cyan,
    gray,
    bold,
    dim,
    bold_red,
    bold_green,
    bold_yellow,
    bold_blue,
    format_status,
    format_status_emoji,
    format_days_remaining,
    format_date,
    format_progress_bar,
    format_progress_summary,
    confirm,
)


class TestColors:
    """Tests for color enable/disable functionality."""

    def test_disable_clears_all_colors(self):
        """Colors.disable() should clear all color codes."""
        Colors.disable()
        assert Colors.RED == ""
        assert Colors.GREEN == ""
        assert Colors.RESET == ""
        assert Colors.BOLD == ""

    def test_color_functions_work_when_disabled(self):
        """Color functions should still work when colors are disabled."""
        Colors.disable()
        assert red("test") == "test"
        assert green("test") == "test"
        assert bold("test") == "test"


class TestColorFunctions:
    """Tests for color convenience functions."""

    def setup_method(self):
        """Disable colors for predictable testing."""
        Colors.disable()

    def test_red(self):
        assert red("error") == "error"

    def test_green(self):
        assert green("success") == "success"

    def test_yellow(self):
        assert yellow("warning") == "warning"

    def test_blue(self):
        assert blue("info") == "info"

    def test_cyan(self):
        assert cyan("highlight") == "highlight"

    def test_gray(self):
        assert gray("muted") == "muted"

    def test_bold(self):
        assert bold("strong") == "strong"

    def test_dim(self):
        assert dim("faded") == "faded"

    def test_bold_red(self):
        assert bold_red("critical") == "critical"

    def test_bold_green(self):
        assert bold_green("great") == "great"

    def test_bold_yellow(self):
        assert bold_yellow("caution") == "caution"

    def test_bold_blue(self):
        assert bold_blue("accent") == "accent"


class TestFormatStatus:
    """Tests for status formatting."""

    def setup_method(self):
        Colors.disable()

    def test_not_started(self):
        result = format_status("not_started")
        assert "Not started" in result

    def test_in_progress(self):
        result = format_status("in_progress")
        assert "In progress" in result

    def test_completed(self):
        result = format_status("completed")
        assert "Completed" in result

    def test_submitted(self):
        result = format_status("submitted")
        assert "Submitted" in result

    def test_overdue(self):
        result = format_status("overdue")
        assert "OVERDUE" in result

    def test_ongoing(self):
        result = format_status("ongoing")
        assert "Ongoing" in result

    def test_unknown_status(self):
        result = format_status("unknown_status")
        assert "unknown_status" in result

    def test_without_emoji(self):
        result = format_status("completed", with_emoji=False)
        assert "Completed" in result


class TestFormatStatusEmoji:
    """Tests for status emoji function."""

    def test_all_statuses_have_emojis(self):
        statuses = [
            "not_started",
            "in_progress",
            "completed",
            "submitted",
            "overdue",
            "ongoing",
        ]
        for status in statuses:
            emoji = format_status_emoji(status)
            assert emoji != ""
            assert emoji != "?"

    def test_unknown_status_returns_question(self):
        assert format_status_emoji("unknown") == "❓"


class TestFormatDaysRemaining:
    """Tests for days remaining formatting."""

    def setup_method(self):
        Colors.disable()

    def test_overdue(self):
        result = format_days_remaining(-5)
        assert "OVERDUE" in result
        assert "5" in result

    def test_today(self):
        result = format_days_remaining(0)
        assert "TODAY" in result

    def test_tomorrow(self):
        result = format_days_remaining(1)
        assert "TOMORROW" in result

    def test_few_days(self):
        result = format_days_remaining(3)
        assert "3" in result
        assert "left" in result

    def test_week(self):
        result = format_days_remaining(7)
        assert "7" in result

    def test_far_future(self):
        result = format_days_remaining(30)
        assert "30" in result

    def test_short_format(self):
        result = format_days_remaining(5, short=True)
        assert "5d" in result


class TestFormatDate:
    """Tests for date formatting."""

    def test_short_format(self):
        dt = datetime(2026, 1, 30)
        result = format_date(dt, "short")
        assert "30" in result
        assert "Jan" in result

    def test_medium_format(self):
        dt = datetime(2026, 1, 30)
        result = format_date(dt, "medium")
        assert "2026" in result

    def test_long_format(self):
        dt = datetime(2026, 1, 30)
        result = format_date(dt, "long")
        assert "January" in result or "Jan" in result

    def test_iso_format(self):
        dt = datetime(2026, 1, 30)
        result = format_date(dt, "iso")
        assert result == "2026-01-30"


class TestFormatProgressBar:
    """Tests for progress bar formatting."""

    def setup_method(self):
        Colors.disable()

    def test_zero_total(self):
        result = format_progress_bar(0, 0)
        assert "0%" in result

    def test_zero_completed(self):
        result = format_progress_bar(0, 10)
        assert "0%" in result

    def test_half_completed(self):
        result = format_progress_bar(5, 10)
        assert "50%" in result

    def test_all_completed(self):
        result = format_progress_bar(10, 10)
        assert "100%" in result

    def test_custom_width(self):
        result = format_progress_bar(5, 10, width=10)
        assert "[" in result
        assert "]" in result


class TestFormatProgressSummary:
    """Tests for progress summary formatting."""

    def setup_method(self):
        Colors.disable()

    def test_no_assessments(self):
        result = format_progress_summary(0, 0)
        assert "No assessments" in result

    def test_partial_complete(self):
        result = format_progress_summary(5, 10)
        assert "5/10" in result
        assert "50%" in result

    def test_all_complete(self):
        result = format_progress_summary(10, 10)
        assert "100%" in result


class TestConfirm:
    """Tests for confirmation prompts."""

    def test_skip_confirm_returns_true(self):
        """skip_confirm=True should return True without prompting."""
        result = confirm("Delete?", skip_confirm=True)
        assert result is True

    def test_yes_response(self):
        """'y' response should return True."""
        with patch("builtins.input", return_value="y"):
            result = confirm("Continue?")
            assert result is True

    def test_yes_full_response(self):
        """'yes' response should return True."""
        with patch("builtins.input", return_value="yes"):
            result = confirm("Continue?")
            assert result is True

    def test_no_response(self):
        """'n' response should return False."""
        with patch("builtins.input", return_value="n"):
            result = confirm("Continue?")
            assert result is False

    def test_empty_response_default_false(self):
        """Empty response with default=False should return False."""
        with patch("builtins.input", return_value=""):
            result = confirm("Continue?", default=False)
            assert result is False

    def test_empty_response_default_true(self):
        """Empty response with default=True should return True."""
        with patch("builtins.input", return_value=""):
            result = confirm("Continue?", default=True)
            assert result is True

    def test_eof_returns_false(self):
        """EOFError should return False."""
        with patch("builtins.input", side_effect=EOFError):
            result = confirm("Continue?")
            assert result is False

    def test_keyboard_interrupt_returns_false(self):
        """KeyboardInterrupt should return False."""
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            result = confirm("Continue?")
            assert result is False
