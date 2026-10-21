"""Reconstruct irregular spreadsheet tables using explicit spatial cell rules."""

from .core import Cell, CellGrid, Coordinate, GridError, MissingPolicy

__version__ = "0.1.0"
__all__ = ["Cell", "CellGrid", "Coordinate", "GridError", "MissingPolicy"]
