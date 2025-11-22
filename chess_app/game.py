"""
Core domain types for the chess game model.

This module defines domain-level abstractions for the chess game,
including game status, move representation, and custom exceptions.
The python-chess library types remain internal to this module and
are not exposed to the rest of the application.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class GameStatus(Enum):
    """Represents the current state of a chess game.
    
    Attributes:
        ONGOING: The game is in progress with no special conditions.
        CHECK: The current player's king is under attack.
        CHECKMATE: The current player's king is in checkmate (game over).
        STALEMATE: The current player has no legal moves but is not in check (draw).
        DRAW_50_MOVE: Game is drawn due to the fifty-move rule.
        DRAW_INSUFFICIENT_MATERIAL: Game is drawn due to insufficient mating material.
        DRAW_OTHER: Game is drawn for other reasons (e.g., threefold repetition, agreement).
    """
    ONGOING = "ongoing"
    CHECK = "check"
    CHECKMATE = "checkmate"
    STALEMATE = "stalemate"
    DRAW_50_MOVE = "draw_50_move"
    DRAW_INSUFFICIENT_MATERIAL = "draw_insufficient_material"
    DRAW_OTHER = "draw_other"


@dataclass
class Move:
    """
    Data transfer object representing a chess move.
    
    This class wraps move information from the python-chess library,
    providing a clean domain-level interface for move representation.
    
    Attributes:
        uci: The move in UCI (Universal Chess Interface) notation (e.g., "e2e4").
        san: The move in SAN (Standard Algebraic Notation), if available (e.g., "e4").
        from_square: The starting square in algebraic notation (e.g., "e2").
        to_square: The destination square in algebraic notation (e.g., "e4").
        promotion: The piece to promote to, if this is a pawn promotion move
                  (e.g., "q" for queen, "r" for rook, etc.). None otherwise.
    """
    uci: str
    san: Optional[str]
    from_square: str
    to_square: str
    promotion: Optional[str] = None


class IllegalMoveError(Exception):
    """
    Exception raised when an illegal chess move is attempted.
    
    This is raised when a move violates chess rules or is not valid
    in the current game position.
    """
    pass


class InvalidFenError(Exception):
    """
    Exception raised when an invalid FEN (Forsyth-Edwards Notation) string is provided.
    
    This is raised when attempting to initialize or set a game position
    from a malformed or invalid FEN string.
    """
    pass


class InvalidPgnError(Exception):
    """
    Exception raised when an invalid PGN (Portable Game Notation) string is provided.
    
    This is raised when attempting to parse or import a game from
    a malformed or invalid PGN string.
    """
    pass
