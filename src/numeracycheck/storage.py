"""Deals with loading and saving the questions and results.

The file handling is also kept here so the rest of the app does not
have to deal with it. This means the way the data is stored can be changed later
without affecting the rest of the app.
"""

from __future__ import annotations

import csv
import logging
import random
from pathlib import Path
from typing import Iterable, Sequence

from .errors import DataError
from .models import Attempt, Question

logger = logging.getLogger(__name__)

ALL_CATEGORIES = "All categories"


class QuestionBank:
    """The questions loaded from the CSV file."""

    def __init__(self, questions: Sequence[Question], skipped: Sequence[str] = ()) -> None:
        """Store the questions that have passed the checks.

        Args:
            questions: questions to add to the bank.
            skipped: Messages for rows that could not be used.

        Raises:
            DataError: If there are no valid questions.

        """
        if not questions:
            raise DataError("The question bank is empty. Check data/questions.csv.")
        self.questions = tuple(questions)
        self.skipped = tuple(skipped)

    def __len__(self) -> int:
        """How many questions were loaded."""
        return len(self.questions)

    @classmethod
    def from_csv(cls, path: str | Path) -> "QuestionBank":
        """Load questions from a CSV file.

        Invalid rows are skipped this means that one wrong rowdoes not stop
        the rest of the questions from loading.

        Args:
            path: Where the question file is.

        Returns:
            QuestionBank: A question bank containing the valid questions.

        Raises:
            DataError: If the file is missing, has the wrong columns or contains
            no valid questions.

        """
        path = Path(path)
        questions: list[Question] = []
        skipped: list[str] = []
        try:
            with path.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                if not reader.fieldnames:
                    raise DataError(f"{path} has no column headings.")
                for line, row in enumerate(reader, start=2):
                    try:
                        questions.append(Question.from_row(row))
                    except DataError as error:
                        message = f"Row {line} skipped: {error}"
                        logger.warning(message)
                        skipped.append(message)
        except FileNotFoundError as error:
            raise DataError(f"Question file not found at {path}.") from error
        except OSError as error:
            raise DataError(f"Could not read {path}: {error}") from error
        return cls(questions, skipped)

    def categories(self) -> tuple[str, ...]:
        """Return the topics available, with "All categories" first."""
        names = sorted({question.category for question in self.questions})
        return (ALL_CATEGORIES, *names)

    def for_category(self, category: str | None = None) -> tuple[Question, ...]:
        """Return the questions in one topic, or all of them."""
        if not category or category == ALL_CATEGORIES:
            return self.questions
        wanted = category.strip().lower()
        return tuple(q for q in self.questions if q.category.lower() == wanted)

    def pick(self, count: int, category: str | None = None,
             rng: random.Random | None = None) -> tuple[Question, ...]:
        """Pick questions at random for one attempt.

        The random number generator is passed in so tests can use a fixed one and get the
        same results each time.

        Args:
            count: Number of questions to pick.
            category: Optional category to pick questions from.
            rng: The random number generator to use.

        Returns:
            tuple[Question, ...]: The selected questions that has no duplicates.

        Raises:
            DataError: If the count is not positive or there are too few
                questions in that topic.

        """
        if count <= 0:
            raise DataError("Choose at least one question.")
        pool = self.for_category(category)
        if len(pool) < count:
            raise DataError(
                f"Only {len(pool)} question(s) available in "
                f"'{category or ALL_CATEGORIES}' but {count} were asked for."
            )
        return tuple((rng or random.Random()).sample(list(pool), count))


class ResultsStore:
    """Saves finished attempts to a CSV file and loads them when needed."""

    def __init__(self, path: str | Path) -> None:
        """Keep track of where the results file is without accessing it yet."""
        self.path = Path(path)

    def save(self, attempt: Attempt) -> None:
        """Add one finished attempt to the results file.

        Args:
            attempt: The completed attempt to save.

        Raises:
            DataError: If the file cannot be written, for example if it is
            open in Excel.

        """
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            exists = self.path.exists() and self.path.stat().st_size > 0
            with self.path.open("a", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=Attempt.COLUMNS)
                if not exists:
                    writer.writeheader()
                writer.writerow(attempt.to_row())
        except PermissionError as error:
            raise DataError(
                f"Cannot write to {self.path}. Close the file in Excel and try again."
            ) from error
        except OSError as error:
            raise DataError(f"Could not save results: {error}") from error

    def load_all(self) -> tuple[Attempt, ...]:
        """Load all saved attempts.

        If the results file does not exist yet, it will return an empty history.
        Any damaged rows are skipped.

        Returns:
            tuple[Attempt, ...]: Saved attempts with the oldest first.

        Raises:
            DataError: If the file exists but it cannot be read.

        """
        if not self.path.exists():
            return ()
        attempts: list[Attempt] = []
        try:
            with self.path.open(encoding="utf-8-sig", newline="") as handle:
                for line, row in enumerate(csv.DictReader(handle), start=2):
                    try:
                        attempts.append(Attempt.from_row(row))
                    except ValueError as error:
                        logger.warning("Skipping results row %s: %s", line, error)
        except OSError as error:
            raise DataError(f"Could not read results: {error}") from error
        return tuple(attempts)

    def export(self, destination: str | Path,
               attempts: Sequence[Attempt] | None = None) -> int:
        """Save the attempts to a file.

        Args:
            destination: Where to save the file.
            attempts: Which attempts to save and saves all attempts by default

        Returns:
            int: The number of rows that were written.

        Raises:
            DataError: If the file cannot be written.

        """
        rows = tuple(attempts) if attempts is not None else self.load_all()
        destination = Path(destination)
        try:
            with destination.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=Attempt.COLUMNS)
                writer.writeheader()
                writer.writerows(attempt.to_row() for attempt in rows)
        except OSError as error:
            raise DataError(f"Could not export results: {error}") from error
        return len(rows)


def filter_by_name(attempts: Iterable[Attempt], name: str) -> tuple[Attempt, ...]:
    """Return the attempts that match a given name.

    Args:
        attempts: The attempts to search through and filter.
        name: The name that needs to match. If no name is given then all attempts are returned.

    Returns:
        tuple[Attempt, ...]: The matching attempts.

    """
    wanted = (name or "").strip().lower()
    if not wanted:
        return tuple(attempts)
    return tuple(a for a in attempts if a.name.strip().lower() == wanted)
