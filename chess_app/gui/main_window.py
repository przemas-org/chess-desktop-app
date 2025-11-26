"""Main window for the chess desktop application."""

from PySide6.QtWidgets import QMainWindow


class MainWindow(QMainWindow):
    """Main application window for the chess game.
    
    This is a stub implementation that sets up the basic window properties.
    Future tickets will add the chessboard widget and other UI elements.
    """
    
    def __init__(self):
        """Initialize the main window with default properties."""
        super().__init__()
        
        # Set window title
        self.setWindowTitle("Chess Desktop App")
        
        # Set default window size
        self.resize(800, 600)

