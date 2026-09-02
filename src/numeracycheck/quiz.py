"""Runs one attempt from the start to the finish.

Since this module doesn't rely on Tkinter, you can test the full quiz directly.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from typing import Callable, NamedTuple, Sequence

from . import validation
from .errors import QuizStateError
from .models import Attempt, Question, now_timestamp


class Feedback(NamedTuple):
    """The feedback returned after a user submits an answer.

    If the answer cannot be marked 'accepted' is False.
    This lets the user fix their answer and try the question again.
    """

    accepted: bool
    correct: bool
    message: str


@dataclass(frozen=True)
class Answered:
    """One answered question which is used to build the review table."""

    question: Question
    given: str
    correct: bool


class Quiz:
    """One attempt, including the answers so far and the time taken."""

    def __init__(self, name: str, questions: Sequence[Question],
                 category: str = "All categories",
                 clock: Callable[[], float] = time.monotonic) -> None:
        """Set up the quiz and start the timer.

        Args:
            name: The name entered by the user.
            questions: The questions that will be asked.
            category: The topic chosen for the quiz.
            clock: Used to keep track of time. tests can use a fake clock clock
                so they do not have to wait.

        Raises:
            QuizStateError: If there are no questions.
            ValueError: If the name is not valid.

        """
        if not questions:
            raise QuizStateError("A quiz needs at least one question.")
        check = validation.validate_name(name)
        if not check.ok:
            raise ValueError(check.message)

        self.name = name.strip()
        self.category = category
        self.questions = tuple(questions)
        self.answers: list[Answered] = []
        self.position = 0
        self._clock = clock
        self._started = clock()

    @property
    def current(self) -> Question:
        """The question is waiting to be answered.

        Raises:
            QuizStateError: If the quiz has already been finished.

        """
        if self.finished:
            raise QuizStateError("The quiz has finished.")
        return self.questions[self.position]

    @property
    def finished(self) -> bool:
        """True once every question has been answered."""
        return self.position >= len(self.questions)

    @property
    def correct_count(self) -> int:
        """How many answers were right."""
        return sum(1 for answer in self.answers if answer.correct)

    def progress(self) -> str:
        """Return the caption above the question, such as "Question 3 of 8"."""
        shown = min(self.position + 1, len(self.questions))
        return f"Question {shown} of {len(self.questions)}"

    def submit(self, given: object) -> Feedback:
        """Check and record an answer, then move onto the next question.

        Invalid input is not treated as a wrong answer. Rather if a user
        types letters into a number box they are asked to fix it rather than
        being marked wrong.

        Args:
            given: What the user typed or selected.

        Returns:
            Feedback about whether the answer was accepted and correct.

        Raises:
            QuizStateError: If the quiz is already finished.

        """
        question = self.current
        check = question.check(given)
        if not check.ok:
            return Feedback(False, False, check.message)

        correct = question.is_correct(given)
        self.answers.append(Answered(question, str(given).strip(), correct))
        self.position += 1

        message = "Correct." if correct else f"Not quite. The answer is {question.answer}."
        if question.explanation:
            message = f"{message} {question.explanation}"
        return Feedback(True, correct, message)

    def seconds_taken(self) -> int:
        """How many whole seconds the attempt has taken so far."""
        return int(round(self._clock() - self._started))

    def percentage(self) -> float:
        """Return the score so far as a percentage."""
        return validation.score_percentage(self.correct_count, len(self.questions))

    def grade(self) -> str:
        """Return the outcome band for the current score."""
        return validation.grade_for_score(self.percentage())

    def to_attempt(self, make_id: Callable[[], str] = lambda: uuid.uuid4().hex[:8]) -> Attempt:
        """Create an attempt from the finished quiz so it can be saved.

        Args:
            make_id: Function used to generate the attempt ID.

        Returns:
            The attempt record ready to be saved.

        Raises:
            QuizStateError: If the quiz is not finished.

        """
        if not self.finished:
            raise QuizStateError("Finish every question before saving.")
        return Attempt(
            attempt_id=make_id(),
            name=self.name,
            category=self.category,
            timestamp=now_timestamp(),
            asked=len(self.questions),
            correct=self.correct_count,
            percentage=self.percentage(),
            grade=self.grade(),
            seconds=self.seconds_taken(),
        )
