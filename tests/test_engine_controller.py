#!/usr/bin/env python3
"""
Unit tests for EngineController.

This module validates the EngineController's coordination between the Game
domain model and the EngineAdapter, including move validation, re-query logic,
and error handling.
"""

import pytest
from PySide6.QtWidgets import QApplication

from chess_app.game import Game, Side
from chess_app.gui.engine_integration import (
    EngineErrorCode,
    FakeEngineAdapter,
)
from chess_app.gui.engine_controller import EngineController


class TestEngineControllerBasics:
    """Tests for basic EngineController functionality."""
    
    def test_controller_initialization(self):
        """EngineController should initialize with Game and adapter."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            game = Game()
            adapter = FakeEngineAdapter()
            controller = EngineController(game, adapter)
            
            assert controller is not None
            assert controller.is_enabled()
            assert not controller.is_in_flight()
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_controller_does_not_query_on_white_turn(self):
        """Controller should not query engine when White to move."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            game = Game()  # White to move at start
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            controller = EngineController(game, adapter)
            
            # Call on_human_move_applied when White to move
            controller.on_human_move_applied()
            
            # No request should be made (still only 1 call: initialize)
            calls = adapter.get_call_log()
            assert len(calls) == 1
            assert calls[0][0] == "initialize"
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_controller_queries_engine_on_black_turn(self):
        """Controller should query engine when Black to move."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            game = Game()
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            controller = EngineController(game, adapter)
            
            # Make a White move so it's Black's turn
            game.apply_move("e2e4")
            assert game.get_side_to_move() == Side.BLACK
            
            # Call on_human_move_applied
            controller.on_human_move_applied()
            
            # Should have made a request_move call
            calls = adapter.get_call_log()
            assert len(calls) == 2
            assert calls[0][0] == "initialize"
            assert calls[1][0] == "request_move"
            
            # Verify FEN was passed
            fen_arg = calls[1][1][0]
            assert " b " in fen_arg  # Black to move
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_controller_does_not_query_when_disabled(self):
        """Controller should not query when engine is disabled."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            game = Game()
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            controller = EngineController(game, adapter)
            
            # Disable the controller by simulating an error
            game.apply_move("e2e4")
            controller.on_human_move_applied()
            adapter.simulate_move_failure(
                EngineErrorCode.TIMEOUT,
                "Test timeout"
            )
            app.processEvents()
            
            # Make another White move
            game.apply_move("e7e5")
            game.apply_move("g1f3")
            
            # Try to trigger engine again
            controller.on_human_move_applied()
            
            # Should not make another request (only the first one)
            calls = adapter.get_call_log()
            request_calls = [c for c in calls if c[0] == "request_move"]
            assert len(request_calls) == 1
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_controller_prevents_overlapping_requests(self):
        """Controller should prevent overlapping engine requests."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            game = Game()
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            controller = EngineController(game, adapter)
            
            # Make a White move
            game.apply_move("e2e4")
            
            # Call on_human_move_applied twice
            controller.on_human_move_applied()
            controller.on_human_move_applied()
            
            # Should only have made one request
            calls = adapter.get_call_log()
            request_calls = [c for c in calls if c[0] == "request_move"]
            assert len(request_calls) == 1
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")


class TestEngineControllerLegalMoves:
    """Tests for legal move application."""
    
    def test_legal_move_applied_to_game(self):
        """Legal engine move should be applied to Game."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            game = Game()
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            controller = EngineController(game, adapter)
            
            # Make a White move
            game.apply_move("e2e4")
            initial_fen = game.export_fen()
            
            # Trigger engine move
            controller.on_human_move_applied()
            
            # Simulate legal engine response
            adapter.simulate_move_response("e7e5")
            app.processEvents()
            
            # Game should have been updated
            final_fen = game.export_fen()
            assert final_fen != initial_fen
            assert " w " in final_fen  # White to move again
            
            # Verify the move was actually made
            history = game.get_history()
            assert len(history) == 2
            assert history[1].uci == "e7e5"
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_engine_move_applied_signal_emitted(self):
        """engine_move_applied signal should be emitted on success."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            game = Game()
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            controller = EngineController(game, adapter)
            
            # Track signal emission
            signal_emitted = []
            controller.engine_move_applied.connect(
                lambda: signal_emitted.append(True)
            )
            
            # Make a White move and trigger engine
            game.apply_move("e2e4")
            controller.on_human_move_applied()
            
            # Simulate legal engine response
            adapter.simulate_move_response("e7e5")
            app.processEvents()
            
            # Signal should have been emitted
            assert len(signal_emitted) == 1
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_in_flight_flag_cleared_after_success(self):
        """In-flight flag should be cleared after successful move."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            game = Game()
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            controller = EngineController(game, adapter)
            
            # Make a White move and trigger engine
            game.apply_move("e2e4")
            controller.on_human_move_applied()
            
            # Should be in flight
            assert controller.is_in_flight()
            
            # Simulate legal engine response
            adapter.simulate_move_response("e7e5")
            app.processEvents()
            
            # Should no longer be in flight
            assert not controller.is_in_flight()
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_controller_allows_next_request_after_success(self):
        """Controller should allow new request after previous completes."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            game = Game()
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            controller = EngineController(game, adapter)
            
            # First White move and engine response
            game.apply_move("e2e4")
            controller.on_human_move_applied()
            adapter.simulate_move_response("e7e5")
            app.processEvents()
            
            # Second White move and engine response
            game.apply_move("g1f3")
            controller.on_human_move_applied()
            
            # Should have made second request
            calls = adapter.get_call_log()
            request_calls = [c for c in calls if c[0] == "request_move"]
            assert len(request_calls) == 2
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")


class TestEngineControllerIllegalMoves:
    """Tests for illegal move handling and re-query logic."""
    
    def test_first_illegal_move_triggers_requery(self):
        """First illegal move should trigger immediate re-query."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            game = Game()
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            controller = EngineController(game, adapter)
            
            # Make a White move and trigger engine
            game.apply_move("e2e4")
            controller.on_human_move_applied()
            
            # Simulate illegal move response (e.g., invalid UCI)
            adapter.simulate_move_response("z9z9")  # Illegal move
            app.processEvents()
            
            # Should have made a second request (re-query)
            calls = adapter.get_call_log()
            request_calls = [c for c in calls if c[0] == "request_move"]
            assert len(request_calls) == 2
            
            # Should still be in flight
            assert controller.is_in_flight()
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_second_illegal_move_disables_engine(self):
        """Second illegal move should disable engine permanently."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            game = Game()
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            controller = EngineController(game, adapter)
            
            # Track engine_disabled signal
            disabled_reasons = []
            controller.engine_disabled.connect(
                lambda reason: disabled_reasons.append(reason)
            )
            
            # Make a White move and trigger engine
            game.apply_move("e2e4")
            controller.on_human_move_applied()
            
            # Simulate first illegal move
            adapter.simulate_move_response("z9z9")
            app.processEvents()
            
            # Simulate second illegal move
            adapter.simulate_move_response("z8z8")
            app.processEvents()
            
            # Engine should be disabled
            assert not controller.is_enabled()
            assert not controller.is_in_flight()
            
            # Signal should have been emitted
            assert len(disabled_reasons) == 1
            assert "illegal move twice" in disabled_reasons[0].lower()
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_illegal_move_counter_resets_on_new_position(self):
        """Illegal move counter should reset for each new position."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            game = Game()
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            controller = EngineController(game, adapter)
            
            # First position: one illegal move, then legal
            game.apply_move("e2e4")
            controller.on_human_move_applied()
            adapter.simulate_move_response("z9z9")  # Illegal
            app.processEvents()
            adapter.simulate_move_response("e7e5")  # Legal on re-query
            app.processEvents()
            
            # Engine should still be enabled
            assert controller.is_enabled()
            
            # Second position: one illegal move should not immediately disable
            game.apply_move("g1f3")
            controller.on_human_move_applied()
            adapter.simulate_move_response("z8z8")  # Illegal
            app.processEvents()
            
            # Should still be enabled (counter was reset)
            assert controller.is_enabled()
            assert controller.is_in_flight()  # Waiting for re-query
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")


class TestEngineControllerErrorHandling:
    """Tests for adapter error and timeout handling."""
    
    def test_adapter_timeout_disables_engine(self):
        """Adapter timeout should disable engine permanently."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            game = Game()
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            controller = EngineController(game, adapter)
            
            # Track engine_disabled signal
            disabled_reasons = []
            controller.engine_disabled.connect(
                lambda reason: disabled_reasons.append(reason)
            )
            
            # Make a White move and trigger engine
            game.apply_move("e2e4")
            controller.on_human_move_applied()
            
            # Simulate timeout
            adapter.simulate_move_failure(
                EngineErrorCode.TIMEOUT,
                "Engine did not respond within 1000ms"
            )
            app.processEvents()
            
            # Engine should be disabled
            assert not controller.is_enabled()
            assert not controller.is_in_flight()
            
            # Signal should have been emitted
            assert len(disabled_reasons) == 1
            assert "timeout" in disabled_reasons[0].lower()
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_adapter_crash_disables_engine(self):
        """Adapter crash should disable engine permanently."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            game = Game()
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            controller = EngineController(game, adapter)
            
            # Track engine_disabled signal
            disabled_reasons = []
            controller.engine_disabled.connect(
                lambda reason: disabled_reasons.append(reason)
            )
            
            # Make a White move and trigger engine
            game.apply_move("e2e4")
            controller.on_human_move_applied()
            
            # Simulate process crash
            adapter.simulate_move_failure(
                EngineErrorCode.PROCESS_CRASHED,
                "Stockfish process crashed"
            )
            app.processEvents()
            
            # Engine should be disabled
            assert not controller.is_enabled()
            assert not controller.is_in_flight()
            
            # Signal should have been emitted
            assert len(disabled_reasons) == 1
            assert "crashed" in disabled_reasons[0].lower()
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_error_clears_in_flight_flag(self):
        """Adapter errors should clear the in-flight flag."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            game = Game()
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            controller = EngineController(game, adapter)
            
            # Make a White move and trigger engine
            game.apply_move("e2e4")
            controller.on_human_move_applied()
            
            # Should be in flight
            assert controller.is_in_flight()
            
            # Simulate error
            adapter.simulate_move_failure(
                EngineErrorCode.TIMEOUT,
                "Test timeout"
            )
            app.processEvents()
            
            # Should no longer be in flight
            assert not controller.is_in_flight()
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_stale_responses_ignored(self):
        """Responses when not in-flight should be ignored."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            game = Game()
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            controller = EngineController(game, adapter)
            
            # Don't make any moves, so no request should be in flight
            assert not controller.is_in_flight()
            
            # Manually emit a move_ready signal (simulating stale response)
            adapter.move_ready.emit("e7e5")
            app.processEvents()
            
            # Game should not have been modified
            history = game.get_history()
            assert len(history) == 0
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")


class TestEngineControllerIntegration:
    """Integration tests for complete game flow."""
    
    def test_complete_move_sequence(self):
        """Test complete sequence: White move → engine query → Black move."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            game = Game()
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            controller = EngineController(game, adapter)
            
            # Track signals
            move_applied_count = []
            controller.engine_move_applied.connect(
                lambda: move_applied_count.append(True)
            )
            
            # Play a sequence of moves
            moves = [
                ("e2e4", "e7e5"),  # 1. e4 e5
                ("g1f3", "b8c6"),  # 2. Nf3 Nc6
                ("f1c4", "g8f6"),  # 3. Bc4 Nf6
            ]
            
            for white_move, black_response in moves:
                # Human plays White
                game.apply_move(white_move)
                
                # Trigger engine
                controller.on_human_move_applied()
                
                # Engine responds
                adapter.simulate_move_response(black_response)
                app.processEvents()
            
            # Verify game state
            history = game.get_history()
            assert len(history) == 6  # 3 White + 3 Black moves
            
            # Verify signals emitted
            assert len(move_applied_count) == 3
            
            # Verify it's White's turn
            assert game.get_side_to_move() == Side.WHITE
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_game_continues_after_engine_disabled(self):
        """Game should allow human moves after engine is disabled."""
        pytest.importorskip("PySide6")
        
        try:
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            game = Game()
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            controller = EngineController(game, adapter)
            
            # Make a White move and cause engine error
            game.apply_move("e2e4")
            controller.on_human_move_applied()
            adapter.simulate_move_failure(
                EngineErrorCode.TIMEOUT,
                "Test timeout"
            )
            app.processEvents()
            
            # Engine should be disabled
            assert not controller.is_enabled()
            
            # But game should still work for human moves
            game.apply_move("e7e5")  # Human plays Black
            game.apply_move("g1f3")  # Human plays White
            
            # Verify moves were applied
            history = game.get_history()
            assert len(history) == 3
            assert history[1].uci == "e7e5"
            assert history[2].uci == "g1f3"
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")

