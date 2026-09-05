"""Tests for the Question and Attempt classes."""

from __future__ import annotations

import pytest

from numeracycheck.errors import DataError
from numeracycheck.models import (
    Attempt,
    MultipleChoiceQuestion,
    NumericQuestion,
    Question,
)


class TestBuilding:
    def test_builds_question_types(self):
        choice = Question.from_row({
            "id": "Q01", "category": "Identifying primes", "type": "multiple_choice",
            "prompt": "Which of these is prime?", "options": "21|27|29|33",
            "answer": "29", "explanation": "",
        })
        typed = Question.from_row({
            "id": "Q02", "category": "Identifying primes", "type": "numeric",
            "prompt": "What is the smallest prime number?", "options": "",
            "answer": "2",
        })
        assert isinstance(choice, MultipleChoiceQuestion)
        assert choice.options == ("21", "27", "29", "33")
        assert isinstance(typed, NumericQuestion)
        assert typed.options == ()

    def test_rejects_bad_row(self):
        with pytest.raises(DataError):
            Question.from_row({"id": "Q1", "category": "", "type": "numeric"})
        with pytest.raises(TypeError):
            Question("Q1", "Topic", "Prompt", "1", "")


class TestMarking:
    def test_marking(self, typed_question, choice_question):
        assert typed_question.is_correct(" 2.0 ")
        assert not typed_question.check("two").ok
        assert choice_question.is_correct("29")
        assert not choice_question.is_correct("27")
        assert not choice_question.check("99").ok

    def test_frozen(self, typed_question):
        with pytest.raises(Exception):
            typed_question.answer = "42"


class TestAttempt:
    def test_attempt_round_trip(self, attempt):
        row = attempt.to_row()
        assert set(row) == set(Attempt.COLUMNS)
        assert row["percentage"] == "87.5"
        assert Attempt.from_row(row) == attempt

        missing = attempt.to_row()
        del missing["grade"]
        with pytest.raises((ValueError, KeyError)):
            Attempt.from_row(missing)
        with pytest.raises(ValueError):
            Attempt.from_row({**attempt.to_row(), "percentage": "high"})
