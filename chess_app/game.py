"""
Core domain types for the chess game model.

This module defines domain-level abstractions for the chess game,
including game status, move representation, and custom exceptions.
The python-chess library types remain internal to this module and
are not exposed to the rest of the application.
"""

import chess
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union


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


class Game:
    """
    Core game state manager and entry point for UI interaction with chess logic.
    
    This class serves as a thin wrapper around python-chess.Board, providing a clean
    domain-level interface for the UI layer. It encapsulates the chess board state
    and maintains a history of moves using domain Move objects.
    
    The Game class is the primary interface for the UI to interact with game state.
    Internal python-chess types (chess.Board, chess.Move, etc.) are NOT exposed
    directly to other parts of the application - all interactions should go through
    this Game class and its domain types.
    
    Attributes:
        _board: The internal python-chess Board instance that manages chess rules
                and position state. This is kept private and not exposed to callers.
        _move_history: A list of domain Move objects representing all moves made
                      in this game. Starts empty and will be populated as moves
                      are applied (in future implementations).
    
    Example:
        # Create a new game with standard starting position
        game = Game()
        
        # Create a game from a specific position
        game = Game.from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
    """
    
    def __init__(self) -> None:
        """
        Initialize a new chess game with the standard starting position.
        
        Creates a new game with pieces arranged in the traditional chess
        opening position (all pieces on their starting squares, white to move).
        The move history starts empty.
        """
        self._board: chess.Board = chess.Board()
        self._move_history: list[Move] = []
    
    @classmethod
    def from_fen(cls, fen: str) -> "Game":
        """
        Create a Game instance from a FEN (Forsyth-Edwards Notation) string.
        
        FEN is a standard notation for describing a chess position. This method
        constructs a Game with the board position specified by the FEN string.
        The move history starts empty regardless of the position.
        
        Args:
            fen: A valid FEN string representing the chess position. This should
                 include all six FEN fields: piece placement, active color,
                 castling rights, en passant square, halfmove clock, and
                 fullmove number.
        
        Returns:
            A new Game instance with the board position set according to the
            provided FEN string.
        
        Raises:
            InvalidFenError: If the provided FEN string is malformed or invalid.
                            The exception message will include details about
                            what was wrong with the FEN string.
        
        Example:
            # Standard starting position
            game = Game.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            
            # Position after 1.e4
            game = Game.from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
        """
        try:
            board = chess.Board(fen=fen)
        except ValueError as e:
            raise InvalidFenError(
                f"Invalid FEN string provided: '{fen}'. "
                f"Error details: {str(e)}"
            ) from e
        
        # Create a new Game instance and set its internal state
        game = cls.__new__(cls)
        game._board = board
        game._move_history = []
        return game
    
    def get_legal_moves(self) -> list[Move]:
        """
        Get all legal moves in the current position.
        
        Queries the underlying python-chess Board for all legal moves and converts
        them into domain Move objects suitable for UI consumption.
        
        Returns:
            A list of Move instances representing all legal moves in the current
            position. Each Move includes UCI notation, SAN notation, from/to squares,
            and promotion information where applicable.
        
        Example:
            game = Game()
            legal_moves = game.get_legal_moves()
            for move in legal_moves:
                print(f"{move.san}: {move.uci}")
        """
        moves = []
        for chess_move in self._board.legal_moves:
            # Convert python-chess move to domain Move
            uci = chess_move.uci()
            san = self._board.san(chess_move)
            from_square = chess.square_name(chess_move.from_square)
            to_square = chess.square_name(chess_move.to_square)
            
            # Handle promotion
            promotion = None
            if chess_move.promotion is not None:
                promotion = chess.piece_symbol(chess_move.promotion)
            
            moves.append(Move(
                uci=uci,
                san=san,
                from_square=from_square,
                to_square=to_square,
                promotion=promotion
            ))
        
        return moves
    
    def apply_move(self, move: Union[Move, str]) -> None:
        """
        Apply a move to the game.
        
        Accepts either a domain Move object or a UCI string, validates the move
        is legal in the current position, and applies it to the board. The move
        is added to the internal move history.
        
        Args:
            move: Either a domain Move object or a UCI string (e.g., "e2e4" or "e7e8q"
                 for promotion moves).
        
        Raises:
            IllegalMoveError: If the move is not legal in the current position or
                            cannot be parsed as a valid UCI move.
        
        Example:
            game = Game()
            # Apply using UCI string
            game.apply_move("e2e4")
            # Apply using Move object
            moves = game.get_legal_moves()
            game.apply_move(moves[0])
        """
        # Extract UCI string from Move object or use string directly
        if isinstance(move, Move):
            uci_str = move.uci
        else:
            uci_str = move
        
        # Parse UCI string to python-chess move
        try:
            chess_move = chess.Move.from_uci(uci_str)
        except ValueError as e:
            raise IllegalMoveError(
                f"Invalid UCI move string: '{uci_str}'. "
                f"Error details: {str(e)}"
            ) from e
        
        # Validate the move is legal
        if chess_move not in self._board.legal_moves:
            raise IllegalMoveError(
                f"Move '{uci_str}' is not legal in the current position. "
                f"Current FEN: {self._board.fen()}"
            )
        
        # Generate SAN before pushing the move (board state will change)
        san = self._board.san(chess_move)
        
        # Apply the move to the board
        self._board.push(chess_move)
        
        # Create domain Move and add to history
        from_square = chess.square_name(chess_move.from_square)
        to_square = chess.square_name(chess_move.to_square)
        promotion = None
        if chess_move.promotion is not None:
            promotion = chess.piece_symbol(chess_move.promotion)
        
        domain_move = Move(
            uci=uci_str,
            san=san,
            from_square=from_square,
            to_square=to_square,
            promotion=promotion
        )
        self._move_history.append(domain_move)
    
    def undo(self) -> None:
        """
        Undo the last move.
        
        Reverts the board state to before the last move was applied and removes
        that move from the move history. Safe to call repeatedly until reaching
        the initial position.
        
        If there are no moves to undo (history is empty), this method does nothing
        (no-op behavior).
        
        Example:
            game = Game()
            game.apply_move("e2e4")
            game.apply_move("e7e5")
            game.undo()  # Reverts e7e5
            game.undo()  # Reverts e2e4
            game.undo()  # Safe no-op, already at starting position
        """
        # Check if there are moves to undo
        if len(self._move_history) > 0:
            # Revert the board state
            self._board.pop()
            # Remove the last move from history
            self._move_history.pop()
    
    def get_history(self) -> tuple[Move, ...]:
        """
        Get a read-only view of the move history.
        
        Returns an immutable tuple containing all moves that have been applied
        in this game, in chronological order.
        
        Returns:
            A tuple of Move objects representing the complete move history.
            The tuple is immutable to prevent external modification of the
            game's internal state.
        
        Example:
            game = Game()
            game.apply_move("e2e4")
            game.apply_move("e7e5")
            history = game.get_history()
            print(f"Moves played: {len(history)}")  # Prints: Moves played: 2
            for move in history:
                print(move.san)  # Prints: e4, e5
        """
        return tuple(self._move_history)
