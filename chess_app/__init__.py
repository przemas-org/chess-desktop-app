"""Chess Desktop Application

A chess game implementation built on python-chess, providing a clean domain API
for chess game management. The main entry point is the Game class, which offers
methods for move validation, game state management, and import/export functionality.

Example:
    Basic usage of the chess game API:
    
    >>> from chess_app import Game, GameStatus
    >>> game = Game()
    >>> game.apply_move("e2e4")
    >>> status = game.get_status()
    >>> print(status)
    GameStatus.ONGOING
"""

from chess_app.game import (
    Game,
    GameStatus,
    Move,
    IllegalMoveError,
    InvalidFenError,
    InvalidPgnError,
)

__version__ = "0.1.0"

__all__ = [
    "Game",
    "GameStatus",
    "Move",
    "IllegalMoveError",
    "InvalidFenError",
    "InvalidPgnError",
]
