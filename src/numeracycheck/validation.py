"""These are the rules that I have added that decide if an answer is valid and correct.

Every function here is a **pure function** this means it uses the
values it is given, so the input always matches the result.
That is what allows it to be quick to test.
"""

from __future__ import annotations

import re
from typing import NamedTuple

#: Answers are compared with this tolerance I have added so a rounded decimal
# still passes.
TOLERANCE = 1e-6

#: Score needed for the types of bands that someone might achieve.
DISTINCTION = 80.0
PASS = 60.0

#: Must start with a letter and only letters, spaces, hyphens and apostrophes can be used.
NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z'\- ]*$")

QUESTION_COLUMNS = ("id", "category", "type", "prompt", "options", "answer")
QUESTION_TYPES = ("multiple_choice", "numeric")


class Check(NamedTuple):
    """The result of the check includes whether it passed and if it failed it says why."""

    ok: bool
    message: str


def validate_name(name: object) -> Check:
    """Check the name typed on the start screen.

    Args:
        name: The value from the name box.

    Returns:
        Check: Valid for 2 to 40 letters, spaces, hyphens or apostrophes.

    """
    if not isinstance(name, str) or not name.strip():
        return Check(False, "Please enter your name before starting.")
    cleaned = name.strip()
    if len(cleaned) < 2:
        return Check(False, "Name must be at least 2 characters long.")
    if len(cleaned) > 40:
        return Check(False, "Name must be 40 characters or fewer.")
    if not NAME_PATTERN.match(cleaned):
        return Check(False, "Name can only contain letters, spaces, hyphens and apostrophes.")
    return Check(True, "")


def clean_answer(raw: object) -> str:
    """Fix an answer so two ways of writing the same thing look the same.

    Removes spaces, lowercases and removes commas, so " 29 ", "29" and "1,009"
    all come out in one form.

    Args:
        raw: The value entered by the user.

    Returns:
        str: The tidied answer, or an empty string if it is not able to be used.

    """
    if not isinstance(raw, str):
        return ""
    return " ".join(raw.strip().lower().replace(",", "").split())


def to_number(raw: object) -> float | None:
    """Turn an answer into a number where possible.

    Args:
        raw: The value entered by the user.

    Returns:
        A float if the answer is a number, or None if it is not.

    """
    try:
        return float(clean_answer(raw))
    except ValueError:
        return None


def check_typed_answer(raw: object) -> Check:
    """Check that a typed answer box contains a usable number."""
    if clean_answer(raw) == "":
        return Check(False, "Please enter an answer before submitting.")
    if to_number(raw) is None:
        return Check(False, "Answer must be a number, for example 42 or -2.5.")
    return Check(True, "")


def check_chosen_option(choice: object, options: tuple) -> Check:
    """Check that a selected option is one of those on screen.

    Args:
        choice: The option the user selected.
        options: The options shown for this question.

    Returns:
        Check: Valid when the choice matches one of the options.

    """
    if not isinstance(choice, str) or not choice.strip():
        return Check(False, "Please select an option before submitting.")
    if clean_answer(choice) not in {clean_answer(option) for option in options}:
        return Check(False, "Please select one of the options shown.")
    return Check(True, "")


def answers_match(given: object, correct: object) -> bool:
    """Check if the user's answer matches the correct answer.

    Numbers are compared as numbers, so "29" and "29.0" are treated as the same.
    Anything else is compared as text, which covers answers like "2x2x3x5".

    Args:
        given: The answer that was entered by the user.
        correct: The correct answer.

    Returns:
        bool: True if the answer is correct, otherwise False.

    """
    given_number = to_number(given)
    correct_number = to_number(correct)
    if given_number is not None and correct_number is not None:
        return abs(given_number - correct_number) <= TOLERANCE

    given_text = clean_answer(given).replace(" ", "")
    correct_text = clean_answer(correct).replace(" ", "")
    if given_text == "":
        return False
    return given_text == correct_text


def score_percentage(correct: int, total: int) -> float:
    """Turn a raw score into a percentage, rounded to one decimal place.

    Args:
        correct: How many questions did the user manage to answer correctly.
        total: The total number of questions asked.

    Returns:
        float: The percentage, or 0.0 when no questions were asked.

    Raises:
        ValueError: If the numbers are negative or the amount of
        correct answers is above total number of questions..

    """
    if correct < 0 or total < 0:
        raise ValueError("Scores cannot be negative.")
    if correct > total:
        raise ValueError("Correct answers cannot exceed the number of questions.")
    return round(correct / total * 100, 1) if total else 0.0


def grade_for_score(percentage: float) -> str:
    """Turn a percentage into the band shown to the user.

    Args:
        percentage: A score between 0 and 100.

    Returns:
        str: "Distinction", "Pass" or "Refer for support".

    Raises:
        ValueError: If the percentage is outside 0 to 100.

    """
    if not 0 <= percentage <= 100:
        raise ValueError("Percentage must be between 0 and 100.")
    if percentage >= DISTINCTION:
        return "Distinction"
    return "Pass" if percentage >= PASS else "Refer for support"


def format_duration(seconds: float) -> str:
    """Format a number of seconds as minutes and seconds, such as 01:35."""
    total = max(0, int(round(seconds)))
    return f"{total // 60:02d}:{total % 60:02d}"


def split_options(raw: object) -> tuple[str, ...]:
    """Split the options cell, such as "26|36|46", into separate options."""
    if not isinstance(raw, str):
        return ()
    return tuple(part.strip() for part in raw.split("|") if part.strip())


def check_question_row(row: object) -> Check:
    """Validate a single question row before it is used.

    Question data is edited in Excel by different people, so we validate each row
    instead of assuming the data is correct.

    Args:
        row: A row read from the CSV file.

    Returns:
        Check: Valid  when all required fields are filled in,
        the question type is supported and multiple choice questions
        have at least two options including the correct answer.




    """
    if not isinstance(row, dict):
        return Check(False, "Question row must be a set of columns.")
    for column in QUESTION_COLUMNS:
        if column not in row:
            return Check(False, f"Missing column '{column}'.")
    for column in ("id", "category", "type", "prompt", "answer"):
        if not str(row.get(column) or "").strip():
            return Check(False, f"Column '{column}' must not be empty.")

    kind = str(row["type"]).strip().lower()
    if kind not in QUESTION_TYPES:
        return Check(False, f"Unsupported question type '{kind}'.")

    if kind == "multiple_choice":
        options = split_options(row.get("options"))
        if len(options) < 2:
            return Check(False, "Multiple-choice questions need at least two options.")
        if not any(answers_match(option, row["answer"]) for option in options):
            return Check(False, "The stated answer is not one of the options offered.")
    elif to_number(row["answer"]) is None:
        return Check(False, "Numeric questions need a numeric answer.")
    return Check(True, "")
