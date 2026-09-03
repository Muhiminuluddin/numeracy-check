"""File paths and limits, all in one place.

Paths can be changed with environment variables so the app can point at a
shared question file without editing the code.
"""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(os.environ.get("NUMERACYCHECK_DATA", ROOT / "data"))
QUESTIONS_PATH = Path(os.environ.get("QUESTIONS_PATH", DATA / "questions.csv"))
RESULTS_PATH = Path(os.environ.get("RESULTS_PATH", DATA / "results.csv"))

APP_NAME = "NumeracyCheck"
APP_TAGLINE = "Numeracy check for consulting teams"
WINDOW_SIZE = "760x560"

DEFAULT_QUESTIONS = 8
MIN_QUESTIONS = 3
MAX_QUESTIONS = 20
