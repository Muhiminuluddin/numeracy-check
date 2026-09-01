"""NumeracyCheck: a numeracy quiz for consulting teams.

The code is layered so the rules never depend on the screens:

* ``validation`` holds the pure functions.
* ``models`` holds the Question and Attempt classes.
* ``storage`` reads and writes the CSV files.
* ``quiz`` runs one attempt.
* ``gui`` is the only part that uses Tkinter.
"""

__version__ = "1.0.0"
