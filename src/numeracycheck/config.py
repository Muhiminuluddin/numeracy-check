"""File paths used by the app.

These can be changed using environment variables, so the app can use a different or shared
question file without me needing to change the code.
"""

from __future__ import annotations

import os
from pathlib import Path

# Where the data is stored.
# Both can be redirected to somewhere else using an environment variable so that the program
# could read the question file from a network drive.
ROOT = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("NUMERACYCHECK_DATA", ROOT / "data"))
QUESTIONS_PATH = Path(os.environ.get("QUESTIONS_PATH", DATA / "questions.csv"))
RESULTS_PATH = Path(os.environ.get("RESULTS_PATH", DATA / "results.csv"))

#The message from the window and the size of the window.
APP_NAME = "NumeracyCheck"
APP_TAGLINE = "Numeracy check for consulting teams"
WINDOW_SIZE = "760x560"

# Quiz length. The minimum number that will produce a significant percent is three,
# while the maximum number per topic is twenty.
DEFAULT_QUESTIONS = 8
MIN_QUESTIONS = 3
MAX_QUESTIONS = 20
