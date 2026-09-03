"""Main window for the quiz app and controller for switching between screens.

Handles switching between the different screens and
keeping track of the quiz, questions and results.
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import messagebox, ttk

from .. import config
from ..errors import DataError, QuizError
from ..quiz import Quiz
from ..storage import QuestionBank, ResultsStore
from .frames import HistoryFrame, QuizFrame, ResultsFrame, StartFrame

logger = logging.getLogger(__name__)


class QuizApp(tk.Tk):
    """The application window."""

    def __init__(self, questions_path=config.QUESTIONS_PATH,
                 results_path=config.RESULTS_PATH) -> None:
        """Set up the application and load the questions.

        Args:
            questions_path: Where the question file is.
            results_path: Where results are saved.

        """
        super().__init__()
        self.title(f"{config.APP_NAME} - {config.APP_TAGLINE}")
        self.geometry(config.WINDOW_SIZE)
        self.minsize(680, 500)

        self.results = ResultsStore(results_path)
        self.quiz: Quiz | None = None
        self.bank: QuestionBank | None = None

        self._styles()
        self._screens()

        try:
            self.bank = QuestionBank.from_csv(questions_path)
        except DataError as error:
            # Without questions there is no quiz, but the user is told why
            # rather than seeing a wall of red text.
            logger.error("Question bank failed to load: %s", error)
            messagebox.showerror("Questions unavailable", str(error))
            self.after(100, self.destroy)
            return

        if self.bank.skipped:
            messagebox.showwarning(
                "Some questions were skipped",
                "The quiz will still run, but these rows need fixing:\n\n"
                + "\n".join(self.bank.skipped),
            )
        self.show("StartFrame")

    def _styles(self) -> None:
        """Set the fonts and colours used across the screens."""
        style = ttk.Style(self)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Heading.TLabel", font=("Segoe UI", 18, "bold"))
        style.configure("Sub.TLabel", font=("Segoe UI", 10))
        style.configure("Prompt.TLabel", font=("Segoe UI", 14), wraplength=620)
        style.configure("Score.TLabel", font=("Segoe UI", 32, "bold"))
        style.configure("Right.TLabel", foreground="#1a7f37")
        style.configure("Wrong.TLabel", foreground="#b42318")

    def _screens(self) -> None:
        """Create the four screens and stack them in the same place."""
        container = ttk.Frame(self, padding=20)
        container.pack(fill="both", expand=True)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        self.frames: dict[str, ttk.Frame] = {}
        for screen in (StartFrame, QuizFrame, ResultsFrame, HistoryFrame):
            frame = screen(container, self)
            self.frames[screen.__name__] = frame
            frame.grid(row=0, column=0, sticky="nsew")

    def show(self, name: str) -> None:
        """Bring one screen to the front.

        Args:
            name: The screen's class name, such as "QuizFrame".

        """
        frame = self.frames[name]
        if hasattr(frame, "on_show"):
            frame.on_show()
        frame.tkraise()

    def start_quiz(self, name: str, category: str, count: int) -> None:
        """Pick the questions and move to the quiz screen."""
        try:
            self.quiz = Quiz(name, self.bank.pick(count, category), category)
        except (QuizError, ValueError) as error:
            messagebox.showwarning("Cannot start the quiz", str(error))
            return
        self.show("QuizFrame")

    def finish_quiz(self) -> None:
        """Save the finished attempt and show the result."""
        if self.quiz is None:
            return
        try:
            self.results.save(self.quiz.to_attempt())
        except QuizError as error:
            # The score is still shown; only saving failed.
            messagebox.showerror("Results not saved", str(error))
        self.show("ResultsFrame")
