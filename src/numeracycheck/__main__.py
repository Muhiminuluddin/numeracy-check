"""Entry point so the application can be started with ``python -m``.

Run from the repository root with ``src`` on the import path::

    PYTHONPATH=src python -m numeracycheck

or after ``pip install -e .``, simply::

    python -m numeracycheck
"""

from __future__ import annotations

import logging
import sys


def main() -> int:
    """Start the graphical application.

    Returns:
        int: ``0`` on a clean exit, ``1`` if Tkinter is unavailable.

    """
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    try:
        from .gui.app import QuizApp
    except ImportError as error:  # pragma: no cover - environment specific
        print(
            "Tkinter is not available in this Python installation.\n"
            "On Debian or Ubuntu install it with: sudo apt install python3-tk\n"
            f"Details: {error}",
            file=sys.stderr,
        )
        return 1

    QuizApp().mainloop()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
