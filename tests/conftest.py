"""Fixtures shared between the tests.

The file-based fixtures use pytest's tmp_path which keeps the tests from
changing the real quiz data.
"""

from __future__ import annotations

import csv

import pytest

from numeracycheck.models import Attempt, MultipleChoiceQuestion, NumericQuestion
from numeracycheck.storage import QuestionBank, ResultsStore

HEADER = ["id", "category", "type", "prompt", "options", "answer", "explanation"]
ROWS = [
    ["Q01", "Identifying primes", "multiple_choice", "Which of these is prime?",
     "21|27|29|33", "29", "29 has no factors except 1 and itself."],
    ["Q02", "Identifying primes", "numeric", "What is the smallest prime number?",
     "", "2", ""],
    ["Q03", "Prime factors", "numeric", "Largest prime factor of 30?", "", "5", ""],
    ["Q04", "Prime factors", "multiple_choice", "Which is a prime factor of 105?",
     "4|5|6|8", "5", ""],
]


@pytest.fixture
def choice_question():
    """A multiple-choice question with four options."""
    return MultipleChoiceQuestion("Q01", "Identifying primes",
                                  "Which of these is prime?", "29",
                                  "29 has no factors except 1 and itself.",
                                  ("21", "27", "29", "33"))


@pytest.fixture
def typed_question():
    """A question answered by typing a number."""
    return NumericQuestion("Q02", "Identifying primes",
                           "What is the smallest prime number?", "2", "")


@pytest.fixture
def questions(choice_question, typed_question):
    """Two questions, used to run short quizzes."""
    return [choice_question, typed_question]


@pytest.fixture
def questions_csv(tmp_path):
    """A valid question file in a temporary folder."""
    path = tmp_path / "questions.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(HEADER)
        writer.writerows(ROWS)
    return path


@pytest.fixture
def bank(questions_csv):
    """A question bank loaded from the temporary file."""
    return QuestionBank.from_csv(questions_csv)


@pytest.fixture
def store(tmp_path):
    """A results store pointing at a temporary file."""
    return ResultsStore(tmp_path / "results" / "results.csv")


@pytest.fixture
def attempt():
    """A finished attempt with known values."""
    return Attempt("abc12345", "Ada Lovelace", "Identifying primes",
                   "2026-09-01T09:15:04+00:00", 8, 7, 87.5, "Distinction", 214)


class FakeClock:
    """A clock a test can move forward on demand."""

    def __init__(self, start=0.0):
        self.now = start

    def __call__(self):
        return self.now

    def advance(self, seconds):
        """Move the clock forward."""
        self.now += seconds


@pytest.fixture
def clock():
    """A fake clock starting at zero."""
    return FakeClock()
