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
from PySide6.QtCore import QObject, Signal, QTimer, QProcess


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


class StockfishProcessAdapter(EngineAdapter):
    """
    Concrete implementation of EngineAdapter using Stockfish via QProcess.
    
    This adapter manages a long-lived Stockfish process, handling UCI protocol
    communication, lifecycle management, and error handling. The process is
    spawned on initialization and kept alive for the duration of the session.
    
    The adapter performs a UCI handshake on initialization:
    1. Start the Stockfish process
    2. Send "uci" command
    3. Wait for "uciok" response
    4. Send "isready" command
    5. Wait for "readyok" response
    6. Transition to READY state
    
    All process communication is non-blocking and event-driven via Qt signals.
    A timeout of 5000ms is enforced for the handshake phase. If the handshake
    fails or times out, the adapter transitions to ERROR state permanently.
    
    Args:
        stockfish_path: Path to the Stockfish binary executable.
    
    Example:
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        adapter.initialized.connect(on_ready)
        adapter.initialization_failed.connect(on_error)
        adapter.initialize()
    
    Note:
        This implementation currently stubs out move request logic. Full UCI
        move request/response handling will be implemented in a later task.
    """
    
    # Handshake timeout in milliseconds
    HANDSHAKE_TIMEOUT_MS = 5000
    
    def __init__(self, stockfish_path: str):
        """
        Initialize the adapter with the path to Stockfish binary.
        
        Args:
            stockfish_path: Path to the Stockfish executable.
        """
        super().__init__()
        self._stockfish_path = stockfish_path
        self._process: Optional[QProcess] = None
        self._handshake_timer: Optional[QTimer] = None
        self._output_buffer = ""
        self._handshake_phase = ""  # Tracks: "" -> "uci_sent" -> "uci_ok" -> "isready_sent" -> "ready_ok"
        self._is_shutting_down = False
        self._move_timeout_timer: Optional[QTimer] = None
        self._pending_request_fen: Optional[str] = None
    
    def initialize(self) -> None:
        """
        Start the Stockfish process and perform UCI handshake.
        
        State transitions:
            DISABLED → INITIALIZING (immediately)
            INITIALIZING → READY (on successful handshake)
            INITIALIZING → ERROR (on failure or timeout)
        
        The method returns immediately. Success/failure is communicated via
        the initialized() or initialization_failed() signals.
        """
        # Transition to INITIALIZING state
        self._state = EngineState.INITIALIZING
        self._is_shutting_down = False
        
        # Create and configure QProcess
        self._process = QProcess()
        
        # Connect process signals
        self._process.started.connect(self._on_process_started)
        self._process.errorOccurred.connect(self._on_process_error)
        self._process.finished.connect(self._on_process_finished)
        self._process.readyReadStandardOutput.connect(self._on_stdout_ready)
        
        # Set up handshake timeout
        self._handshake_timer = QTimer()
        self._handshake_timer.setSingleShot(True)
        self._handshake_timer.timeout.connect(self._on_handshake_timeout)
        self._handshake_timer.start(self.HANDSHAKE_TIMEOUT_MS)
        
        # Start the Stockfish process
        self._process.start(self._stockfish_path, [])
    
    def request_move(self, fen: str, timeout_ms: int = 1000) -> None:
        """
        Request a move for the given position.
        
        Sends 'position fen <FEN>' and 'go movetime 100' commands to Stockfish,
        starts a timeout timer, and waits for the bestmove response.
        
        Args:
            fen: FEN string of the position (with Black to move in v1).
            timeout_ms: Timeout in milliseconds for the engine response.
        
        State transitions:
            READY → BUSY (immediately)
            BUSY → READY (on successful bestmove response)
            BUSY → ERROR (on timeout or crash)
            Other states: emits move_failed(INVALID_REQUEST)
        """
        # Validate state
        if self._state != EngineState.READY:
            self.move_failed.emit(
                EngineErrorCode.INVALID_REQUEST,
                f"Cannot request move in state {self._state.value}"
            )
            return
        
        # Check if process is available
        if self._process is None or self._process.state() != QProcess.ProcessState.Running:
            self._state = EngineState.ERROR
            self.move_failed.emit(
                EngineErrorCode.PROCESS_CRASHED,
                "Stockfish process is not running"
            )
            return
        
        # Transition to BUSY
        self._state = EngineState.BUSY
        self._pending_request_fen = fen
        
        # Send UCI commands
        position_cmd = f"position fen {fen}\n"
        go_cmd = "go movetime 100\n"
        
        try:
            self._process.write(position_cmd.encode('utf-8'))
            self._process.write(go_cmd.encode('utf-8'))
        except Exception as e:
            self._state = EngineState.ERROR
            self.move_failed.emit(
                EngineErrorCode.PROCESS_CRASHED,
                f"Failed to write to Stockfish process: {e}"
            )
            return
        
        # Set up timeout timer
        self._move_timeout_timer = QTimer()
        self._move_timeout_timer.setSingleShot(True)
        self._move_timeout_timer.timeout.connect(self._on_move_timeout)
        self._move_timeout_timer.start(timeout_ms)
    
    def shutdown(self) -> None:
        """
        Cleanly shut down the Stockfish process.
        
        This method is safe to call in any state and can be called multiple times.
        It attempts to gracefully terminate the process by sending "quit" command,
        then waits briefly before forcing termination if needed.
        
        No signals are emitted after shutdown begins.
        """
        self._is_shutting_down = True
        
        # Stop handshake timer if running
        if self._handshake_timer is not None:
            self._handshake_timer.stop()
            self._handshake_timer = None
        
        # Stop move timeout timer if running
        if self._move_timeout_timer is not None:
            self._move_timeout_timer.stop()
            self._move_timeout_timer = None
        
        # Terminate the process if it exists
        if self._process is not None:
            # Try graceful shutdown with "quit" command
            if self._process.state() == QProcess.ProcessState.Running:
                try:
                    self._process.write(b"quit\n")
                    self._process.waitForFinished(1000)  # Wait 1 second
                except Exception:
                    pass  # Ignore errors during shutdown
            
            # Force kill if still running
            if self._process.state() == QProcess.ProcessState.Running:
                self._process.kill()
                self._process.waitForFinished(1000)
            
            # Disconnect all signals to prevent any further emissions
            try:
                self._process.started.disconnect()
                self._process.errorOccurred.disconnect()
                self._process.finished.disconnect()
                self._process.readyReadStandardOutput.disconnect()
            except Exception:
                pass  # Ignore errors if already disconnected
            
            self._process = None
    
    def _on_process_started(self) -> None:
        """Handle successful process startup - send initial UCI command."""
        if self._is_shutting_down:
            return
        
        # Send "uci" command to initiate handshake
        self._handshake_phase = "uci_sent"
        self._process.write(b"uci\n")
    
    def _on_process_error(self, error) -> None:
        """Handle process startup or runtime errors."""
        if self._is_shutting_down:
            return
        
        # Map QProcess error to message
        error_messages = {
            QProcess.ProcessError.FailedToStart: "Failed to start Stockfish process. Check that the binary exists and is executable.",
            QProcess.ProcessError.Crashed: "Stockfish process crashed unexpectedly.",
            QProcess.ProcessError.Timedout: "Stockfish process timed out.",
            QProcess.ProcessError.WriteError: "Failed to write to Stockfish process.",
            QProcess.ProcessError.ReadError: "Failed to read from Stockfish process.",
            QProcess.ProcessError.UnknownError: "Unknown error occurred with Stockfish process.",
        }
        
        error_msg = error_messages.get(error, f"Stockfish process error: {error}")
        
        # Clean up
        self._cleanup_on_error()
        
        # Transition to ERROR state and emit failure signal
        self._state = EngineState.ERROR
        self.initialization_failed.emit(EngineErrorCode.INITIALIZATION_FAILED, error_msg)
    
    def _on_process_finished(self, exit_code: int, exit_status) -> None:
        """Handle unexpected process termination."""
        if self._is_shutting_down:
            return
        
        # If process exits during initialization, it's an initialization failure
        if self._state == EngineState.INITIALIZING:
            self._cleanup_on_error()
            self._state = EngineState.ERROR
            self.initialization_failed.emit(
                EngineErrorCode.PROCESS_CRASHED,
                f"Stockfish process terminated unexpectedly during initialization (exit code: {exit_code})"
            )
        # If process exits after being ready, it's a runtime crash
        elif self._state in (EngineState.READY, EngineState.BUSY):
            # Save the state before cleanup modifies it
            was_busy = (self._state == EngineState.BUSY)
            
            self._cleanup_on_error()
            self._state = EngineState.ERROR
            
            # Emit appropriate signal based on the saved state
            if was_busy:
                self.move_failed.emit(
                    EngineErrorCode.PROCESS_CRASHED,
                    f"Stockfish process crashed during move request (exit code: {exit_code})"
                )
    
    def _on_stdout_ready(self) -> None:
        """Handle data available on stdout - accumulate and parse UCI responses."""
        if self._is_shutting_down or self._process is None:
            return
        
        # Read all available data
        data = self._process.readAllStandardOutput()
        text = bytes(data).decode('utf-8', errors='replace')
        self._output_buffer += text
        
        # Process complete lines
        while '\n' in self._output_buffer:
            line, self._output_buffer = self._output_buffer.split('\n', 1)
            line = line.strip()
            
            if not line:
                continue
            
            # Handle UCI handshake responses
            if self._state == EngineState.INITIALIZING:
                self._process_handshake_line(line)
            
            # Handle move responses
            elif self._state == EngineState.BUSY:
                # Ignore info lines (engine analysis output)
                if line.startswith("info "):
                    continue
                
                # Parse bestmove lines
                if line.startswith("bestmove "):
                    # Extract UCI move (first token after "bestmove")
                    tokens = line.split()
                    if len(tokens) >= 2:
                        uci_move = tokens[1]
                        self._process_bestmove_line(uci_move)
    
    def _process_handshake_line(self, line: str) -> None:
        """Process a single line during UCI handshake."""
        if self._handshake_phase == "uci_sent" and line == "uciok":
            # Received uciok, send isready
            self._handshake_phase = "uci_ok"
            self._process.write(b"isready\n")
        
        elif self._handshake_phase == "uci_ok" and line == "readyok":
            # Handshake complete!
            self._handshake_phase = "ready_ok"
            
            # Stop timeout timer
            if self._handshake_timer is not None:
                self._handshake_timer.stop()
                self._handshake_timer = None
            
            # Transition to READY and emit success signal
            self._state = EngineState.READY
            self.initialized.emit()
    
    def _process_bestmove_line(self, uci_move: str) -> None:
        """
        Process a bestmove response from the engine.
        
        Args:
            uci_move: The UCI move string extracted from the bestmove line.
        """
        if self._is_shutting_down:
            return
        
        # Stop and clear timeout timer
        if self._move_timeout_timer is not None:
            self._move_timeout_timer.stop()
            self._move_timeout_timer = None
        
        # Clear pending request state
        self._pending_request_fen = None
        
        # Transition to READY state
        self._state = EngineState.READY
        
        # Emit the move result
        self.move_ready.emit(uci_move)
    
    def _on_handshake_timeout(self) -> None:
        """Handle handshake timeout - transition to ERROR state."""
        if self._is_shutting_down:
            return
        
        if self._state == EngineState.INITIALIZING:
            self._cleanup_on_error()
            self._state = EngineState.ERROR
            self.initialization_failed.emit(
                EngineErrorCode.TIMEOUT,
                f"UCI handshake timed out after {self.HANDSHAKE_TIMEOUT_MS}ms"
            )
    
    def _on_move_timeout(self) -> None:
        """Handle move request timeout - transition to ERROR state."""
        if self._is_shutting_down:
            return
        
        if self._state != EngineState.BUSY:
            return
        
        # Store timeout value for error message before clearing
        timeout_ms = self._move_timeout_timer.interval() if self._move_timeout_timer else 1000
        
        # Stop timer and clear request state
        if self._move_timeout_timer is not None:
            self._move_timeout_timer.stop()
            self._move_timeout_timer = None
        
        self._pending_request_fen = None
        
        # Clean up and transition to ERROR (terminal state)
        self._cleanup_on_error()
        self._state = EngineState.ERROR
        
        # Emit failure signal
        self.move_failed.emit(
            EngineErrorCode.TIMEOUT,
            f"Engine did not respond within {timeout_ms}ms"
        )
    
    def _cleanup_on_error(self) -> None:
        """Clean up resources on error (without emitting signals)."""
        # Stop handshake timer
        if self._handshake_timer is not None:
            self._handshake_timer.stop()
            self._handshake_timer = None
        
        # Terminate process
        if self._process is not None and self._process.state() == QProcess.ProcessState.Running:
            self._process.kill()
            self._process.waitForFinished(1000)

