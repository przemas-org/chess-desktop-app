"""Board widget for chess GUI.

This module provides a dedicated widget for rendering a chessboard
based on FEN (Forsyth-Edwards Notation) strings.
"""

from typing import Optional
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect, QSize
from PySide6.QtGui import QPaintEvent, QPainter, QColor, QFont


# Unicode chess piece glyphs mapping
# Maps (piece_type, color) tuples to their Unicode representations
PIECE_UNICODE: dict[tuple[str, str], str] = {
    ("p", "white"): "\u2659",  # ♙ White Pawn
    ("n", "white"): "\u2658",  # ♘ White Knight
    ("b", "white"): "\u2657",  # ♗ White Bishop
    ("r", "white"): "\u2656",  # ♖ White Rook
    ("q", "white"): "\u2655",  # ♕ White Queen
    ("k", "white"): "\u2654",  # ♔ White King
    ("p", "black"): "\u265F",  # ♟ Black Pawn
    ("n", "black"): "\u265E",  # ♞ Black Knight
    ("b", "black"): "\u265D",  # ♝ Black Bishop
    ("r", "black"): "\u265C",  # ♜ Black Rook
    ("q", "black"): "\u265B",  # ♛ Black Queen
    ("k", "black"): "\u265A",  # ♚ Black King
}


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
    
    def sizeHint(self) -> QSize:
        """Provide a size hint for the widget.
        
        Returns a square size hint to encourage square layouts when this
        widget is used as the main window's central widget or in layouts.
        
        Returns:
            A QSize of 480×480 pixels (60 pixels per square × 8 squares).
        """
        return QSize(480, 480)
    
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
    
    def _calculate_layout(self, width: int, height: int) -> tuple[int, int, int]:
        """Calculate board layout parameters for the given widget dimensions.
        
        This method computes the square size and centering margins needed to
        render an 8×8 chessboard within the available space. The board is
        centered within the widget, with any extra space becoming padding.
        
        Args:
            width: Available width in pixels.
            height: Available height in pixels.
        
        Returns:
            A tuple of (square_size, x_margin, y_margin) where:
            - square_size: Size of each square in pixels (integer)
            - x_margin: Horizontal offset to center the board
            - y_margin: Vertical offset to center the board
        
        Example:
            # For a 800×800 widget
            square_size, x_margin, y_margin = self._calculate_layout(800, 800)
            # Returns: (100, 0, 0)
            
            # For a 850×800 widget
            square_size, x_margin, y_margin = self._calculate_layout(850, 800)
            # Returns: (100, 25, 0)
        """
        # Square size is limited by the smaller dimension
        square_size = min(width, height) // 8
        
        # Calculate margins to center the board
        board_width = square_size * 8
        board_height = square_size * 8
        x_margin = (width - board_width) // 2
        y_margin = (height - board_height) // 2
        
        return square_size, x_margin, y_margin
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """Paint the chessboard with pieces using Unicode glyphs.
        
        Renders an 8×8 chessboard with alternating light and dark squares,
        and draws chess pieces as Unicode characters. The board is centered
        within the widget with uniform margins.
        
        Layout:
        - Square size is computed as min(width, height) // 8
        - Board is centered with equal margins on all sides
        - Light squares: #F0D9B5 (classic beige)
        - Dark squares: #B58863 (classic brown)
        - Pieces are rendered in "DejaVu Serif" font at 60% of square size
        
        Board orientation:
        - Rank 8 (black pieces) at top (board index 0)
        - Rank 1 (white pieces) at bottom (board index 7)
        - Files a-h from left to right (board indices 0-7)
        
        Manual verification steps:
        - Run app and load standard starting position
        - Verify white pieces appear at bottom, black at top
        - Verify light/dark square alternation (a1 is dark square)
        - Test window resizing maintains board centering and proportions
        - Verify pieces remain visible at different window sizes
        
        Args:
            event: The paint event.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get widget dimensions and calculate layout
        width = self.width()
        height = self.height()
        square_size, x_margin, y_margin = self._calculate_layout(width, height)
        
        # Define square colors (classic beige/brown)
        light_square = QColor("#F0D9B5")
        dark_square = QColor("#B58863")
        
        # Draw the 8×8 board
        for rank in range(8):
            for file in range(8):
                # Determine square color: (rank + file) % 2 == 0 for light squares
                # Note: In chess, a1 is a dark square (rank=0, file=0 in bottom-left)
                # Our board has rank 0 at top, so we need to adjust
                is_light = (rank + file) % 2 != 0
                color = light_square if is_light else dark_square
                
                # Calculate square position
                x = x_margin + file * square_size
                y = y_margin + rank * square_size
                
                # Draw the square
                painter.fillRect(x, y, square_size, square_size, color)
        
        # Set up font for piece rendering (60% of square size)
        font = QFont("DejaVu Serif")
        font.setPixelSize(int(square_size * 0.6))
        painter.setFont(font)
        
        # Draw pieces
        for rank in range(8):
            for file in range(8):
                piece_data = self._board[rank][file]
                
                if piece_data is not None:
                    # Get the Unicode glyph for this piece
                    piece_key = (piece_data["piece"], piece_data["color"])
                    glyph = PIECE_UNICODE.get(piece_key, "")
                    
                    if glyph:
                        # Calculate square bounds
                        x = x_margin + file * square_size
                        y = y_margin + rank * square_size
                        rect = QRect(x, y, square_size, square_size)
                        
                        # Draw the piece glyph centered in the square
                        painter.drawText(
                            rect,
                            Qt.AlignmentFlag.AlignCenter,
                            glyph
                        )

