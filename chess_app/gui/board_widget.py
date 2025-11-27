"""Board widget for chess GUI.

This module provides a dedicated widget for rendering a chessboard
based on FEN (Forsyth-Edwards Notation) strings.
"""

from typing import Optional, Collection
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, QRect, QSize, Signal
from PySide6.QtGui import QPaintEvent, QPainter, QColor, QFont, QMouseEvent


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
    
    Signals:
        square_clicked: Emitted when a square is clicked. Parameters are:
                       - square (str): Algebraic notation (e.g., "e4")
                       - button (Qt.MouseButton): The mouse button used
    
    Attributes:
        _fen: The current full FEN string.
        _board: An 8×8 list structure where each element is either None (empty)
                or a dict with "piece" and "color" keys. Board orientation is
                fixed with white at the bottom (rank 1 at index 7, rank 8 at index 0).
        _selected_square: The currently selected square in algebraic notation, or None.
        _highlighted_squares: Set of squares to highlight in algebraic notation.
    """
    
    # Qt signal: emitted when a square is clicked
    square_clicked = Signal(str, Qt.MouseButton)
    
    def __init__(self):
        """Initialize the BoardWidget with an empty 8×8 board."""
        super().__init__()
        
        # Initialize with empty board (8×8 grid)
        self._fen: str = ""
        self._board: list[list[Optional[dict]]] = [
            [None for _ in range(8)] for _ in range(8)
        ]
        
        # Mouse interaction and highlighting state
        self._selected_square: Optional[str] = None
        self._highlighted_squares: set[str] = set()
    
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
    
    def set_selected_square(self, square: Optional[str]) -> None:
        """Set the currently selected square for visual highlighting.
        
        Updates the internal selected square state and triggers a repaint
        to show the selection overlay. Pass None to clear the selection.
        
        Args:
            square: Algebraic square notation (e.g., "e4") or None to clear.
        
        Example:
            widget.set_selected_square("e2")  # Highlight e2
            widget.set_selected_square(None)  # Clear selection
        """
        self._selected_square = square
        self.update()
    
    def set_highlighted_squares(self, squares: Collection[str]) -> None:
        """Set the squares to highlight as potential move destinations.
        
        Updates the internal highlighted squares state and triggers a repaint
        to show the highlight overlays. Pass an empty collection to clear
        all highlights.
        
        Args:
            squares: Collection of algebraic square notations (e.g., ["e4", "e3"]).
        
        Example:
            widget.set_highlighted_squares(["e4", "e3", "d3"])
            widget.set_highlighted_squares([])  # Clear highlights
        """
        self._highlighted_squares = set(squares)
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
    
    def _pixel_to_square(self, x: int, y: int) -> Optional[str]:
        """Convert pixel coordinates to algebraic square notation.
        
        Maps a click position (in widget coordinates) to a chess square
        in algebraic notation (e.g., "e4"). Returns None if the coordinates
        are outside the board area.
        
        Args:
            x: X-coordinate in widget pixels.
            y: Y-coordinate in widget pixels.
        
        Returns:
            Algebraic square notation (e.g., "a1", "h8") if within the board,
            None if outside the board area.
        
        Example:
            # Click in bottom-left square
            square = widget._pixel_to_square(10, 470)  # Returns "a1"
            
            # Click outside board
            square = widget._pixel_to_square(500, 500)  # Returns None
        """
        # Get current layout
        width = self.width()
        height = self.height()
        square_size, x_margin, y_margin = self._calculate_layout(width, height)
        
        # Adjust coordinates relative to board origin
        board_x = x - x_margin
        board_y = y - y_margin
        
        # Check if click is outside the board area
        board_size = square_size * 8
        if board_x < 0 or board_x >= board_size or board_y < 0 or board_y >= board_size:
            return None
        
        # Convert to file/rank indices (0-7)
        file_idx = board_x // square_size
        rank_idx = board_y // square_size
        
        # Ensure indices are in valid range (defensive check)
        if not (0 <= file_idx < 8 and 0 <= rank_idx < 8):
            return None
        
        # Convert to algebraic notation
        # File: 0-7 → 'a'-'h'
        file_char = chr(ord('a') + file_idx)
        
        # Rank: board index 0-7 → chess rank '8'-'1'
        # (board index 0 = rank 8, board index 7 = rank 1)
        rank_char = str(8 - rank_idx)
        
        return file_char + rank_char
    
    def _square_to_rect(self, square: str, square_size: int, x_margin: int, y_margin: int) -> Optional[QRect]:
        """Convert algebraic square notation to pixel rectangle.
        
        Maps a chess square in algebraic notation to its pixel rectangle
        for rendering. Returns None if the square notation is invalid.
        
        Args:
            square: Algebraic square notation (e.g., "e4").
            square_size: Size of each square in pixels.
            x_margin: Horizontal offset to board origin.
            y_margin: Vertical offset to board origin.
        
        Returns:
            QRect representing the square's pixel bounds, or None if invalid.
        """
        if len(square) != 2:
            return None
        
        file_char = square[0]
        rank_char = square[1]
        
        # Validate and convert file ('a'-'h' → 0-7)
        if not ('a' <= file_char <= 'h'):
            return None
        file_idx = ord(file_char) - ord('a')
        
        # Validate and convert rank ('1'-'8' → board index 7-0)
        if not ('1' <= rank_char <= '8'):
            return None
        rank_number = int(rank_char)
        rank_idx = 8 - rank_number  # rank 8 → index 0, rank 1 → index 7
        
        # Calculate pixel position
        x = x_margin + file_idx * square_size
        y = y_margin + rank_idx * square_size
        
        return QRect(x, y, square_size, square_size)
    
    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events to detect square clicks.
        
        Converts the click position to a chess square and emits the
        square_clicked signal with the square name and button used.
        Ignores clicks outside the board area.
        
        Args:
            event: The mouse press event containing position and button information.
        """
        # Get click position
        x = event.position().x()
        y = event.position().y()
        
        # Convert to square notation
        square = self._pixel_to_square(int(x), int(y))
        
        # Emit signal if click was on a valid square
        if square is not None:
            self.square_clicked.emit(square, event.button())
    
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
        
        # Draw selection and highlight overlays
        # These are drawn after the board but before pieces for proper layering
        
        # Draw highlighted destination squares (semi-transparent blue/cyan)
        if self._highlighted_squares:
            highlight_color = QColor(0, 150, 255, 80)
            for square in self._highlighted_squares:
                rect = self._square_to_rect(square, square_size, x_margin, y_margin)
                if rect is not None:
                    painter.fillRect(rect, highlight_color)
        
        # Draw selected square overlay (semi-transparent yellow)
        if self._selected_square is not None:
            selection_color = QColor(255, 255, 0, 100)
            rect = self._square_to_rect(self._selected_square, square_size, x_margin, y_margin)
            if rect is not None:
                painter.fillRect(rect, selection_color)
        
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

