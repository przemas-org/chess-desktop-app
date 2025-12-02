"""
Engine controller for coordinating between Game and EngineAdapter.

This module provides the EngineController class that bridges the domain Game
model and the EngineAdapter, managing automated engine moves for Black with
move validation, re-query logic, and error handling.
"""

from typing import Optional
from PySide6.QtCore import QObject, Signal

from ..game import Game, Side, GameStatus, IllegalMoveError
from .engine_integration import EngineAdapter, EngineErrorCode


class EngineController(QObject):
    """
    Controller coordinating between Game domain model and EngineAdapter.
    
    This controller manages automated engine moves for the engine-controlled side
    (Black in v1), including:
    - Triggering engine queries after human moves
    - Validating and applying engine responses
    - Re-querying once on illegal moves
    - Permanently disabling engine on repeated failures or errors
    
    The controller enforces a single in-flight request policy to prevent
    overlapping engine queries and maintains simple enabled/disabled state.
    
    For v1, the engine always plays Black. The controller is called by MainWindow
    after each successful human move via on_human_move_applied().
    
    Signals:
        engine_move_applied(): Emitted when an engine move has been successfully
                              applied to the Game. MainWindow should refresh the
                              board display in response.
        
        engine_disabled(reason: str): Emitted when the engine has been permanently
                                     disabled due to repeated failures or errors.
                                     The reason string describes why.
    
    Usage Example:
        # Create controller (assuming adapter is initialized)
        game = Game()
        adapter = StockfishProcessAdapter("/path/to/stockfish")
        controller = EngineController(game, adapter)
        
        # Connect signals
        controller.engine_move_applied.connect(on_board_update_needed)
        controller.engine_disabled.connect(on_engine_error)
        
        # After human move is applied to game:
        controller.on_human_move_applied()
        
        # Controller will query engine if Black to move, validate response,
        # and emit engine_move_applied or engine_disabled as appropriate
    """
    
    # Qt signals
    engine_move_applied = Signal()
    engine_disabled = Signal(str)
    
    def __init__(self, game: Game, adapter: EngineAdapter):
        """
        Initialize the engine controller.
        
        Args:
            game: The Game domain model instance to coordinate with.
            adapter: The EngineAdapter to use for move requests.
        """
        super().__init__()
        
        # Store references
        self._game = game
        self._adapter = adapter
        
        # Engine configuration (v1: always Black)
        self._engine_side = Side.BLACK
        
        # Engine state tracking
        self._is_enabled = True
        self._in_flight = False
        self._illegal_move_count = 0
        
        # Connect to adapter signals
        self._adapter.move_ready.connect(self._on_move_ready)
        self._adapter.move_failed.connect(self._on_move_failed)
    
    def on_human_move_applied(self) -> None:
        """
        Notify controller that a human move has been applied.
        
        This method should be called by MainWindow after each successful human
        move. The controller will check if it should query the engine for a
        response move based on:
        - Engine is enabled
        - No request currently in flight
        - It is the engine's turn (Black to move in v1)
        - Game is not in a terminal state (checkmate, stalemate, or draw)
        
        If all conditions are met, exports FEN from Game and requests a move
        from the adapter.
        
        Example:
            # In MainWindow after applying human move:
            self._game.apply_move("e2e4")
            self.update_board_from_game()
            if self._engine_controller:
                self._engine_controller.on_human_move_applied()
        """
        # Guard: check if engine is enabled
        if not self._is_enabled:
            return
        
        # Guard: prevent overlapping requests
        if self._in_flight:
            return
        
        # Guard: check if it's the engine's turn
        if self._game.get_side_to_move() != self._engine_side:
            return
        
        # Guard: check if game is in a terminal state
        status = self._game.get_status()
        if status in (GameStatus.CHECKMATE, GameStatus.STALEMATE,
                      GameStatus.DRAW_50_MOVE, GameStatus.DRAW_INSUFFICIENT_MATERIAL,
                      GameStatus.DRAW_OTHER):
            return
        
        # Reset illegal move counter for new position
        self._illegal_move_count = 0
        
        # Export FEN and request move
        fen = self._game.export_fen()
        self._in_flight = True
        self._adapter.request_move(fen, timeout_ms=1000)
    
    def is_enabled(self) -> bool:
        """
        Check if the engine is currently enabled.
        
        Returns:
            True if engine is enabled and can make moves, False if disabled.
        """
        return self._is_enabled
    
    def is_in_flight(self) -> bool:
        """
        Check if an engine request is currently in flight.
        
        Returns:
            True if waiting for engine response, False otherwise.
        """
        return self._in_flight
    
    def _on_move_ready(self, uci_move: str) -> None:
        """
        Handle successful engine response with a UCI move.
        
        Validates the move by attempting to apply it to the Game. If legal,
        clears state and emits engine_move_applied. If illegal, handles
        re-query logic.
        
        Args:
            uci_move: UCI move string from the engine (e.g., "e7e5").
        """
        # Guard: ignore stale responses
        if not self._in_flight:
            return
        
        try:
            # Attempt to apply the move (validates legality)
            self._game.apply_move(uci_move)
            
            # Success! Clear state and notify
            self._in_flight = False
            self._illegal_move_count = 0
            self.engine_move_applied.emit()
            
        except IllegalMoveError:
            # Move is illegal - handle re-query logic
            self._handle_illegal_move(uci_move)
    
    def _handle_illegal_move(self, uci_move: str) -> None:
        """
        Handle an illegal move from the engine.
        
        On the first illegal move for a position, immediately re-queries the
        engine from the same position. On the second illegal move, permanently
        disables the engine and emits engine_disabled.
        
        Args:
            uci_move: The illegal UCI move string that was rejected.
        """
        self._illegal_move_count += 1
        
        if self._illegal_move_count < 2:
            # First failure - retry immediately from same position
            fen = self._game.export_fen()
            self._adapter.request_move(fen, timeout_ms=1000)
            # Keep _in_flight = True
        else:
            # Second failure - disable permanently
            self._in_flight = False
            self._is_enabled = False
            self.engine_disabled.emit(
                f"Engine returned illegal move twice: {uci_move}"
            )
    
    def _on_move_failed(self, error_code: EngineErrorCode, message: str) -> None:
        """
        Handle engine adapter errors (timeout, crash, etc.).
        
        Clears the in-flight flag and permanently disables the engine on any
        adapter error. Emits engine_disabled with details.
        
        Args:
            error_code: The error code from the adapter.
            message: Human-readable error message.
        """
        # Guard: ignore if no request in flight
        if not self._in_flight:
            return
        
        # Clear in-flight flag
        self._in_flight = False
        
        # Disable engine permanently on any adapter error
        self._is_enabled = False
        self.engine_disabled.emit(
            f"Engine error ({error_code.value}): {message}"
        )

