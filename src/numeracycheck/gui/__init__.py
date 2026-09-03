"""Tkinter presentation layer.

This subpackage is the only part of the application that imports ``tkinter``.
Keeping it isolated means the automated tests, which run headless in
continuous integration, never need a display server.
"""
