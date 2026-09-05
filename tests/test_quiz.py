"""Tests for running one attempt."""

from __future__ import annotations

import pytest

from numeracycheck.errors import QuizStateError
from numeracycheck.quiz import Quiz


@pytest.fixture
def quiz(questions, clock):
    """A two-question quiz driven by a fake clock."""
    return Quiz("Ada Lovelace", questions, "Identifying primes", clock=clock)


class TestStarting:
    def test_starting_a_quiz(self, questions):
        with pytest.raises(QuizStateError, match="at least one question"):
            Quiz("Ada", [])
        with pytest.raises(ValueError):
            Quiz("", questions)
        assert Quiz("  Ada  ", questions).name == "Ada"


class TestProgress:
    def test_progress(self, quiz, questions):
        assert quiz.current is questions[0]
        assert quiz.progress() == "Question 1 of 2"
        quiz.submit("29")
        assert quiz.current is questions[1]
        quiz.submit("2")
        assert quiz.finished
        with pytest.raises(QuizStateError, match="has finished"):
            _ = quiz.current

    def test_bad_answer_stays_put(self, quiz):
        result = quiz.submit("")
        assert not result.accepted
        assert quiz.progress() == "Question 1 of 2"
        assert quiz.answers == []


class TestMarking:
    def test_marking(self, quiz):
        right = quiz.submit("29")
        assert right.accepted and right.correct
        assert quiz.correct_count == 1

        wrong = quiz.submit("7")
        assert not wrong.correct
        assert "2" in wrong.message


class TestScoring:
    def test_scoring(self, quiz):
        quiz.submit("29")
        quiz.submit("7")
        assert quiz.percentage() == 50.0
        assert quiz.grade() == "Refer for support"

    def test_saving_the_attempt(self, quiz, clock):
        quiz.submit("29")
        with pytest.raises(QuizStateError, match="Finish every question"):
            quiz.to_attempt()

        quiz.submit("2")
        clock.advance(120)
        attempt = quiz.to_attempt(make_id=lambda: "test0001")

        assert attempt.attempt_id == "test0001"
        assert attempt.name == "Ada Lovelace"
        assert attempt.category == "Identifying primes"
        assert (attempt.asked, attempt.correct) == (2, 2)
        assert attempt.percentage == 100.0
        assert attempt.grade == "Distinction"
        assert attempt.seconds == 120
