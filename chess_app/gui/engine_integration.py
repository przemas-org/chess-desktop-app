"""
Engine integration abstraction for chess GUI.

This module provides a clean abstraction layer for integrating chess engines
(specifically Stockfish via UCI protocol) into the GUI layer. It defines the
contract for asynchronous engine communication using Qt signals, hiding UCI
and process management details behind a simple API.

For v1, the engine always plays Black. All FEN positions passed to request_move()
must have Black to move.
"""

from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Optional
from PySide6.QtCore import QObject, Signal, QTimer


class QABCMeta(type(QObject), ABCMeta):
    """Metaclass combining Qt's metaclass with ABC's metaclass."""
    pass


class EngineState(Enum):
    """
    Represents the current state of the engine adapter.
    
    State transitions:
        DISABLED → INITIALIZING (via initialize())
        INITIALIZING → READY (on successful UCI handshake)
        INITIALIZING → ERROR (on initialization failure)
        READY → BUSY (on request_move())
        BUSY → READY (on successful move response)
        BUSY → ERROR (on timeout or crash)
        Any state → ERROR (on terminal failure)
        ERROR remains ERROR (terminal state)
    
    Attributes:
        DISABLED: Engine is not available or has been explicitly disabled.
                 This is the initial state before initialization.
        INITIALIZING: Engine process is starting and UCI handshake is in progress.
                     No move requests can be made in this state.
        READY: Engine has been successfully initialized and is available for
              move requests. This is the only state where request_move() is valid.
        BUSY: A move request is currently in flight, waiting for the engine response.
             No additional requests can be made until the response arrives or times out.
        ERROR: A terminal error has occurred (crash, persistent failures, etc.).
              The engine cannot be used for the remainder of the session.
    """
    DISABLED = "disabled"
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"


class EngineErrorCode(Enum):
    """
    Standardized error codes for engine failures.
    
    These codes provide consistent error categorization for error handling
    and logging throughout the engine integration layer.
    
    Attributes:
        INITIALIZATION_FAILED: The engine process could not be started or the
                              UCI handshake failed. The engine moves to ERROR state.
        TIMEOUT: The engine did not respond within the configured timeout period.
                After a timeout, the engine moves to ERROR state.
        ILLEGAL_MOVE: The engine returned a move that is not legal in the current
                     position. This may trigger a retry or move to ERROR state
                     depending on the controller's policy.
        PROCESS_CRASHED: The engine process terminated unexpectedly during operation.
                        The engine moves to ERROR state.
        INVALID_REQUEST: API misuse detected, such as calling request_move() when
                        the engine is not in READY state, or attempting to make
                        concurrent requests. The engine state is not changed.
    """
    INITIALIZATION_FAILED = "initialization_failed"
    TIMEOUT = "timeout"
    ILLEGAL_MOVE = "illegal_move"
    PROCESS_CRASHED = "process_crashed"
    INVALID_REQUEST = "invalid_request"


class EngineAdapter(QObject, metaclass=QABCMeta):
    """
    Abstract base class defining the contract for chess engine communication.
    
    This adapter provides an asynchronous API for requesting moves from a chess
    engine. All operations are non-blocking and results are delivered via Qt signals.
    
    API Contract:
        - Single in-flight request: Only one request_move() can be active at a time.
          Attempting concurrent requests will emit move_failed with INVALID_REQUEST.
        - Engine always plays Black (v1 constraint): All FEN positions passed to
          request_move() must have Black to move. No validation is performed by
          the adapter.
        - State machine enforcement: request_move() is only valid when state is READY.
          Calls in other states emit move_failed with INVALID_REQUEST immediately.
        - No FEN validation: The adapter assumes valid FEN input from Game.export_fen().
        - Thread safety: Concrete implementations must ensure thread-safe signal
          emission if using background threads for engine communication.
    
    Signals:
        initialized(): Emitted when the engine has been successfully initialized
                      and is ready to accept move requests. State transitions to READY.
        
        initialization_failed(error_code: EngineErrorCode, message: str):
                      Emitted when initialization fails. State transitions to ERROR.
        
        move_ready(uci_move: str): Emitted when a valid move has been received from
                      the engine. The move is in UCI format (e.g., "e7e5", "e7e8q").
                      State transitions from BUSY to READY.
        
        move_failed(error_code: EngineErrorCode, message: str):
                      Emitted when a move request fails due to timeout, error, or
                      invalid API usage. State may transition to ERROR for terminal
                      failures (timeout, crash) or remain unchanged for INVALID_REQUEST.
    
    Usage Example:
        # Create adapter (concrete implementation)
        adapter = StockfishAdapter("/path/to/stockfish")
        
        # Connect signals
        adapter.initialized.connect(on_engine_ready)
        adapter.move_ready.connect(on_move_received)
        adapter.move_failed.connect(on_move_error)
        
        # Initialize engine
        adapter.initialize()
        
        # Later, when initialized signal received and state is READY:
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        adapter.request_move(fen, timeout_ms=1000)
        
        # When done:
        adapter.shutdown()
    
    Note for v1:
        The engine always plays Black. Controllers must ensure FEN positions
        passed to request_move() have Black to move (indicated by 'b' in the
        second field of the FEN string).
    """
    
    # Qt signals for asynchronous result delivery
    initialized = Signal()
    initialization_failed = Signal(EngineErrorCode, str)
    move_ready = Signal(str)
    move_failed = Signal(EngineErrorCode, str)
    
    def __init__(self):
        """Initialize the engine adapter with DISABLED state."""
        super().__init__()
        self._state = EngineState.DISABLED
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Start the engine process and perform UCI handshake.
        
        This method is asynchronous. It returns immediately and emits either
        initialized() or initialization_failed() when the process completes.
        
        State transitions:
            DISABLED → INITIALIZING (immediately)
            INITIALIZING → READY (on success via initialized signal)
            INITIALIZING → ERROR (on failure via initialization_failed signal)
        
        Raises:
            No exceptions are raised. All failures are reported via the
            initialization_failed signal.
        
        Example:
            adapter = StockfishAdapter("/usr/bin/stockfish")
            adapter.initialized.connect(lambda: print("Engine ready!"))
            adapter.initialize()
        """
        pass
    
    @abstractmethod
    def request_move(self, fen: str, timeout_ms: int = 1000) -> None:
        """
        Request the best move for the given position.
        
        This method is asynchronous and only valid when state is READY.
        It returns immediately and emits either move_ready() or move_failed()
        when the engine responds or the timeout expires.
        
        For v1, the FEN must represent a position with Black to move. No
        validation is performed by the adapter.
        
        Args:
            fen: Full FEN string representing the position. Must have Black to move
                 (second field must be 'b'). Assumed to be valid FEN from Game.
            timeout_ms: Timeout in milliseconds. If the engine does not respond
                       within this period, move_failed(TIMEOUT, ...) is emitted
                       and state transitions to ERROR. Default is 1000ms.
        
        State transitions:
            READY → BUSY (immediately)
            BUSY → READY (on success via move_ready signal)
            BUSY → ERROR (on timeout/crash via move_failed signal)
            Other states: No state change, emits move_failed(INVALID_REQUEST, ...)
        
        Error conditions emitted via move_failed:
            - INVALID_REQUEST: Called when state is not READY
            - TIMEOUT: Engine did not respond within timeout_ms
            - PROCESS_CRASHED: Engine process died during request
            - ILLEGAL_MOVE: Engine returned an illegal move (reported by controller)
        
        Example:
            # Assuming adapter is initialized and state is READY
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            adapter.request_move(fen, timeout_ms=1500)
            # Wait for move_ready or move_failed signal
        """
        pass
    
    @abstractmethod
    def shutdown(self) -> None:
        """
        Cleanly shut down the engine process.
        
        This method can be called in any state and should ensure graceful
        termination of any background processes or threads. After shutdown,
        the adapter should not emit any further signals.
        
        Safe to call multiple times. No signals are emitted.
        
        Example:
            adapter.shutdown()  # Clean up resources
        """
        pass
    
    def get_state(self) -> EngineState:
        """
        Query the current engine state.
        
        Returns:
            The current EngineState (DISABLED, INITIALIZING, READY, BUSY, or ERROR).
        
        Example:
            if adapter.get_state() == EngineState.READY:
                adapter.request_move(fen)
        """
        return self._state


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
        self._call_log: list[tuple[str, tuple]] = []
        self._pending_timers: list[QTimer] = []
    
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
    
    def get_call_log(self) -> list[tuple[str, tuple]]:
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

