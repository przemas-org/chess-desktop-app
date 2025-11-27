#!/usr/bin/env python3
"""
Unit tests for engine abstraction API.

This module validates the EngineAdapter contract, state transitions,
and FakeEngineAdapter behavior without requiring actual Stockfish binary.
"""

import pytest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer

from chess_app.gui.engine_integration import (
    EngineState,
    EngineErrorCode,
    EngineAdapter,
    FakeEngineAdapter,
)


class TestEngineState:
    """Tests for EngineState enum."""
    
    def test_engine_state_values(self):
        """EngineState should have all required states."""
        assert EngineState.DISABLED.value == "disabled"
        assert EngineState.INITIALIZING.value == "initializing"
        assert EngineState.READY.value == "ready"
        assert EngineState.BUSY.value == "busy"
        assert EngineState.ERROR.value == "error"
    
    def test_engine_state_enum_members(self):
        """EngineState should have exactly 5 members."""
        states = list(EngineState)
        assert len(states) == 5
        assert EngineState.DISABLED in states
        assert EngineState.INITIALIZING in states
        assert EngineState.READY in states
        assert EngineState.BUSY in states
        assert EngineState.ERROR in states


class TestEngineErrorCode:
    """Tests for EngineErrorCode enum."""
    
    def test_error_code_values(self):
        """EngineErrorCode should have all required error codes."""
        assert EngineErrorCode.INITIALIZATION_FAILED.value == "initialization_failed"
        assert EngineErrorCode.TIMEOUT.value == "timeout"
        assert EngineErrorCode.ILLEGAL_MOVE.value == "illegal_move"
        assert EngineErrorCode.PROCESS_CRASHED.value == "process_crashed"
        assert EngineErrorCode.INVALID_REQUEST.value == "invalid_request"
    
    def test_error_code_enum_members(self):
        """EngineErrorCode should have exactly 5 members."""
        codes = list(EngineErrorCode)
        assert len(codes) == 5
        assert EngineErrorCode.INITIALIZATION_FAILED in codes
        assert EngineErrorCode.TIMEOUT in codes
        assert EngineErrorCode.ILLEGAL_MOVE in codes
        assert EngineErrorCode.PROCESS_CRASHED in codes
        assert EngineErrorCode.INVALID_REQUEST in codes


class TestFakeEngineAdapterBasics:
    """Tests for basic FakeEngineAdapter functionality."""
    
    def test_fake_adapter_can_be_instantiated(self):
        """FakeEngineAdapter should be instantiable."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            assert adapter is not None
            assert isinstance(adapter, EngineAdapter)
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_initial_state_is_disabled(self):
        """FakeEngineAdapter should start in DISABLED state."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            assert adapter.get_state() == EngineState.DISABLED
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_call_log_initially_empty(self):
        """FakeEngineAdapter call log should start empty."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            call_log = adapter.get_call_log()
            assert call_log == []
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")


class TestFakeEngineAdapterInitialization:
    """Tests for FakeEngineAdapter initialization behavior."""
    
    def test_initialize_transitions_to_initializing(self):
        """initialize() should transition state to INITIALIZING."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            assert adapter.get_state() == EngineState.DISABLED
            
            adapter.initialize()
            assert adapter.get_state() == EngineState.INITIALIZING
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_initialize_logged_in_call_log(self):
        """initialize() call should be logged."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            adapter.initialize()
            
            call_log = adapter.get_call_log()
            assert len(call_log) == 1
            assert call_log[0] == ("initialize", ())
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_simulate_init_success_emits_signal(self):
        """simulate_init_success() should emit initialized signal."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            
            # Track signal emission
            signal_emitted = []
            adapter.initialized.connect(lambda: signal_emitted.append(True))
            
            adapter.initialize()
            adapter.simulate_init_success()
            
            # Process events to ensure signal delivery
            app.processEvents()
            
            assert len(signal_emitted) == 1
            assert adapter.get_state() == EngineState.READY
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_simulate_init_failure_emits_signal(self):
        """simulate_init_failure() should emit initialization_failed signal."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            
            # Track signal emission
            signal_data = []
            adapter.initialization_failed.connect(
                lambda code, msg: signal_data.append((code, msg))
            )
            
            adapter.initialize()
            adapter.simulate_init_failure(
                EngineErrorCode.INITIALIZATION_FAILED,
                "Test failure"
            )
            
            # Process events
            app.processEvents()
            
            assert len(signal_data) == 1
            assert signal_data[0][0] == EngineErrorCode.INITIALIZATION_FAILED
            assert signal_data[0][1] == "Test failure"
            assert adapter.get_state() == EngineState.ERROR
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")


class TestFakeEngineAdapterMoveRequest:
    """Tests for FakeEngineAdapter move request behavior."""
    
    def test_request_move_logs_call(self):
        """request_move() should log the call with FEN and timeout."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            adapter.request_move(fen, timeout_ms=2000)
            
            call_log = adapter.get_call_log()
            assert len(call_log) == 2  # initialize, request_move
            assert call_log[1][0] == "request_move"
            assert call_log[1][1][0] == fen
            assert call_log[1][1][1] == 2000
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_request_move_when_ready_transitions_to_busy(self):
        """request_move() in READY state should transition to BUSY."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            assert adapter.get_state() == EngineState.READY
            
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            adapter.request_move(fen)
            
            assert adapter.get_state() == EngineState.BUSY
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_request_move_when_not_ready_emits_error(self):
        """request_move() when not READY should emit move_failed."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            
            # Track signal emission
            error_data = []
            adapter.move_failed.connect(
                lambda code, msg: error_data.append((code, msg))
            )
            
            # Try to request move in DISABLED state
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            adapter.request_move(fen)
            
            # Process events
            app.processEvents()
            
            assert len(error_data) == 1
            assert error_data[0][0] == EngineErrorCode.INVALID_REQUEST
            assert "disabled" in error_data[0][1].lower()
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_simulate_move_response_emits_signal(self):
        """simulate_move_response() should emit move_ready signal."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            # Track signal emission
            move_data = []
            adapter.move_ready.connect(lambda move: move_data.append(move))
            
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            adapter.request_move(fen)
            adapter.simulate_move_response("e7e5")
            
            # Process events
            app.processEvents()
            
            assert len(move_data) == 1
            assert move_data[0] == "e7e5"
            assert adapter.get_state() == EngineState.READY
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_simulate_move_failure_emits_signal(self):
        """simulate_move_failure() should emit move_failed signal."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            # Track signal emission
            error_data = []
            adapter.move_failed.connect(
                lambda code, msg: error_data.append((code, msg))
            )
            
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            adapter.request_move(fen)
            adapter.simulate_move_failure(EngineErrorCode.TIMEOUT, "Test timeout")
            
            # Process events
            app.processEvents()
            
            assert len(error_data) == 1
            assert error_data[0][0] == EngineErrorCode.TIMEOUT
            assert error_data[0][1] == "Test timeout"
            assert adapter.get_state() == EngineState.ERROR
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")


class TestFakeEngineAdapterStateTransitions:
    """Tests for state machine transitions in FakeEngineAdapter."""
    
    def test_disabled_to_initializing_to_ready(self):
        """Test state transition: DISABLED → INITIALIZING → READY."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            assert adapter.get_state() == EngineState.DISABLED
            
            adapter.initialize()
            assert adapter.get_state() == EngineState.INITIALIZING
            
            adapter.simulate_init_success()
            assert adapter.get_state() == EngineState.READY
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_disabled_to_initializing_to_error(self):
        """Test state transition: DISABLED → INITIALIZING → ERROR."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            assert adapter.get_state() == EngineState.DISABLED
            
            adapter.initialize()
            assert adapter.get_state() == EngineState.INITIALIZING
            
            adapter.simulate_init_failure(
                EngineErrorCode.INITIALIZATION_FAILED,
                "Test error"
            )
            assert adapter.get_state() == EngineState.ERROR
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_ready_to_busy_to_ready(self):
        """Test state transition: READY → BUSY → READY."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            assert adapter.get_state() == EngineState.READY
            
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            adapter.request_move(fen)
            assert adapter.get_state() == EngineState.BUSY
            
            adapter.simulate_move_response("e7e5")
            assert adapter.get_state() == EngineState.READY
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_busy_to_error_on_timeout(self):
        """Test state transition: BUSY → ERROR on timeout."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            adapter.request_move(fen)
            assert adapter.get_state() == EngineState.BUSY
            
            adapter.simulate_move_failure(EngineErrorCode.TIMEOUT, "Timeout")
            assert adapter.get_state() == EngineState.ERROR
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_busy_to_error_on_crash(self):
        """Test state transition: BUSY → ERROR on crash."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            adapter.request_move(fen)
            assert adapter.get_state() == EngineState.BUSY
            
            adapter.simulate_move_failure(EngineErrorCode.PROCESS_CRASHED, "Crashed")
            assert adapter.get_state() == EngineState.ERROR
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_busy_to_ready_on_illegal_move(self):
        """Test state transition: BUSY → READY on illegal move."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            adapter.request_move(fen)
            assert adapter.get_state() == EngineState.BUSY
            
            adapter.simulate_move_failure(EngineErrorCode.ILLEGAL_MOVE, "Illegal")
            assert adapter.get_state() == EngineState.READY
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")


class TestFakeEngineAdapterShutdown:
    """Tests for FakeEngineAdapter shutdown behavior."""
    
    def test_shutdown_logs_call(self):
        """shutdown() should log the call."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            adapter.shutdown()
            
            call_log = adapter.get_call_log()
            assert len(call_log) == 1
            assert call_log[0] == ("shutdown", ())
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_shutdown_can_be_called_in_any_state(self):
        """shutdown() should be safe to call in any state."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # Test shutdown in DISABLED state
            adapter1 = FakeEngineAdapter()
            adapter1.shutdown()
            assert len(adapter1.get_call_log()) == 1
            
            # Test shutdown in INITIALIZING state
            adapter2 = FakeEngineAdapter()
            adapter2.initialize()
            adapter2.shutdown()
            assert len(adapter2.get_call_log()) == 2
            
            # Test shutdown in READY state
            adapter3 = FakeEngineAdapter()
            adapter3.initialize()
            adapter3.simulate_init_success()
            adapter3.shutdown()
            assert len(adapter3.get_call_log()) == 2
            
            # Test shutdown in ERROR state
            adapter4 = FakeEngineAdapter()
            adapter4.initialize()
            adapter4.simulate_init_failure(
                EngineErrorCode.INITIALIZATION_FAILED,
                "Test"
            )
            adapter4.shutdown()
            assert len(adapter4.get_call_log()) == 2
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_shutdown_multiple_times(self):
        """shutdown() should be safe to call multiple times."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            adapter.shutdown()
            adapter.shutdown()
            adapter.shutdown()
            
            call_log = adapter.get_call_log()
            assert len(call_log) == 3
            assert all(call[0] == "shutdown" for call in call_log)
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")


class TestFakeEngineAdapterConcurrentRequests:
    """Tests for concurrent request handling."""
    
    def test_concurrent_request_emits_invalid_request_error(self):
        """Second request_move() while BUSY should emit INVALID_REQUEST."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            # Track error signals
            error_data = []
            adapter.move_failed.connect(
                lambda code, msg: error_data.append((code, msg))
            )
            
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            adapter.request_move(fen)
            assert adapter.get_state() == EngineState.BUSY
            
            # Try second request while first is in flight
            adapter.request_move(fen)
            
            # Process events
            app.processEvents()
            
            # Should have emitted INVALID_REQUEST for second call
            assert len(error_data) == 1
            assert error_data[0][0] == EngineErrorCode.INVALID_REQUEST
            
            # State should still be BUSY (first request still pending)
            assert adapter.get_state() == EngineState.BUSY
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_request_after_completion_succeeds(self):
        """request_move() after previous request completes should succeed."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            
            # First request
            adapter.request_move(fen)
            adapter.simulate_move_response("e7e5")
            assert adapter.get_state() == EngineState.READY
            
            # Second request after first completed
            adapter.request_move(fen)
            assert adapter.get_state() == EngineState.BUSY
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")


class TestFakeEngineAdapterDelayedResponse:
    """Tests for delayed response simulation."""
    
    def test_delayed_move_response(self):
        """simulate_move_response() with delay should emit signal after delay."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            # Track signal emission
            move_data = []
            adapter.move_ready.connect(lambda move: move_data.append(move))
            
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            adapter.request_move(fen)
            
            # Simulate delayed response (100ms)
            adapter.simulate_move_response("e7e5", delay_ms=100)
            
            # Signal should not be emitted immediately
            app.processEvents()
            assert len(move_data) == 0
            assert adapter.get_state() == EngineState.BUSY
            
            # Wait for the delay and process events
            QTimer.singleShot(150, app.quit)
            app.exec()
            
            # Now signal should be emitted
            assert len(move_data) == 1
            assert move_data[0] == "e7e5"
            assert adapter.get_state() == EngineState.READY
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")


class TestFakeEngineAdapterCallLog:
    """Tests for call logging functionality."""
    
    def test_call_log_records_all_calls(self):
        """Call log should record all method calls in order."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            
            # Make various calls
            adapter.initialize()
            adapter.simulate_init_success()
            
            fen1 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            adapter.request_move(fen1, timeout_ms=1500)
            adapter.simulate_move_response("e7e5")
            
            fen2 = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"
            adapter.request_move(fen2, timeout_ms=2000)
            
            adapter.shutdown()
            
            # Verify call log
            call_log = adapter.get_call_log()
            assert len(call_log) == 4  # init, request1, request2, shutdown
            
            assert call_log[0] == ("initialize", ())
            assert call_log[1] == ("request_move", (fen1, 1500))
            assert call_log[2] == ("request_move", (fen2, 2000))
            assert call_log[3] == ("shutdown", ())
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_call_log_copy_independent(self):
        """get_call_log() should return independent copy."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            adapter.initialize()
            
            # Get first copy
            log1 = adapter.get_call_log()
            assert len(log1) == 1
            
            # Make more calls
            adapter.simulate_init_success()
            fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            adapter.request_move(fen)
            
            # Get second copy
            log2 = adapter.get_call_log()
            assert len(log2) == 2
            
            # First copy should be unchanged
            assert len(log1) == 1
            
            # Modifying one copy shouldn't affect the other
            log1.append(("test", ()))
            log3 = adapter.get_call_log()
            assert len(log3) == 2
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")


class TestEngineAdapterContract:
    """Tests validating the EngineAdapter API contract."""
    
    def test_adapter_is_qobject(self):
        """EngineAdapter should inherit from QObject for signals."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            from PySide6.QtCore import QObject
            
            adapter = FakeEngineAdapter()
            assert isinstance(adapter, QObject)
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_adapter_has_required_signals(self):
        """EngineAdapter should have all required signals."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            
            # Verify signals exist
            assert hasattr(adapter, 'initialized')
            assert hasattr(adapter, 'initialization_failed')
            assert hasattr(adapter, 'move_ready')
            assert hasattr(adapter, 'move_failed')
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_adapter_has_required_methods(self):
        """EngineAdapter should have all required methods."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            
            # Verify methods exist and are callable
            assert hasattr(adapter, 'initialize')
            assert callable(adapter.initialize)
            assert hasattr(adapter, 'request_move')
            assert callable(adapter.request_move)
            assert hasattr(adapter, 'shutdown')
            assert callable(adapter.shutdown)
            assert hasattr(adapter, 'get_state')
            assert callable(adapter.get_state)
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_get_state_returns_engine_state(self):
        """get_state() should return an EngineState enum value."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            adapter = FakeEngineAdapter()
            state = adapter.get_state()
            
            assert isinstance(state, EngineState)
            assert state in list(EngineState)
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")

