"""Tests for the rules in validation.py.

Each test covers one rule and checks the cases that matter for it, including
the values at the edge of a rule where mistakes usually hide.
"""

from __future__ import annotations

import pytest

from numeracycheck import validation

GOOD_ROW = {
    "id": "Q01", "category": "Identifying primes", "type": "multiple_choice",
    "prompt": "Which of these is prime?", "options": "21|27|29|33",
    "answer": "29", "explanation": "29 has no factors except 1 and itself.",
}


class TestNames:
    def test_accepts_real_names(self):
        assert validation.validate_name("Ada Lovelace").ok
        assert validation.validate_name("O'Neill").ok
        assert validation.validate_name("  Muhiminul  ").ok

    def test_rejects_bad_names_with_a_reason(self):
        assert "before starting" in validation.validate_name("").message
        assert "at least 2" in validation.validate_name("A").message
        assert "letters, spaces" in validation.validate_name("R2D2").message
        assert "40 characters" in validation.validate_name("A" * 41).message
        assert not validation.validate_name(None).ok


class TestReadingAnswers:
    def test_tidies_answers_and_reads_them_as_numbers(self):
        assert validation.clean_answer("  29  ") == "29"
        assert validation.clean_answer("1,009") == "1009"
        assert validation.clean_answer("2X2X3X5") == "2x2x3x5"
        assert validation.clean_answer(None) == ""

        assert validation.to_number("29") == 29
        assert validation.to_number("1,009") == 1009
        assert validation.to_number("twelve") is None
        assert validation.to_number("") is None


class TestCheckingWhatWasSubmitted:
    def test_guards_both_kinds_of_answer_box(self):
        assert validation.check_typed_answer("29").ok
        assert "before submitting" in validation.check_typed_answer("  ").message
        assert "must be a number" in validation.check_typed_answer("twenty").message

        options = ("21", "27", "29", "33")
        assert validation.check_chosen_option("29", options).ok
        assert not validation.check_chosen_option("99", options).ok
        assert not validation.check_chosen_option("", options).ok


class TestMarking:
    def test_marks_matching_answers_right_and_others_wrong(self):
        assert validation.answers_match("29", "29")
        assert validation.answers_match("29.0", "29")
        assert validation.answers_match(" 2 x 2 x 3 x 5 ", "2x2x3x5")
        assert validation.answers_match("1,009", "1009")

        assert not validation.answers_match("27", "29")
        assert not validation.answers_match("", "29")
        assert not validation.answers_match("2x3x5", "2x2x3x5")


class TestScoring:
    def test_works_out_the_percentage(self):
        assert validation.score_percentage(7, 8) == 87.5
        assert validation.score_percentage(2, 3) == 66.7
        assert validation.score_percentage(0, 0) == 0.0

    def test_applies_the_bands_at_their_edges(self):
        assert validation.grade_for_score(80.0) == "Distinction"
        assert validation.grade_for_score(79.9) == "Pass"
        assert validation.grade_for_score(60.0) == "Pass"
        assert validation.grade_for_score(59.9) == "Refer for support"

    def test_rejects_impossible_scores_and_percentages(self):
        with pytest.raises(ValueError):
            validation.score_percentage(-1, 5)
        with pytest.raises(ValueError):
            validation.score_percentage(6, 5)
        with pytest.raises(ValueError):
            validation.grade_for_score(100.1)


class TestSmallHelpers:
    def test_formats_the_time_and_splits_the_options(self):
        assert validation.format_duration(95) == "01:35"
        assert validation.format_duration(-5) == "00:00"
        assert validation.split_options("21|27 | 29") == ("21", "27", "29")
        assert validation.split_options("") == ()


class TestCheckingTheQuestionFile:
    def test_accepts_a_good_row(self):
        assert validation.check_question_row(GOOD_ROW).ok

    def test_rejects_a_row_the_app_cannot_use(self):
        missing = {k: v for k, v in GOOD_ROW.items() if k != "answer"}
        assert "Missing column" in validation.check_question_row(missing).message
        assert "must not be empty" in validation.check_question_row(
            {**GOOD_ROW, "prompt": "  "}).message
        assert "Unsupported question type" in validation.check_question_row(
            {**GOOD_ROW, "type": "essay"}).message
        assert "at least two options" in validation.check_question_row(
            {**GOOD_ROW, "options": "29"}).message
        assert "not one of the options" in validation.check_question_row(
            {**GOOD_ROW, "answer": "99"}).message
        assert not validation.check_question_row(
            {**GOOD_ROW, "type": "numeric", "options": "", "answer": "two"}).ok
