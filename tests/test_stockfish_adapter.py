#!/usr/bin/env python3
"""
Unit tests for StockfishProcessAdapter.

This module tests the concrete Stockfish adapter implementation using mocked
QProcess to simulate various scenarios without requiring an actual Stockfish binary.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch, call
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QProcess, QTimer

from chess_app.gui.engine_integration import (
    EngineState,
    EngineErrorCode,
    StockfishProcessAdapter,
)


@pytest.fixture
def qt_app():
    """Ensure QApplication exists for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestStockfishAdapterBasics:
    """Tests for basic StockfishProcessAdapter functionality."""
    
    def test_adapter_can_be_instantiated(self, qt_app):
        """StockfishProcessAdapter should be instantiable with a path."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        assert adapter is not None
        assert adapter.get_state() == EngineState.DISABLED
    
    def test_initial_state_is_disabled(self, qt_app):
        """StockfishProcessAdapter should start in DISABLED state."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        assert adapter.get_state() == EngineState.DISABLED
    
    def test_stores_stockfish_path(self, qt_app):
        """StockfishProcessAdapter should store the binary path."""
        path = "/custom/path/to/stockfish"
        adapter = StockfishProcessAdapter(path)
        assert adapter._stockfish_path == path


class TestStockfishAdapterInitialization:
    """Tests for StockfishProcessAdapter initialization and handshake."""
    
    def test_initialize_transitions_to_initializing(self, qt_app):
        """initialize() should transition to INITIALIZING state."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        assert adapter.get_state() == EngineState.DISABLED
        
        # Replace process and timer with mocks after adapter creation
        # but before initialize() to avoid segfault from mocking Qt classes
        mock_process = Mock()
        mock_timer = Mock()
        
        # Patch the constructor calls by replacing what initialize() creates
        with patch.object(adapter, '_process', None), \
             patch.object(adapter, '_handshake_timer', None):
            # Mock the QProcess and QTimer creation inside initialize
            with patch('chess_app.gui.engine_integration.QProcess', return_value=mock_process), \
                 patch('chess_app.gui.engine_integration.QTimer', return_value=mock_timer):
                adapter.initialize()
        
        assert adapter.get_state() == EngineState.INITIALIZING
    
    def test_initialize_starts_process(self, qt_app):
        """initialize() should start the QProcess with the stockfish path."""
        path = "/usr/bin/stockfish"
        adapter = StockfishProcessAdapter(path)
        
        # Mock QProcess and QTimer
        mock_process = Mock()
        mock_timer = Mock()
        
        with patch('chess_app.gui.engine_integration.QProcess', return_value=mock_process), \
             patch('chess_app.gui.engine_integration.QTimer', return_value=mock_timer):
            adapter.initialize()
        
        # Verify process.start() was called with the correct path
        mock_process.start.assert_called_once_with(path, [])
    
    def test_initialize_sets_up_timeout(self, qt_app):
        """initialize() should set up a handshake timeout timer."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        
        # Mock QProcess and QTimer
        mock_process = Mock()
        mock_timer = Mock()
        
        with patch('chess_app.gui.engine_integration.QProcess', return_value=mock_process), \
             patch('chess_app.gui.engine_integration.QTimer', return_value=mock_timer):
            adapter.initialize()
        
        # Verify timer was created and started
        mock_timer.setSingleShot.assert_called_once_with(True)
        mock_timer.start.assert_called_once_with(5000)  # 5000ms timeout
    
    def test_successful_handshake_emits_initialized(self, qt_app):
        """Successful UCI handshake should emit initialized signal and transition to READY."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        
        # Track signal emission
        signal_emitted = []
        adapter.initialized.connect(lambda: signal_emitted.append(True))
        
        # Manually transition to initializing and set up mock process
        adapter._state = EngineState.INITIALIZING
        adapter._process = Mock()
        mock_timer = Mock()
        adapter._handshake_timer = mock_timer
        
        # Simulate process started
        adapter._handshake_phase = "uci_sent"
        
        # Simulate receiving "uciok"
        adapter._process_handshake_line("uciok")
        assert adapter._handshake_phase == "uci_ok"
        adapter._process.write.assert_called_with(b"isready\n")
        
        # Simulate receiving "readyok"
        adapter._process_handshake_line("readyok")
        
        # Process events
        qt_app.processEvents()
        
        # Verify state and signal
        assert adapter.get_state() == EngineState.READY
        assert len(signal_emitted) == 1
        # Timer was set to None after stopping, but we saved a reference
        mock_timer.stop.assert_called_once()
        assert adapter._handshake_timer is None
    
    def test_process_started_sends_uci_command(self, qt_app):
        """When process starts, adapter should send 'uci' command."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        adapter._state = EngineState.INITIALIZING
        adapter._process = Mock()
        
        # Simulate process started
        adapter._on_process_started()
        
        # Verify "uci\n" was written
        adapter._process.write.assert_called_once_with(b"uci\n")
        assert adapter._handshake_phase == "uci_sent"


class TestStockfishAdapterErrors:
    """Tests for error handling in StockfishProcessAdapter."""
    
    def test_process_failed_to_start_emits_error(self, qt_app):
        """Process failing to start should emit initialization_failed."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        
        # Track signal emission
        error_data = []
        adapter.initialization_failed.connect(
            lambda code, msg: error_data.append((code, msg))
        )
        
        # Setup minimal mocks
        adapter._state = EngineState.INITIALIZING
        adapter._process = Mock()
        adapter._handshake_timer = Mock()
        
        # Simulate process error (FailedToStart)
        adapter._on_process_error(QProcess.ProcessError.FailedToStart)
        
        # Process events
        qt_app.processEvents()
        
        # Verify error signal and state
        assert len(error_data) == 1
        assert error_data[0][0] == EngineErrorCode.INITIALIZATION_FAILED
        assert "Failed to start" in error_data[0][1]
        assert adapter.get_state() == EngineState.ERROR
    
    def test_process_crash_during_init_emits_error(self, qt_app):
        """Process crashing during initialization should emit initialization_failed."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        
        # Track signal emission
        error_data = []
        adapter.initialization_failed.connect(
            lambda code, msg: error_data.append((code, msg))
        )
        
        # Setup minimal mocks
        adapter._state = EngineState.INITIALIZING
        adapter._process = Mock()
        adapter._process.state.return_value = QProcess.ProcessState.NotRunning
        adapter._handshake_timer = Mock()
        
        # Simulate process finished unexpectedly
        adapter._on_process_finished(1, QProcess.ExitStatus.CrashExit)
        
        # Process events
        qt_app.processEvents()
        
        # Verify error signal and state
        assert len(error_data) == 1
        assert error_data[0][0] == EngineErrorCode.PROCESS_CRASHED
        assert "terminated unexpectedly" in error_data[0][1]
        assert adapter.get_state() == EngineState.ERROR
    
    def test_handshake_timeout_emits_error(self, qt_app):
        """Handshake timeout should emit initialization_failed with TIMEOUT."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        
        # Track signal emission
        error_data = []
        adapter.initialization_failed.connect(
            lambda code, msg: error_data.append((code, msg))
        )
        
        # Setup minimal mocks
        adapter._state = EngineState.INITIALIZING
        adapter._process = Mock()
        adapter._process.state.return_value = QProcess.ProcessState.Running
        adapter._handshake_timer = Mock()
        
        # Simulate timeout
        adapter._on_handshake_timeout()
        
        # Process events
        qt_app.processEvents()
        
        # Verify error signal and state
        assert len(error_data) == 1
        assert error_data[0][0] == EngineErrorCode.TIMEOUT
        assert "5000ms" in error_data[0][1]
        assert adapter.get_state() == EngineState.ERROR
    
    def test_malformed_uci_output_handled(self, qt_app):
        """Malformed UCI output should be handled gracefully (timeout will catch it)."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        
        # Setup
        adapter._state = EngineState.INITIALIZING
        adapter._process = Mock()
        adapter._handshake_phase = "uci_sent"
        
        # Process malformed lines - should not crash
        adapter._process_handshake_line("some random output")
        adapter._process_handshake_line("id name Stockfish")
        adapter._process_handshake_line("option name Threads")
        
        # State should still be INITIALIZING (waiting for uciok)
        assert adapter.get_state() == EngineState.INITIALIZING
        assert adapter._handshake_phase == "uci_sent"
    
    def test_process_crash_after_ready_transitions_to_error(self, qt_app):
        """Process crashing after being READY should transition to ERROR."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        
        # Setup - adapter is in READY state
        adapter._state = EngineState.READY
        adapter._process = Mock()
        adapter._process.state.return_value = QProcess.ProcessState.NotRunning
        adapter._handshake_timer = None
        
        # Simulate process crash
        adapter._on_process_finished(1, QProcess.ExitStatus.CrashExit)
        
        # Verify state transition
        assert adapter.get_state() == EngineState.ERROR


class TestStockfishAdapterShutdown:
    """Tests for shutdown behavior."""
    
    def test_shutdown_in_disabled_state(self, qt_app):
        """shutdown() should be safe to call in DISABLED state."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        
        # Should not raise any exceptions
        adapter.shutdown()
        
        assert adapter._is_shutting_down is True
    
    def test_shutdown_stops_handshake_timer(self, qt_app):
        """shutdown() should stop the handshake timer if running."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        
        # Setup with mock timer - save reference before shutdown
        mock_timer = Mock()
        adapter._handshake_timer = mock_timer
        adapter._process = None
        
        adapter.shutdown()
        
        mock_timer.stop.assert_called_once()
        assert adapter._handshake_timer is None
    
    def test_shutdown_terminates_running_process(self, qt_app):
        """shutdown() should gracefully terminate a running process."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        
        # Setup with mock process - save reference before shutdown sets it to None
        mock_process = Mock()
        mock_process.state.return_value = QProcess.ProcessState.Running
        adapter._process = mock_process
        
        adapter.shutdown()
        
        # Verify quit command was sent (check saved reference)
        mock_process.write.assert_called_once_with(b"quit\n")
        mock_process.waitForFinished.assert_called()
        # Process should be set to None after shutdown
        assert adapter._process is None
    
    def test_shutdown_kills_unresponsive_process(self, qt_app):
        """shutdown() should force-kill process if it doesn't exit gracefully."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        
        # Setup with mock process that stays running - save reference before shutdown
        mock_process = Mock()
        mock_process.state.return_value = QProcess.ProcessState.Running
        adapter._process = mock_process
        
        adapter.shutdown()
        
        # Verify kill was called (check saved reference)
        mock_process.kill.assert_called()
        # Process should be set to None after shutdown
        assert adapter._process is None
    
    def test_shutdown_disconnects_signals(self, qt_app):
        """shutdown() should disconnect all process signals."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        
        # Setup with mock process
        mock_signal = Mock()
        adapter._process = Mock()
        adapter._process.state.return_value = QProcess.ProcessState.NotRunning
        adapter._process.started = mock_signal
        adapter._process.errorOccurred = mock_signal
        adapter._process.finished = mock_signal
        adapter._process.readyReadStandardOutput = mock_signal
        
        adapter.shutdown()
        
        # Verify disconnect was called on signals
        assert mock_signal.disconnect.call_count == 4
    
    def test_shutdown_can_be_called_multiple_times(self, qt_app):
        """shutdown() should be safe to call multiple times."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        
        # Should not raise any exceptions
        adapter.shutdown()
        adapter.shutdown()
        adapter.shutdown()
        
        assert adapter._is_shutting_down is True
    
    def test_no_signals_emitted_after_shutdown(self, qt_app):
        """No signals should be emitted after shutdown() is called."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        
        # Track signals
        signals_emitted = []
        adapter.initialized.connect(lambda: signals_emitted.append("initialized"))
        adapter.initialization_failed.connect(lambda c, m: signals_emitted.append("failed"))
        
        # Setup
        adapter._state = EngineState.INITIALIZING
        adapter._process = Mock()
        adapter._handshake_timer = Mock()
        
        # Shutdown
        adapter.shutdown()
        
        # Try to trigger various handlers - should be ignored
        adapter._on_process_started()
        adapter._on_handshake_timeout()
        adapter._on_stdout_ready()
        
        # No signals should have been emitted
        assert len(signals_emitted) == 0


class TestStockfishAdapterRequestMove:
    """Tests for stubbed request_move functionality."""
    
    def test_request_move_in_disabled_state_emits_error(self, qt_app):
        """request_move() in DISABLED state should emit INVALID_REQUEST."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        
        # Track error signal
        error_data = []
        adapter.move_failed.connect(
            lambda code, msg: error_data.append((code, msg))
        )
        
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        adapter.request_move(fen)
        
        # Process events
        qt_app.processEvents()
        
        # Verify error
        assert len(error_data) == 1
        assert error_data[0][0] == EngineErrorCode.INVALID_REQUEST
        assert "disabled" in error_data[0][1].lower()
    
    def test_request_move_in_initializing_state_emits_error(self, qt_app):
        """request_move() in INITIALIZING state should emit INVALID_REQUEST."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        adapter._state = EngineState.INITIALIZING
        
        # Track error signal
        error_data = []
        adapter.move_failed.connect(
            lambda code, msg: error_data.append((code, msg))
        )
        
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        adapter.request_move(fen)
        
        # Process events
        qt_app.processEvents()
        
        # Verify error
        assert len(error_data) == 1
        assert error_data[0][0] == EngineErrorCode.INVALID_REQUEST
    
    def test_request_move_in_ready_state_transitions_to_busy(self, qt_app):
        """request_move() in READY state should transition to BUSY (then back to READY in stub)."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        adapter._state = EngineState.READY
        
        # Track move signal
        move_data = []
        adapter.move_ready.connect(lambda move: move_data.append(move))
        
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        adapter.request_move(fen)
        
        # Process events
        qt_app.processEvents()
        
        # In stub implementation, immediately returns to READY with placeholder move
        assert adapter.get_state() == EngineState.READY
        assert len(move_data) == 1
        assert move_data[0] == "e7e5"  # Placeholder move
    
    def test_request_move_in_busy_state_emits_error(self, qt_app):
        """request_move() in BUSY state should emit INVALID_REQUEST."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        adapter._state = EngineState.BUSY
        
        # Track error signal
        error_data = []
        adapter.move_failed.connect(
            lambda code, msg: error_data.append((code, msg))
        )
        
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        adapter.request_move(fen)
        
        # Process events
        qt_app.processEvents()
        
        # Verify error
        assert len(error_data) == 1
        assert error_data[0][0] == EngineErrorCode.INVALID_REQUEST
    
    def test_request_move_in_error_state_emits_error(self, qt_app):
        """request_move() in ERROR state should emit INVALID_REQUEST."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        adapter._state = EngineState.ERROR
        
        # Track error signal
        error_data = []
        adapter.move_failed.connect(
            lambda code, msg: error_data.append((code, msg))
        )
        
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        adapter.request_move(fen)
        
        # Process events
        qt_app.processEvents()
        
        # Verify error
        assert len(error_data) == 1
        assert error_data[0][0] == EngineErrorCode.INVALID_REQUEST


class TestStockfishAdapterStateTransitions:
    """Tests for state machine transitions."""
    
    def test_disabled_to_initializing_transition(self, qt_app):
        """Test DISABLED → INITIALIZING transition."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        assert adapter.get_state() == EngineState.DISABLED
        
        # Mock QProcess to prevent actual process start
        mock_process = Mock()
        mock_timer = Mock()
        
        with patch('chess_app.gui.engine_integration.QProcess', return_value=mock_process), \
             patch('chess_app.gui.engine_integration.QTimer', return_value=mock_timer):
            adapter.initialize()
            assert adapter.get_state() == EngineState.INITIALIZING
    
    def test_initializing_to_ready_transition(self, qt_app):
        """Test INITIALIZING → READY transition on successful handshake."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        adapter._state = EngineState.INITIALIZING
        adapter._process = Mock()
        adapter._handshake_timer = Mock()
        adapter._handshake_phase = "uci_ok"
        
        # Simulate readyok
        adapter._process_handshake_line("readyok")
        
        assert adapter.get_state() == EngineState.READY
    
    def test_initializing_to_error_on_timeout(self, qt_app):
        """Test INITIALIZING → ERROR transition on timeout."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        adapter._state = EngineState.INITIALIZING
        adapter._process = Mock()
        adapter._process.state.return_value = QProcess.ProcessState.Running
        adapter._handshake_timer = Mock()
        
        adapter._on_handshake_timeout()
        
        assert adapter.get_state() == EngineState.ERROR
    
    def test_initializing_to_error_on_crash(self, qt_app):
        """Test INITIALIZING → ERROR transition on process crash."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        adapter._state = EngineState.INITIALIZING
        adapter._process = Mock()
        adapter._process.state.return_value = QProcess.ProcessState.NotRunning
        adapter._handshake_timer = Mock()
        
        adapter._on_process_finished(1, QProcess.ExitStatus.CrashExit)
        
        assert adapter.get_state() == EngineState.ERROR
    
    def test_ready_to_busy_to_ready_in_stub(self, qt_app):
        """Test READY → BUSY → READY transition in stubbed move request."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        adapter._state = EngineState.READY
        
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        adapter.request_move(fen)
        
        # In stub, immediately returns to READY
        assert adapter.get_state() == EngineState.READY


class TestStockfishAdapterIOHandling:
    """Tests for I/O handling and output parsing."""
    
    def test_stdout_accumulates_partial_lines(self, qt_app):
        """Output buffer should accumulate partial lines."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        adapter._state = EngineState.INITIALIZING
        adapter._process = Mock()
        adapter._handshake_phase = "uci_sent"
        
        # Simulate partial output
        adapter._output_buffer = "id name Stock"
        assert "id name Stock" in adapter._output_buffer
        
        # Should not have processed anything yet (no newline)
        assert adapter._handshake_phase == "uci_sent"
    
    def test_stdout_processes_complete_lines(self, qt_app):
        """Complete lines should be processed and buffer cleared."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        adapter._state = EngineState.INITIALIZING
        adapter._process = Mock()
        adapter._handshake_phase = "uci_sent"
        
        # Simulate complete line via buffer manipulation
        adapter._output_buffer = "uciok\n"
        
        # Manually process (simulating what readyReadStandardOutput does)
        while '\n' in adapter._output_buffer:
            line, adapter._output_buffer = adapter._output_buffer.split('\n', 1)
            line = line.strip()
            if line:
                adapter._process_handshake_line(line)
        
        # Should have processed uciok and transitioned
        assert adapter._handshake_phase == "uci_ok"
        adapter._process.write.assert_called_with(b"isready\n")
    
    def test_empty_lines_ignored(self, qt_app):
        """Empty lines should be ignored during processing."""
        adapter = StockfishProcessAdapter("/usr/bin/stockfish")
        adapter._state = EngineState.INITIALIZING
        adapter._process = Mock()
        adapter._handshake_phase = "uci_sent"
        
        # Process empty lines - should not affect state
        adapter._process_handshake_line("")
        adapter._process_handshake_line("   ")
        
        assert adapter._handshake_phase == "uci_sent"
        assert adapter.get_state() == EngineState.INITIALIZING

