"""Main window for the chess desktop application."""

from typing import Optional
from PySide6.QtWidgets import QMainWindow, QMessageBox
from PySide6.QtCore import Qt
from .board_widget import BoardWidget
from .engine_controller import EngineController
from .engine_integration import EngineAdapter
from ..game import Game, IllegalMoveError, Side, GameStatus


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
        self._engine_enabled: bool = False
        
        # Input locking (disabled until game is set)
        self._input_enabled: bool = False
        
        # Set initial window title (no engine yet)
        title = self._compute_window_title(self._engine_enabled, self._game)
        self.setWindowTitle(title)
        
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
        # Enable input when a game is set
        self._input_enabled = True
    
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
        self._engine_enabled = True
        
        # Update window title to reflect engine availability
        title = self._compute_window_title(self._engine_enabled, self._game)
        self.setWindowTitle(title)
        
        # Connect controller signals
        self._engine_controller.engine_move_applied.connect(
            self._on_engine_move_applied
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
        # Guard: ignore all clicks when input is disabled
        if not self._input_enabled:
            return
        
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
        
        # Guard: ignore input when disabled
        if not self._input_enabled:
            return
        
        # Guard: block input while engine move is in flight
        if self._engine_controller is not None and self._engine_controller.is_in_flight():
            return
        
        # Guard: when engine is configured AND enabled, only allow White pieces
        if self._engine_controller is not None and self._engine_controller.is_enabled():
            piece_side = self._game.get_piece_side(square)
            if piece_side != Side.WHITE:
                # Silently ignore - not a White piece
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
        # Guard: ignore input when disabled
        if not self._input_enabled:
            return
        
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
            
            # Evaluate game status and handle terminal states
            self._evaluate_and_handle_game_status()
            
            # Clear selection after successful move
            self._clear_selection()
            
            # Trigger engine move if available (only if game is ongoing)
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
        # Guard: ignore input when disabled (for complete input isolation)
        if not self._input_enabled:
            return
        
        self._selected_source = None
        self._legal_destinations = set()
        self._board_widget.set_selected_square(None)
        self._board_widget.set_highlighted_squares([])
    
    def _on_engine_move_applied(self) -> None:
        """Handle engine move completion: update board and evaluate status.
        
        This method is called when the engine controller successfully applies
        an engine move to the game. It updates the board display from the new
        game state and evaluates the game status to detect terminal conditions
        or update the window title with the current state.
        
        This ensures that engine moves trigger the same status evaluation flow
        as human moves, maintaining consistent game-end detection and UI updates.
        """
        # Update the board from the new game state
        self.update_board_from_game()
        
        # Evaluate game status and handle terminal states
        self._evaluate_and_handle_game_status()
    
    def _on_engine_disabled(self, reason: str) -> None:
        """Handle engine being permanently disabled.
        
        This is called when the engine controller disables the engine due to
        repeated failures or errors. Updates the window title to reflect
        that the engine is no longer available.
        
        Args:
            reason: Human-readable description of why engine was disabled.
        """
        self._engine_enabled = False
        title = self._compute_window_title(self._engine_enabled, self._game)
        self.setWindowTitle(title)
    
    @staticmethod
    def _get_result_description(status: GameStatus, side_to_move: Side) -> str:
        """Map game status and side to human-readable result description.
        
        This is a pure helper function that converts domain-level game status
        and side-to-move information into user-friendly result strings suitable
        for display in message boxes and window titles.
        
        Args:
            status: The terminal game status (checkmate or draw variant).
            side_to_move: The side whose turn it was when terminal state occurred.
        
        Returns:
            A human-readable description of the game result.
            
        Examples:
            >>> MainWindow._get_result_description(GameStatus.CHECKMATE, Side.WHITE)
            'Checkmate — Black wins'
            >>> MainWindow._get_result_description(GameStatus.STALEMATE, Side.WHITE)
            'Draw by stalemate'
        """
        if status == GameStatus.CHECKMATE:
            # The side to move is in checkmate, so the other side wins
            if side_to_move == Side.WHITE:
                return "Checkmate — Black wins"
            else:
                return "Checkmate — White wins"
        elif status == GameStatus.STALEMATE:
            return "Draw by stalemate"
        elif status == GameStatus.DRAW_INSUFFICIENT_MATERIAL:
            return "Draw by insufficient material"
        elif status == GameStatus.DRAW_50_MOVE:
            return "Draw by fifty-move rule"
        elif status == GameStatus.DRAW_OTHER:
            return "Draw by repetition"
        else:
            # Fallback for unexpected status
            return f"Game ended: {status.value}"
    
    @staticmethod
    def _get_ongoing_status_text(status: GameStatus, side_to_move: Side) -> str:
        """Get brief status text for ongoing games.
        
        This is a pure helper function that creates concise status text
        for the window title when the game is still in progress.
        
        Args:
            status: The current game status (ongoing or check).
            side_to_move: The side whose turn it is.
        
        Returns:
            Brief status text suitable for window title.
            
        Examples:
            >>> MainWindow._get_ongoing_status_text(GameStatus.ONGOING, Side.WHITE)
            'White to move'
            >>> MainWindow._get_ongoing_status_text(GameStatus.CHECK, Side.BLACK)
            'Black to move — in check'
        """
        side_name = "White" if side_to_move == Side.WHITE else "Black"
        
        if status == GameStatus.CHECK:
            return f"{side_name} to move — in check"
        else:
            return f"{side_name} to move"
    
    @staticmethod
    def _compute_window_title(
        engine_enabled: bool,
        game: Optional[Game] = None
    ) -> str:
        """Compute window title based on engine availability and game state.
        
        This is the single source of truth for window title computation.
        It centralizes all title-related logic, replacing scattered ad-hoc
        title construction throughout the codebase.
        
        Title format depends on game state:
        - No game set: "Chess Desktop App — [Engine Mode]"
        - Ongoing game: "Chess Desktop App — [Engine Mode] ([Status])"
        - Game over: "Chess Desktop App — Game Over: [Result]"
        
        Note that game-over titles do NOT include engine mode, as the
        engine/human distinction is not relevant to the final result.
        
        Args:
            engine_enabled: Whether engine is currently enabled.
            game: Optional Game instance for status/side queries. If None,
                  returns base title with engine mode only.
        
        Returns:
            Complete window title string suitable for setWindowTitle().
            
        Examples:
            >>> MainWindow._compute_window_title(False, None)
            'Chess Desktop App — Human vs Human'
            >>> MainWindow._compute_window_title(True, None)
            'Chess Desktop App — Engine Enabled'
        """
        # Base application title
        base_title = "Chess Desktop App"
        
        # Determine engine mode suffix
        if engine_enabled:
            engine_mode = " — Engine Enabled"
        else:
            engine_mode = " — Human vs Human"
        
        # If no game is set, return base title with engine mode
        if game is None:
            return base_title + engine_mode
        
        # Query game state
        status = game.get_status()
        side_to_move = game.get_side_to_move()
        
        # Check if terminal state
        terminal_statuses = {
            GameStatus.CHECKMATE,
            GameStatus.STALEMATE,
            GameStatus.DRAW_INSUFFICIENT_MATERIAL,
            GameStatus.DRAW_50_MOVE,
            GameStatus.DRAW_OTHER
        }
        
        if status in terminal_statuses:
            # Terminal state: show game-over format without engine mode
            result_description = MainWindow._get_result_description(status, side_to_move)
            return f"{base_title} — Game Over: {result_description}"
        else:
            # Ongoing game: show engine mode and game status
            ongoing_text = MainWindow._get_ongoing_status_text(status, side_to_move)
            return f"{base_title}{engine_mode} ({ongoing_text})"
    
    def _handle_game_end(self, status: GameStatus, side_to_move: Side) -> None:
        """Handle terminal game states with modal dialog and title update.
        
        This method is called when the game reaches a terminal state (checkmate
        or any draw variant). It displays a modal message box with the result
        and updates the window title to reflect the game-over state.
        
        Additionally, this method disables further user input to prevent
        interactions after the game has ended.
        
        Args:
            status: The terminal game status (checkmate or draw variant).
            side_to_move: The side whose turn it was when terminal state occurred.
        
        Note:
            This method shows a blocking modal dialog, so it will pause execution
            until the user dismisses the message box.
        """
        # Disable input before showing modal to ensure no interactions during dialog
        self._input_enabled = False
        
        # Get human-readable result description
        result_description = self._get_result_description(status, side_to_move)
        
        # Show modal message box with result
        QMessageBox.information(
            self,
            "Game Over",
            result_description,
            QMessageBox.StandardButton.Ok
        )
        
        # Update window title to game-over format
        title = self._compute_window_title(self._engine_enabled, self._game)
        self.setWindowTitle(title)
    
    def _evaluate_and_handle_game_status(self) -> None:
        """Evaluate current game status and handle terminal states or update title.
        
        This is the main entry point for game status evaluation. It queries the
        game model for current status and side-to-move, then either:
        - For terminal states: delegates to _handle_game_end()
        - For non-terminal states: updates window title with ongoing status
        
        This method should be called after every move (human or engine) to keep
        the UI in sync with the game state.
        
        Note:
            This method requires a game to be set via set_game(). If no game is
            set, it returns early without doing anything.
        """
        # Guard: ensure game is set
        if self._game is None:
            return
        
        # Query game state
        status = self._game.get_status()
        side_to_move = self._game.get_side_to_move()
        
        # Check if terminal state
        terminal_statuses = {
            GameStatus.CHECKMATE,
            GameStatus.STALEMATE,
            GameStatus.DRAW_INSUFFICIENT_MATERIAL,
            GameStatus.DRAW_50_MOVE,
            GameStatus.DRAW_OTHER
        }
        
        if status in terminal_statuses:
            # Handle game end
            self._handle_game_end(status, side_to_move)
        else:
            # Update title for ongoing game
            title = self._compute_window_title(self._engine_enabled, self._game)
            self.setWindowTitle(title)

