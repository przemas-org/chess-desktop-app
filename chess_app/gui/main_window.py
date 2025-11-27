"""Main window for the chess desktop application."""

from typing import Optional
from PySide6.QtWidgets import QMainWindow
from .board_widget import BoardWidget
from ..game import Game


class MainWindow(QMainWindow):
    """Main application window for the chess game.
    
    This window acts as the controller between the Game domain model and the
    BoardWidget view. It owns a Game instance and coordinates updates between
    the game state and the board display.
    
    The MainWindow maintains clear responsibility boundaries:
    - Game: GUI-agnostic chess logic and state management
    - MainWindow: Controller coordinating game and view
    - BoardWidget: FEN-based rendering (internal API only)
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
        
        # Game instance owned by this window
        self._game: Optional[Game] = None
    
    def set_game(self, game: Game) -> None:
        """Set or replace the game instance owned by this window.
        
        This method injects a Game instance into the MainWindow, allowing it
        to coordinate between the game model and the board view. The game can
        be replaced at any time, making this useful for starting new games,
        loading saved games, or testing.
        
        Args:
            game: A Game instance to be owned by this window.
        
        Example:
            window = MainWindow()
            game = Game()  # Standard starting position
            window.set_game(game)
            window.update_board_from_game()
            
            # Or load from FEN
            game = Game.from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
            window.set_game(game)
            window.update_board_from_game()
        """
        self._game = game
    
    def update_board_from_game(self) -> None:
        """Update the board display from the current game state.
        
        This method reads the current position from the owned Game instance
        (via export_fen) and updates the BoardWidget to display that position.
        This is the primary method for refreshing the board view after game
        state changes.
        
        All board updates should go through this method to maintain consistency
        between the game model and the view.
        
        Raises:
            RuntimeError: If no game has been set via set_game().
            BoardFenError: If the game's FEN is somehow invalid (propagated from BoardWidget).
        
        Example:
            window = MainWindow()
            game = Game()
            window.set_game(game)
            
            # Make some moves
            game.apply_move("e2e4")
            game.apply_move("e7e5")
            
            # Refresh the board to show the new position
            window.update_board_from_game()
        """
        if self._game is None:
            raise RuntimeError(
                "Cannot update board: no game has been set. "
                "Call set_game() first to provide a Game instance."
            )
        
        fen = self._game.export_fen()
        self._board_widget.set_fen(fen)

