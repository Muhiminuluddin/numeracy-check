"""The different screens used in the app.

Each screen handles a different part of the quiz which could be starting the quiz,
answering questions or checking past results.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .. import config, validation
from ..errors import QuizError
from ..storage import filter_by_name


def button_row(parent: tk.Widget, *buttons) -> ttk.Frame:
    """Create a row of buttons with their labels and actions."""
    row = ttk.Frame(parent)
    row.pack(anchor="w", pady=14)
    for label, command in buttons:
        ttk.Button(row, text=label, command=command).pack(side="left", padx=(0, 10))
    return row


def make_table(parent: tk.Widget, columns: tuple, height: int) -> ttk.Treeview:
    """Create a table using the columns provided.

    Both the results screen and the history screen show a table.
    """
    table = ttk.Treeview(parent, columns=[c[0] for c in columns],
                         show="headings", height=height)
    for name, heading, width in columns:
        table.heading(name, text=heading)
        table.column(name, width=width, anchor="w")
    table.pack(fill="both", expand=True)
    return table


class StartFrame(ttk.Frame):
    """Screen 1: name, topic and how many questions."""

    def __init__(self, parent: tk.Widget, app) -> None:
        """Build the start screen."""
        super().__init__(parent)
        self.app = app
        self.name_var = tk.StringVar()
        self.topic_var = tk.StringVar()
        self.count_var = tk.IntVar(value=config.DEFAULT_QUESTIONS)

        ttk.Label(self, text=config.APP_NAME, style="Heading.TLabel").pack(anchor="w")
        ttk.Label(self, text="Answer a short set of numeracy questions. Your score is "
                             "saved so you can track progress over time.",
                  style="Sub.TLabel", wraplength=620).pack(anchor="w", pady=(4, 20))

        form = ttk.Frame(self)
        form.pack(anchor="w", fill="x")
        ttk.Label(form, text="Your name").grid(row=0, column=0, sticky="w", pady=6)
        ttk.Label(form, text="Topic").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Label(form, text="Questions").grid(row=2, column=0, sticky="w", pady=6)

        self.name_box = ttk.Entry(form, textvariable=self.name_var, width=32)
        self.name_box.grid(row=0, column=1, sticky="w", padx=12)
        self.topic_box = ttk.Combobox(form, textvariable=self.topic_var,
                                      state="readonly", width=30)
        self.topic_box.grid(row=1, column=1, sticky="w", padx=12)
        ttk.Spinbox(form, from_=config.MIN_QUESTIONS, to=config.MAX_QUESTIONS,
                    textvariable=self.count_var, width=6
                    ).grid(row=2, column=1, sticky="w", padx=12)

        self.error = ttk.Label(self, text="", style="Wrong.TLabel")
        self.error.pack(anchor="w", pady=(12, 0))

        button_row(self, ("Start quiz", self.start),
                   ("View past results", lambda: app.show("HistoryFrame")))

    def on_show(self) -> None:
        """Refresh the topic list when the screen opens."""
        if self.app.bank is None:
            return
        self.topic_box["values"] = self.app.bank.categories()
        if not self.topic_var.get():
            self.topic_var.set(self.app.bank.categories()[0])
        self.error.config(text="")
        self.name_box.focus_set()

    def start(self) -> None:
        """Check the form, then ask the app to start a quiz."""
        check = validation.validate_name(self.name_var.get())
        if not check.ok:
            self.error.config(text=check.message)
            return
        try:
            count = int(self.count_var.get())
        except (tk.TclError, ValueError):
            self.error.config(text="Number of questions must be a whole number.")
            return
        if not config.MIN_QUESTIONS <= count <= config.MAX_QUESTIONS:
            self.error.config(text=f"Choose between {config.MIN_QUESTIONS} and "
                                   f"{config.MAX_QUESTIONS} questions.")
            return
        self.error.config(text="")
        self.app.start_quiz(self.name_var.get(), self.topic_var.get(), count)


class QuizFrame(ttk.Frame):
    """Screen 2: one question at a time, with the feedback given straight away."""

    def __init__(self, parent: tk.Widget, app) -> None:
        """Build the quiz screen."""
        super().__init__(parent)
        self.app = app
        self.choice_var = tk.StringVar()
        self.typed_var = tk.StringVar()

        self.progress = ttk.Label(self, text="", style="Sub.TLabel")
        self.progress.pack(anchor="w", pady=(0, 12))
        self.prompt = ttk.Label(self, text="", style="Prompt.TLabel")
        self.prompt.pack(anchor="w", pady=(0, 16))
        self.answer_area = ttk.Frame(self)
        self.answer_area.pack(anchor="w", fill="x")
        self.feedback = ttk.Label(self, text="", wraplength=620)
        self.feedback.pack(anchor="w", pady=16)

        buttons = ttk.Frame(self)
        buttons.pack(anchor="w", pady=8)
        self.submit_button = ttk.Button(buttons, text="Submit answer", command=self.submit)
        self.submit_button.pack(side="left")
        self.next_button = ttk.Button(buttons, text="Next question", state="disabled",
                                      command=self.next_question)
        self.next_button.pack(side="left", padx=10)
        ttk.Button(buttons, text="Quit quiz", command=self.quit_quiz).pack(side="left")

    def on_show(self) -> None:
        """Draw the current question."""
        self.draw()

    def draw(self) -> None:
        """Show the question and the right answer box."""
        quiz = self.app.quiz
        if quiz is None or quiz.finished:
            return
        question = quiz.current
        self.progress.config(text=f"{quiz.progress()} - {question.category}")
        self.prompt.config(text=question.prompt)
        self.feedback.config(text="", style="TLabel")

        for widget in self.answer_area.winfo_children():
            widget.destroy()

        if question.options:
            self.choice_var.set("")
            for option in question.options:
                ttk.Radiobutton(self.answer_area, text=option, value=option,
                                variable=self.choice_var).pack(anchor="w", pady=2)
        else:
            self.typed_var.set("")
            box = ttk.Entry(self.answer_area, textvariable=self.typed_var, width=24)
            box.pack(anchor="w")
            box.bind("<Return>", lambda _event: self.submit())
            box.focus_set()

        self.submit_button.config(state="normal")
        self.next_button.config(state="disabled")

    def submit(self) -> None:
        """Send the answer to the quiz and show the feedback."""
        quiz = self.app.quiz
        if quiz is None or quiz.finished:
            return
        given = self.choice_var.get() if quiz.current.options else self.typed_var.get()
        result = quiz.submit(given)
        self.feedback.config(text=result.message,
                             style="Right.TLabel" if result.correct else "Wrong.TLabel")
        if not result.accepted:
            return
        self.submit_button.config(state="disabled")
        self.next_button.config(state="normal",
                                text="See results" if quiz.finished else "Next question")

    def next_question(self) -> None:
        """Move on, or show the result if that was the last question."""
        if self.app.quiz is None:
            return
        if self.app.quiz.finished:
            self.app.finish_quiz()
        else:
            self.draw()

    def quit_quiz(self) -> None:
        """Give up on the attempt, after checking and without saving a score."""
        if messagebox.askyesno("Quit quiz", "Your answers will not be saved. Quit anyway?"):
            self.app.quiz = None
            self.app.show("StartFrame")


class ResultsFrame(ttk.Frame):
    """Screen 3: the score, the band and a review of every question."""

    COLUMNS = (("q", "Question", 300), ("yours", "Your answer", 110),
               ("right", "Correct answer", 120), ("outcome", "Outcome", 90))

    def __init__(self, parent: tk.Widget, app) -> None:
        """Build the results screen."""
        super().__init__(parent)
        self.app = app

        ttk.Label(self, text="Your result", style="Heading.TLabel").pack(anchor="w")
        self.score = ttk.Label(self, text="", style="Score.TLabel")
        self.score.pack(anchor="w", pady=(8, 0))
        self.detail = ttk.Label(self, text="", style="Sub.TLabel")
        self.detail.pack(anchor="w", pady=(0, 12))
        self.table = make_table(self, self.COLUMNS, height=9)

        button_row(self, ("Take another quiz", lambda: app.show("StartFrame")),
                   ("View past results", lambda: app.show("HistoryFrame")))

    def on_show(self) -> None:
        """Fill in the score and the review table."""
        quiz = self.app.quiz
        if quiz is None:
            return
        self.score.config(text=f"{quiz.percentage():.0f}%")
        self.detail.config(
            text=f"{quiz.name}: {quiz.correct_count} of {len(quiz.questions)} correct "
                 f"- {quiz.grade()} - time taken "
                 f"{validation.format_duration(quiz.seconds_taken())}")
        self.table.delete(*self.table.get_children())
        for answer in quiz.answers:
            self.table.insert("", "end", values=(
                answer.question.prompt, answer.given, answer.question.answer,
                "Correct" if answer.correct else "Incorrect"))


class HistoryFrame(ttk.Frame):
    """Screen 4: shows previous quiz attempts and allows the user to filter and export them."""

    COLUMNS = (("when", "Completed", 170), ("who", "Name", 160),
               ("topic", "Topic", 160), ("score", "Score", 90),
               ("band", "Outcome", 140))

    def __init__(self, parent: tk.Widget, app) -> None:
        """Build the history screen."""
        super().__init__(parent)
        self.app = app
        self.attempts: tuple = ()
        self.filter_var = tk.StringVar()

        ttk.Label(self, text="Past results", style="Heading.TLabel").pack(anchor="w")
        row = ttk.Frame(self)
        row.pack(anchor="w", fill="x", pady=10)
        ttk.Label(row, text="Filter by name").pack(side="left")
        ttk.Entry(row, textvariable=self.filter_var, width=24).pack(side="left", padx=8)
        ttk.Button(row, text="Apply", command=self.refresh).pack(side="left")
        ttk.Button(row, text="Clear", command=self.clear).pack(side="left", padx=8)

        self.table = make_table(self, self.COLUMNS, height=11)
        self.status = ttk.Label(self, text="", style="Sub.TLabel")
        self.status.pack(anchor="w", pady=(10, 0))

        button_row(self, ("Export to CSV", self.export),
                   ("Back", lambda: app.show("StartFrame")))

    def on_show(self) -> None:
        """Reload the results each time the screen is opened."""
        self.refresh()

    def refresh(self) -> None:
        """Load the results, apply the filter and fill the table."""
        try:
            saved = self.app.results.load_all()
        except QuizError as error:
            messagebox.showerror("Could not load results", str(error))
            return
        self.attempts = filter_by_name(saved, self.filter_var.get())
        self.table.delete(*self.table.get_children())
        for attempt in reversed(self.attempts):
            self.table.insert("", "end", values=(
                attempt.timestamp.replace("T", " ").replace("+00:00", ""),
                attempt.name, attempt.category,
                f"{attempt.percentage:.0f}%", attempt.grade))
        if self.attempts:
            self.status.config(text=f"{len(self.attempts)} attempt(s) shown.")
        else:
            self.status.config(text="No attempts saved yet.")

    def clear(self) -> None:
        """Remove the filter and reload."""
        self.filter_var.set("")
        self.refresh()

    def export(self) -> None:
        """Save the rows on screen to a file the user chooses."""
        if not self.attempts:
            messagebox.showinfo("Nothing to export", "There are no results to export.")
            return
        destination = filedialog.asksaveasfilename(
            title="Export results", defaultextension=".csv",
            initialfile="numeracycheck_results.csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not destination:
            return
        try:
            written = self.app.results.export(destination, self.attempts)
        except QuizError as error:
            messagebox.showerror("Export failed", str(error))
            return
        messagebox.showinfo("Export complete", f"{written} row(s) written.")
