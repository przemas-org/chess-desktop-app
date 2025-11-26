"""Board widget for chess GUI.

This module provides a dedicated widget for rendering a chessboard
based on FEN (Forsyth-Edwards Notation) strings.
"""

from typing import Optional
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPaintEvent


class BoardFenError(Exception):
    """Exception raised when an invalid FEN string is provided to the BoardWidget.
    
    This GUI-layer exception is raised when FEN parsing or validation fails
    in the BoardWidget class.
    """
    pass


class BoardWidget(QWidget):
    """Widget for displaying a chessboard from FEN notation.
    
    This widget maintains an internal 8×8 board representation derived from
    a FEN string and provides a FEN-based API for updating the board state.
    The widget does not depend on Game or python-chess types and operates
    purely at the GUI layer.
    
    Attributes:
        _fen: The current full FEN string.
        _board: An 8×8 list structure where each element is either None (empty)
                or a dict with "piece" and "color" keys. Board orientation is
                fixed with white at the bottom (rank 1 at index 7, rank 8 at index 0).
    """
    
    def __init__(self):
        """Initialize the BoardWidget with an empty 8×8 board."""
        super().__init__()
        
        # Initialize with empty board (8×8 grid)
        self._fen: str = ""
        self._board: list[list[Optional[dict]]] = [
            [None for _ in range(8)] for _ in range(8)
        ]
    
    def set_fen(self, fen: str) -> None:
        """Set the board position from a FEN string.
        
        Parses the piece-placement field of the FEN string and updates the
        internal 8×8 board representation. Validates that the FEN piece-placement
        field expands to exactly 8 ranks with 8 files each.
        
        Args:
            fen: A full FEN string (e.g., "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1").
                 Only the piece-placement field (first field) is used for board representation.
        
        Raises:
            BoardFenError: If the FEN piece-placement field is invalid (wrong number of ranks
                          or files, invalid characters, etc.).
        
        Example:
            widget = BoardWidget()
            widget.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        """
        # Extract piece-placement field (first field before first space)
        piece_placement = fen.split()[0] if ' ' in fen else fen
        
        # Split into ranks
        ranks = piece_placement.split('/')
        
        # Validate exactly 8 ranks
        if len(ranks) != 8:
            raise BoardFenError(
                f"Invalid FEN: expected 8 ranks, got {len(ranks)}. "
                f"FEN piece-placement: '{piece_placement}'"
            )
        
        # Parse each rank (from rank 8 down to rank 1)
        new_board: list[list[Optional[dict]]] = []
        valid_pieces = set('pnbrqkPNBRQK')
        
        for rank_idx, rank_str in enumerate(ranks):
            row: list[Optional[dict]] = []
            
            # Process each character in the rank
            for char in rank_str:
                if char.isdigit():
                    # Expand digit into empty squares
                    empty_count = int(char)
                    row.extend([None] * empty_count)
                elif char in valid_pieces:
                    # Map piece character to descriptor
                    if char.isupper():
                        # Uppercase = white piece
                        row.append({"piece": char.lower(), "color": "white"})
                    else:
                        # Lowercase = black piece
                        row.append({"piece": char, "color": "black"})
                else:
                    raise BoardFenError(
                        f"Invalid character '{char}' in FEN rank {rank_idx + 1}. "
                        f"FEN piece-placement: '{piece_placement}'"
                    )
            
            # Validate exactly 8 files in this rank
            if len(row) != 8:
                raise BoardFenError(
                    f"Invalid FEN: rank {rank_idx + 1} has {len(row)} files, expected 8. "
                    f"Rank string: '{rank_str}'"
                )
            
            new_board.append(row)
        
        # Update internal state
        self._fen = fen
        self._board = new_board
        
        # Trigger repaint
        self.update()
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint event handler (stub implementation).
        
        This is a stub implementation. Actual painting logic will be
        implemented in a future ticket.
        
        Args:
            event: The paint event.
        """
        super().paintEvent(event)

