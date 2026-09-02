"""Custom errors used by the application.

These errors let the app handle expected problems without hiding
actual programming errors that need to be fixed.
"""


class QuizError(Exception):
    """Base class for errors raised intentionally by the quiz application."""


class DataError(QuizError):
    """Raised when a question or results file could not be read, written or understood."""


class QuizStateError(QuizError):
    """Raised when a quiz is used in the wrong order, such as scoring before finishing."""
