"""
Tests for validation module.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.validation import (
    resolve_course_code,
    validate_status,
    validate_assessment_key,
    validate_hours,
    validate_score,
)
from src.errors import ValidationError


class TestResolveCourseCode:
    """Tests for resolve_course_code function."""

    def test_short_code_lowercase(self):
        assert resolve_course_code("pc") == "ELEC70028"
        assert resolve_course_code("do") == "ELEC70082"
        assert resolve_course_code("cv") == "ELEC70073"
        assert resolve_course_code("ao") == "ELEC70066"

    def test_short_code_uppercase(self):
        assert resolve_course_code("PC") == "ELEC70028"
        assert resolve_course_code("DO") == "ELEC70082"

    def test_full_code(self):
        assert resolve_course_code("ELEC70028") == "ELEC70028"
        assert resolve_course_code("elec70028") == "ELEC70028"

    def test_with_whitespace(self):
        assert resolve_course_code("  pc  ") == "ELEC70028"
        assert resolve_course_code(" ELEC70028 ") == "ELEC70028"

    def test_invalid_code(self):
        with pytest.raises(ValidationError) as exc_info:
            resolve_course_code("invalid")
        assert "Unknown course" in str(exc_info.value)
        assert exc_info.value.field == "course"

    def test_empty_code(self):
        with pytest.raises(ValidationError) as exc_info:
            resolve_course_code("")
        assert exc_info.value.field == "course"

    def test_none_code(self):
        with pytest.raises(ValidationError):
            resolve_course_code(None)  # type: ignore


class TestValidateStatus:
    """Tests for validate_status function."""

    def test_valid_statuses(self):
        assert validate_status("not_started") == "not_started"
        assert validate_status("in_progress") == "in_progress"
        assert validate_status("completed") == "completed"
        assert validate_status("submitted") == "submitted"
        assert validate_status("overdue") == "overdue"
        assert validate_status("ongoing") == "ongoing"

    def test_aliases(self):
        assert validate_status("done") == "completed"
        assert validate_status("finished") == "completed"
        assert validate_status("complete") == "completed"
        assert validate_status("wip") == "in_progress"
        assert validate_status("working") == "in_progress"
        assert validate_status("started") == "in_progress"
        assert validate_status("todo") == "not_started"
        assert validate_status("pending") == "not_started"
        assert validate_status("submit") == "submitted"
        assert validate_status("sent") == "submitted"
        assert validate_status("late") == "overdue"

    def test_case_insensitive(self):
        assert validate_status("DONE") == "completed"
        assert validate_status("In_Progress") == "in_progress"
        assert validate_status("WIP") == "in_progress"

    def test_with_whitespace(self):
        assert validate_status("  done  ") == "completed"

    def test_invalid_status(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_status("invalid")
        assert "Invalid status" in str(exc_info.value)
        assert exc_info.value.field == "status"

    def test_empty_status(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_status("")
        assert exc_info.value.field == "status"


class TestValidateAssessmentKey:
    """Tests for validate_assessment_key function."""

    def test_exact_match(self):
        assessments = {"basic_part_1": {}, "basic_part_2": {}}
        assert (
            validate_assessment_key("ELEC70028", "basic_part_1", assessments)
            == "basic_part_1"
        )

    def test_case_insensitive_match(self):
        assessments = {"Basic_Part_1": {}, "core_part_1": {}}
        assert (
            validate_assessment_key("ELEC70028", "basic_part_1", assessments)
            == "Basic_Part_1"
        )

    def test_partial_match(self):
        assessments = {"basic_part_1": {}, "core_part_1": {}}
        assert (
            validate_assessment_key("ELEC70028", "basic", assessments) == "basic_part_1"
        )

    def test_ambiguous_match(self):
        assessments = {"basic_part_1": {}, "basic_part_2": {}}
        with pytest.raises(ValidationError) as exc_info:
            validate_assessment_key("ELEC70028", "basic", assessments)
        assert "Ambiguous" in str(exc_info.value)
        assert exc_info.value.field == "assessment"

    def test_no_match(self):
        assessments = {"basic_part_1": {}}
        with pytest.raises(ValidationError) as exc_info:
            validate_assessment_key("ELEC70028", "nonexistent", assessments)
        assert "Unknown assessment" in str(exc_info.value)

    def test_empty_key(self):
        assessments = {"basic_part_1": {}}
        with pytest.raises(ValidationError) as exc_info:
            validate_assessment_key("ELEC70028", "", assessments)
        assert exc_info.value.field == "assessment"


class TestValidateHours:
    """Tests for validate_hours function."""

    def test_valid_hours(self):
        assert validate_hours("2") == 2.0
        assert validate_hours("2.5") == 2.5
        assert validate_hours("0.5") == 0.5
        assert validate_hours("0") == 0.0

    def test_integer_input(self):
        # Should also accept numeric types converted to string
        assert validate_hours(str(2)) == 2.0
        assert validate_hours(str(2.5)) == 2.5

    def test_negative_hours(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_hours("-1")
        assert "negative" in str(exc_info.value)
        assert exc_info.value.field == "hours"

    def test_excessive_hours(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_hours("25")
        assert "Maximum is 24" in str(exc_info.value)

    def test_invalid_format(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_hours("abc")
        assert "Invalid hours" in str(exc_info.value)

    def test_empty_hours(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_hours("")
        assert exc_info.value.field == "hours"


class TestValidateScore:
    """Tests for validate_score function."""

    def test_valid_scores(self):
        assert validate_score("pass") == "pass"
        assert validate_score("fail") == "fail"
        assert validate_score("85%") == "85%"
        assert validate_score("17/20") == "17/20"
        assert validate_score("A+") == "A+"

    def test_with_whitespace(self):
        assert validate_score("  pass  ") == "pass"

    def test_empty_score(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_score("")
        assert exc_info.value.field == "score"

    def test_none_score(self):
        with pytest.raises(ValidationError):
            validate_score(None)  # type: ignore


class TestValidationErrorAttributes:
    """Tests for ValidationError attributes."""

    def test_error_has_field(self):
        try:
            resolve_course_code("invalid")
        except ValidationError as e:
            assert e.field == "course"
            assert e.valid_options is not None
            assert len(e.valid_options) > 0

    def test_error_has_hint(self):
        try:
            validate_status("invalid")
        except ValidationError as e:
            assert e.hint is not None
            assert "Valid options" in e.hint

    def test_error_message_format(self):
        try:
            resolve_course_code("xyz")
        except ValidationError as e:
            message = str(e)
            assert "xyz" in message
            assert "Hint" in message
