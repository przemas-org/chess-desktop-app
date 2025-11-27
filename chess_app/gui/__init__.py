"""GUI module for the chess desktop application.

This module provides the PySide6-based graphical user interface.
"""

from chess_app.gui.main_window import MainWindow
from chess_app.gui.board_widget import BoardWidget, BoardFenError
from chess_app.gui.engine_controller import EngineController

__all__ = ["MainWindow", "BoardWidget", "BoardFenError", "EngineController"]

