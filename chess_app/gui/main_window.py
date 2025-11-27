"""Main window for the chess desktop application."""

from typing import Optional
from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt
from .board_widget import BoardWidget
from .engine_controller import EngineController
from .engine_integration import EngineAdapter
from ..game import Game, IllegalMoveError


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
        
        # Move selection state
        self._selected_source: Optional[str] = None
        self._legal_destinations: set[str] = set()
        
        # Engine components (optional, may be None if engine not available)
        self._engine_adapter: Optional[EngineAdapter] = None
        self._engine_controller: Optional[EngineController] = None
        
        # Connect board widget signals
        self._board_widget.square_clicked.connect(self._on_square_clicked)
    
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
    
    def set_engine_adapter(self, adapter: EngineAdapter) -> None:
        """Set the engine adapter and create the engine controller.
        
        This method should be called after set_game() to enable engine play.
        It creates an EngineController that coordinates between the Game and
        the adapter, handling automated engine moves for Black.
        
        Args:
            adapter: An initialized EngineAdapter instance.
        
        Example:
            window = MainWindow()
            game = Game()
            window.set_game(game)
            
            adapter = StockfishProcessAdapter("/path/to/stockfish")
            adapter.initialize()
            window.set_engine_adapter(adapter)
        """
        if self._game is None:
            raise RuntimeError(
                "Cannot set engine adapter: no game has been set. "
                "Call set_game() first."
            )
        
        self._engine_adapter = adapter
        self._engine_controller = EngineController(self._game, adapter)
        
        # Connect controller signals
        self._engine_controller.engine_move_applied.connect(
            self.update_board_from_game
        )
        self._engine_controller.engine_disabled.connect(
            self._on_engine_disabled
        )
    
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
    
    def _on_square_clicked(self, square: str, button: Qt.MouseButton) -> None:
        """Handle square clicks from the board widget.
        
        Implements two-click move selection logic:
        - Left-click on source square: select piece and highlight legal destinations
        - Left-click on destination: apply move if legal
        - Left-click on selected source: cancel selection
        - Right-click anywhere: cancel selection
        
        Args:
            square: The clicked square in algebraic notation (e.g., "e4").
            button: The mouse button used (left or right).
        """
        # Right-click always clears selection
        if button == Qt.MouseButton.RightButton:
            self._clear_selection()
            return
        
        # Left-click: handle source or destination selection
        if button == Qt.MouseButton.LeftButton:
            if self._selected_source is None:
                # No source selected: try to select this square as source
                self._handle_source_selection(square)
            else:
                # Source already selected: treat this as destination
                self._handle_destination_selection(square)
    
    def _handle_source_selection(self, square: str) -> None:
        """Handle left-click when no source is selected.
        
        If the clicked square has legal moves available, select it as the source
        and highlight all legal destination squares. If the square has no legal
        moves, clear any existing selection.
        
        Args:
            square: The clicked square in algebraic notation.
        """
        # Guard: ensure game is set
        if self._game is None:
            return
        
        try:
            # Get all legal moves in the current position
            all_legal_moves = self._game.get_legal_moves()
            
            # Filter moves from the clicked square
            moves_from_square = [
                move for move in all_legal_moves
                if move.from_square == square
            ]
            
            # If no legal moves from this square, clear selection
            if not moves_from_square:
                self._clear_selection()
                return
            
            # Select this square as source
            self._selected_source = square
            
            # Compute legal destination squares
            self._legal_destinations = {move.to_square for move in moves_from_square}
            
            # Update board widget to show selection and highlights
            self._board_widget.set_selected_square(square)
            self._board_widget.set_highlighted_squares(self._legal_destinations)
            
        except Exception:
            # On any error, clear selection for safety
            self._clear_selection()
    
    def _handle_destination_selection(self, square: str) -> None:
        """Handle left-click when a source is already selected.
        
        If the clicked square is the same as the selected source, cancel the selection.
        If the clicked square is a legal destination, apply the move and update the board.
        If the clicked square is not a legal destination, do nothing (silent failure).
        
        For promotion moves, automatically select queen promotion.
        
        Args:
            square: The clicked square in algebraic notation.
        """
        # If clicking the same square, cancel selection
        if square == self._selected_source:
            self._clear_selection()
            return
        
        # If not a legal destination, ignore silently
        if square not in self._legal_destinations:
            return
        
        # Guard: ensure game is set
        if self._game is None:
            self._clear_selection()
            return
        
        try:
            # Find the matching move(s)
            all_legal_moves = self._game.get_legal_moves()
            matching_moves = [
                move for move in all_legal_moves
                if move.from_square == self._selected_source and move.to_square == square
            ]
            
            if not matching_moves:
                # No matching move found (shouldn't happen, but handle gracefully)
                self._clear_selection()
                return
            
            # If multiple moves (promotion variants), select queen promotion
            move_to_apply = matching_moves[0]
            if len(matching_moves) > 1:
                # Look for queen promotion
                queen_moves = [m for m in matching_moves if m.promotion == 'q']
                if queen_moves:
                    move_to_apply = queen_moves[0]
            
            # Apply the move
            self._game.apply_move(move_to_apply)
            
            # Update the board from the new game state
            self.update_board_from_game()
            
            # Clear selection after successful move
            self._clear_selection()
            
            # Trigger engine move if available
            if self._engine_controller:
                self._engine_controller.on_human_move_applied()
            
        except IllegalMoveError:
            # If move is somehow illegal, clear selection silently
            self._clear_selection()
        except Exception:
            # On any other error, clear selection for safety
            self._clear_selection()
    
    def _clear_selection(self) -> None:
        """Clear the current move selection and all highlights.
        
        Resets the internal selection state and clears visual highlights
        in the board widget. Safe to call at any time.
        """
        self._selected_source = None
        self._legal_destinations = set()
        self._board_widget.set_selected_square(None)
        self._board_widget.set_highlighted_squares([])
    
    def _on_engine_disabled(self, reason: str) -> None:
        """Handle engine being permanently disabled.
        
        This is called when the engine controller disables the engine due to
        repeated failures or errors. Currently just logs the reason silently.
        Future versions may show a user notification.
        
        Args:
            reason: Human-readable description of why engine was disabled.
        """
        # For v1, silently disable. Could add UI notification in future.
        pass

