"""Main window for the chess desktop application."""

from PySide6.QtWidgets import QMainWindow
from .board_widget import BoardWidget


class MainWindow(QMainWindow):
    """Main application window for the chess game.
    
    This window integrates the BoardWidget as its central widget and provides
    a FEN-based API for updating the board display. The window does not directly
    depend on the Game model - all communication is via FEN strings.
    """
    
    def __init__(self):
        """Initialize the main window with default properties."""
        super().__init__()
        
        # Set window title
        self.setWindowTitle("Chess Desktop App")
        
        # Set default window size
        self.resize(800, 600)
        
        # Create and set the board widget as the central widget
        self._board_widget = BoardWidget()
        self.setCentralWidget(self._board_widget)
    
    def set_board_fen(self, fen: str) -> None:
        """Set the board position from a FEN string.
        
        This method updates the displayed chessboard to show the position
        specified by the FEN string. It delegates to the BoardWidget's
        set_fen method.
        
        Args:
            fen: A valid FEN string representing the chess position.
        
        Raises:
            BoardFenError: If the FEN string is invalid (propagated from BoardWidget).
        
        Example:
            window = MainWindow()
            window.set_board_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
        """
        self._board_widget.set_fen(fen)

