"""Models used by the application and the main models are questions and quiz attempts.

Question is an abstract base class that defines what all question types need
to do. The specific question types then provide the details. This lets the
quiz handle different question types in the same way.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import ClassVar

from . import validation
from .errors import DataError


@dataclass(frozen=True)
class Question(ABC):
    """A quiz question that once loaded, it cannot be changed."""

    question_id: str
    category: str
    prompt: str
    answer: str
    explanation: str = ""

    @property
    def options(self) -> tuple[str, ...]:
        """The possible options the user can choose from. Empty for typed questions."""
        return ()

    @abstractmethod
    def check(self, given: object) -> validation.Check:
        """Check that an answer is usable and valid before it is marked."""

    def is_correct(self, given: object) -> bool:
        """Mark an answer against the stored one."""
        return validation.answers_match(given, self.answer)

    @classmethod
    def from_row(cls, row: dict) -> "Question":
        """Create the approporiate question type from a row in the CSV file.

        Args:
            row: A row read from the question CSV file.

        Returns:
            Question: A MultipleChoiceQuestion or a NumericQuestion.

        Raises:
            DataError: If the row contains invalid data.

        """
        result = validation.check_question_row(row)
        if not result.ok:
            raise DataError(result.message)

        fields = {
            "question_id": str(row["id"]).strip(),
            "category": str(row["category"]).strip(),
            "prompt": str(row["prompt"]).strip(),
            "answer": str(row["answer"]).strip(),
            "explanation": str(row.get("explanation") or "").strip(),
        }
        if str(row["type"]).strip().lower() == "multiple_choice":
            return MultipleChoiceQuestion(
                choices=validation.split_options(row.get("options")), **fields
            )
        return NumericQuestion(**fields)


@dataclass(frozen=True)
class MultipleChoiceQuestion(Question):
    """A question answered by picking one of the several options given."""

    choices: tuple[str, ...] = ()

    @property
    def options(self) -> tuple[str, ...]:
        """The options that are shown."""
        return self.choices

    def check(self, given: object) -> validation.Check:
        """Check that the option picked is one of those offered."""
        return validation.check_chosen_option(given, self.choices)


@dataclass(frozen=True)
class NumericQuestion(Question):
    """A question which is answered by typing a number, such as x = 5."""

    def check(self, given: object) -> validation.Check:
        """Check that the answer which is typed is a number."""
        return validation.check_typed_answer(given)


@dataclass(frozen=True)
class Attempt:
    """One finished attempt, which is saved to the results file."""

    attempt_id: str
    name: str
    category: str
    timestamp: str
    asked: int
    correct: int
    percentage: float
    grade: str
    seconds: int = 0

    #: Keep the columns in the same order when reading and writing the results file.
    COLUMNS: ClassVar[tuple[str, ...]] = (
        "attempt_id", "name", "category", "timestamp",
        "asked", "correct", "percentage", "grade", "seconds",
    )

    def to_row(self) -> dict[str, str]:
        """Convert this attempt into a row for the results file."""
        return {
            "attempt_id": self.attempt_id,
            "name": self.name,
            "category": self.category,
            "timestamp": self.timestamp,
            "asked": str(self.asked),
            "correct": str(self.correct),
            "percentage": f"{self.percentage:.1f}",
            "grade": self.grade,
            "seconds": str(self.seconds),
        }

    @classmethod
    def from_row(cls, row: dict) -> "Attempt":
        """Create an attempt from a row in the results file.

        Args:
            row: A row from the results file.

        Returns:
            Attempt: The attempt created from the row.

        Raises:
            ValueError: If a value is missing or cannot be convereted.
            Storage handles this so a bad row does not stop the other rows
            from being loaded.


        """
        try:
            return cls(
                attempt_id=str(row["attempt_id"]).strip(),
                name=str(row["name"]).strip(),
                category=str(row["category"]).strip(),
                timestamp=str(row["timestamp"]).strip(),
                asked=int(row["asked"]),
                correct=int(row["correct"]),
                percentage=float(row["percentage"]),
                grade=str(row["grade"]).strip(),
                seconds=int(row["seconds"]),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"Damaged results row: {error}") from error


def now_timestamp() -> str:
    """Return the current UTC time as a timestamp."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
