#!/usr/bin/env python3
"""
Test utilities for engine adapter testing.

This module provides fake/mock implementations of the EngineAdapter interface
for use in unit tests. These fakes allow testing of higher-level components
(like EngineController and MainWindow) without spawning actual engine processes.

The primary utility is FakeEngineAdapter, which:
- Records all method calls for verification
- Allows simulation of various engine behaviors (success, timeout, crash, etc.)
- Supports delayed responses for timing-related tests
- Maintains proper state machine transitions matching the real adapter contract

Usage Example:
    from tests.engine_fakes import FakeEngineAdapter
    
    # Create and initialize
    fake = FakeEngineAdapter()
    fake.initialized.connect(on_ready_handler)
    fake.initialize()
    fake.simulate_init_success()
    
    # Simulate move request and response
    fake.request_move(fen, timeout_ms=1000)
    fake.simulate_move_response("e7e5")
    
    # Verify calls were made
    calls = fake.get_call_log()
    assert calls[0] == ("initialize", ())
    assert calls[1] == ("request_move", (fen, 1000))
"""

from typing import List, Tuple
from PySide6.QtCore import QTimer

from chess_app.gui.engine_integration import (
    EngineAdapter,
    EngineState,
    EngineErrorCode,
)

__all__ = ['FakeEngineAdapter']


class FakeEngineAdapter(EngineAdapter):
    """
    Fake engine adapter for testing.
    
    This implementation records all method calls and provides test helper methods
    to simulate engine behavior without spawning actual processes. Useful for
    unit testing higher-level components that depend on EngineAdapter.
    
    The fake adapter can be configured to simulate various scenarios:
    - Successful initialization and move responses
    - Initialization failures
    - Move timeouts
    - Illegal moves
    - Process crashes
    
    Call logging:
        All method invocations (initialize, request_move, shutdown) are logged
        and can be inspected via get_call_log().
    
    Usage Example:
        # Create fake adapter
        fake = FakeEngineAdapter()
        
        # Connect signals
        fake.initialized.connect(on_initialized)
        fake.move_ready.connect(on_move)
        
        # Simulate initialization
        fake.initialize()
        fake.simulate_init_success()  # Triggers initialized signal
        
        # Simulate move request
        fake.request_move(fen)
        fake.simulate_move_response("e7e5")  # Triggers move_ready signal
        
        # Inspect calls
        calls = fake.get_call_log()
        assert calls[0] == ("initialize", ())
        assert calls[1] == ("request_move", (fen, 1000))
    """
    
    def __init__(self):
        """Initialize the fake adapter with empty call log."""
        super().__init__()
        self._call_log: List[Tuple[str, tuple]] = []
        self._pending_timers: List[QTimer] = []
    
    def initialize(self) -> None:
        """
        Record initialization call and transition to INITIALIZING state.
        
        Does not emit any signals automatically. Use simulate_init_success()
        or simulate_init_failure() to trigger the appropriate signal.
        """
        self._call_log.append(("initialize", ()))
        self._state = EngineState.INITIALIZING
    
    def request_move(self, fen: str, timeout_ms: int = 1000) -> None:
        """
        Record move request call and handle state transitions.
        
        If state is not READY, immediately emits move_failed(INVALID_REQUEST).
        Otherwise transitions to BUSY state. Use simulate_move_response() or
        simulate_move_failure() to trigger the appropriate signal.
        
        Args:
            fen: FEN position string (logged but not validated)
            timeout_ms: Timeout in milliseconds (logged)
        """
        self._call_log.append(("request_move", (fen, timeout_ms)))
        
        if self._state != EngineState.READY:
            # Emit error signal for invalid state
            self.move_failed.emit(
                EngineErrorCode.INVALID_REQUEST,
                f"Cannot request move in state {self._state.value}"
            )
            return
        
        self._state = EngineState.BUSY
    
    def shutdown(self) -> None:
        """
        Record shutdown call and cancel any pending timers.
        
        Can be called in any state. Cancels all pending delayed responses.
        """
        self._call_log.append(("shutdown", ()))
        
        # Cancel any pending timers
        for timer in self._pending_timers:
            timer.stop()
        self._pending_timers.clear()
    
    def simulate_init_success(self) -> None:
        """
        Simulate successful engine initialization.
        
        Transitions state from INITIALIZING to READY and emits initialized signal.
        Should only be called after initialize() when state is INITIALIZING.
        
        Example:
            fake.initialize()
            fake.simulate_init_success()
            # initialized signal emitted, state is now READY
        """
        if self._state == EngineState.INITIALIZING:
            self._state = EngineState.READY
            self.initialized.emit()
    
    def simulate_init_failure(self, error_code: EngineErrorCode, message: str) -> None:
        """
        Simulate engine initialization failure.
        
        Transitions state from INITIALIZING to ERROR and emits initialization_failed signal.
        Should only be called after initialize() when state is INITIALIZING.
        
        Args:
            error_code: The error code to report (typically INITIALIZATION_FAILED)
            message: Human-readable error message
        
        Example:
            fake.initialize()
            fake.simulate_init_failure(
                EngineErrorCode.INITIALIZATION_FAILED,
                "Stockfish binary not found"
            )
            # initialization_failed signal emitted, state is now ERROR
        """
        if self._state == EngineState.INITIALIZING:
            self._state = EngineState.ERROR
            self.initialization_failed.emit(error_code, message)
    
    def simulate_move_response(self, uci_move: str, delay_ms: int = 0) -> None:
        """
        Simulate successful move response from engine.
        
        Transitions state from BUSY to READY and emits move_ready signal.
        Should only be called after request_move() when state is BUSY.
        
        Args:
            uci_move: The UCI move string to return (e.g., "e7e5", "e7e8q")
            delay_ms: Optional delay in milliseconds before emitting signal.
                     If 0, signal is emitted immediately. If > 0, signal is
                     emitted after delay via QTimer.
        
        Example:
            fake.request_move(fen)
            fake.simulate_move_response("e7e5")
            # move_ready signal emitted, state is now READY
            
            # With delay:
            fake.request_move(fen)
            fake.simulate_move_response("e7e5", delay_ms=100)
            # move_ready signal will be emitted after 100ms
        """
        if self._state != EngineState.BUSY:
            return
        
        if delay_ms <= 0:
            self._state = EngineState.READY
            self.move_ready.emit(uci_move)
        else:
            # Schedule delayed emission
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self._emit_delayed_move(uci_move, timer))
            timer.start(delay_ms)
            self._pending_timers.append(timer)
    
    def simulate_move_failure(self, error_code: EngineErrorCode, message: str) -> None:
        """
        Simulate move request failure.
        
        Transitions state from BUSY to ERROR (for terminal errors like TIMEOUT,
        PROCESS_CRASHED) or keeps state unchanged (for INVALID_REQUEST).
        Emits move_failed signal.
        
        Args:
            error_code: The error code to report (TIMEOUT, PROCESS_CRASHED, etc.)
            message: Human-readable error message
        
        Example:
            fake.request_move(fen)
            fake.simulate_move_failure(
                EngineErrorCode.TIMEOUT,
                "Engine did not respond within 1000ms"
            )
            # move_failed signal emitted, state is now ERROR
        """
        # Terminal errors transition to ERROR state
        if error_code in (EngineErrorCode.TIMEOUT, EngineErrorCode.PROCESS_CRASHED):
            self._state = EngineState.ERROR
        elif error_code == EngineErrorCode.ILLEGAL_MOVE:
            # For illegal move, return to READY so controller can retry
            self._state = EngineState.READY
        # INVALID_REQUEST keeps current state
        
        self.move_failed.emit(error_code, message)
    
    def get_call_log(self) -> List[Tuple[str, tuple]]:
        """
        Get the log of all method calls made to this adapter.
        
        Returns:
            List of tuples (method_name, args_tuple) in chronological order.
            For example: [("initialize", ()), ("request_move", (fen, 1000))]
        
        Example:
            fake = FakeEngineAdapter()
            fake.initialize()
            fake.request_move("rnbq... b ...", timeout_ms=2000)
            fake.shutdown()
            
            calls = fake.get_call_log()
            assert len(calls) == 3
            assert calls[0][0] == "initialize"
            assert calls[1][0] == "request_move"
            assert calls[2][0] == "shutdown"
        """
        return self._call_log.copy()
    
    def _emit_delayed_move(self, uci_move: str, timer: QTimer) -> None:
        """Internal helper to emit move_ready after delay."""
        if self._state == EngineState.BUSY:
            self._state = EngineState.READY
            self.move_ready.emit(uci_move)
        
        # Clean up timer
        if timer in self._pending_timers:
            self._pending_timers.remove(timer)

