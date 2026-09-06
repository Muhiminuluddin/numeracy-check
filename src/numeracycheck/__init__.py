"""NumeracyCheck: a numeracy quiz for consulting teams.

The code is split into separate layers so that the main rules are not linked
to the screens


• ``validation`` contains the main validation functions.
• ``models`` contains the Question and Attempt classes.
• ``storage`` handles reading and writing the CSV files.
• ``quiz`` is responsible for running each quiz attempt.
• ``gui`` is the only part of the application that uses Tkinter.
"""

__version__ = "1.0.0"
