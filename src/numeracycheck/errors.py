"""The three errors this application raises on purpose.

Having its own errors means the screens can catch problems the application
knows about, without also hiding real programming mistakes.
"""


class QuizError(Exception):
    """Base class for every error this application raises on purpose."""


class DataError(QuizError):
    """A question or results file could not be read, written or understood."""


class QuizStateError(QuizError):
    """A quiz was used in the wrong order, such as scoring before finishing."""
