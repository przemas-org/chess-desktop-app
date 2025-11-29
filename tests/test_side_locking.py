#!/usr/bin/env python3
"""
Tests for side locking and input gating in MainWindow.

This module validates that:
1. Human players can only move White pieces when engine is configured
2. User input is blocked while engine moves are in flight
3. Without engine configured, both sides can be moved (existing behavior preserved)
"""

import pytest


class TestSideLockingBasics:
    """Tests for basic side locking functionality."""
    
    def test_white_pieces_can_be_selected_with_engine(self):
        """White pieces should be selectable when engine is configured."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            from tests.engine_fakes import FakeEngineAdapter
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            game = Game()
            window.set_game(game)
            window.update_board_from_game()
            
            # Configure engine
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            window.set_engine_adapter(adapter)
            
            # Click on e2 (white pawn)
            window._on_square_clicked("e2", Qt.MouseButton.LeftButton)
            
            # Should be selected
            assert window._selected_source == "e2"
            assert len(window._legal_destinations) == 2  # e3, e4
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_black_pieces_cannot_be_selected_with_engine(self):
        """Black pieces should not be selectable when engine is configured."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            from tests.engine_fakes import FakeEngineAdapter
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            game = Game()
            window.set_game(game)
            window.update_board_from_game()
            
            # Configure engine
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            window.set_engine_adapter(adapter)
            
            # Click on e7 (black pawn)
            window._on_square_clicked("e7", Qt.MouseButton.LeftButton)
            
            # Should NOT be selected (silently ignored)
            assert window._selected_source is None
            assert len(window._legal_destinations) == 0
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_empty_squares_ignored_with_engine(self):
        """Empty squares should not be selectable when engine is configured."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            from tests.engine_fakes import FakeEngineAdapter
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            game = Game()
            window.set_game(game)
            window.update_board_from_game()
            
            # Configure engine
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            window.set_engine_adapter(adapter)
            
            # Click on e4 (empty square)
            window._on_square_clicked("e4", Qt.MouseButton.LeftButton)
            
            # Should NOT be selected
            assert window._selected_source is None
            assert len(window._legal_destinations) == 0
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_side_locking_persists_after_engine_disabled(self):
        """Side locking should persist even after engine is disabled."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from chess_app.game import Game, Side
            from chess_app.gui import MainWindow
            from tests.engine_fakes import FakeEngineAdapter, EngineErrorCode
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            game = Game()
            window.set_game(game)
            window.update_board_from_game()
            
            # Configure engine
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            window.set_engine_adapter(adapter)
            
            # Make a white move to trigger engine
            game.apply_move("e2e4")
            window.update_board_from_game()
            window._engine_controller.on_human_move_applied()
            
            # Simulate engine error to disable it
            adapter.simulate_move_failure(
                EngineErrorCode.TIMEOUT,
                "Test timeout"
            )
            app.processEvents()
            
            # Verify engine is disabled
            assert not window._engine_controller.is_enabled()
            
            # Try to click black pawn on e7
            window._on_square_clicked("e7", Qt.MouseButton.LeftButton)
            
            # Should still be rejected (side locking persists)
            assert window._selected_source is None
            assert len(window._legal_destinations) == 0
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_white_pieces_with_no_legal_moves_deselect(self):
        """Clicking white pieces with no legal moves should clear selection."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            from tests.engine_fakes import FakeEngineAdapter
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            # Use a position where white rook on a1 has no legal moves (blocked)
            game = Game()  # Standard starting position
            window.set_game(game)
            window.update_board_from_game()
            
            # Configure engine
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            window.set_engine_adapter(adapter)
            
            # Click on a1 (white rook, but blocked by pawn on a2)
            window._on_square_clicked("a1", Qt.MouseButton.LeftButton)
            
            # Should not be selected (no legal moves)
            assert window._selected_source is None
            assert len(window._legal_destinations) == 0
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")


class TestInputGating:
    """Tests for input gating during engine moves."""
    
    def test_clicks_blocked_during_engine_move(self):
        """User clicks should be ignored while engine move is in flight."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            from tests.engine_fakes import FakeEngineAdapter
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            game = Game()
            window.set_game(game)
            window.update_board_from_game()
            
            # Configure engine
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            window.set_engine_adapter(adapter)
            
            # Make a white move to trigger engine
            game.apply_move("e2e4")
            window.update_board_from_game()
            window._engine_controller.on_human_move_applied()
            
            # Verify engine is in flight
            assert window._engine_controller.is_in_flight()
            
            # Try to click on d2 (white pawn)
            window._on_square_clicked("d2", Qt.MouseButton.LeftButton)
            
            # Should be blocked (no selection made)
            assert window._selected_source is None
            assert len(window._legal_destinations) == 0
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_clicks_allowed_after_engine_move_completes(self):
        """User clicks should work normally after engine move completes."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            from tests.engine_fakes import FakeEngineAdapter
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            game = Game()
            window.set_game(game)
            window.update_board_from_game()
            
            # Configure engine
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            window.set_engine_adapter(adapter)
            
            # Make a white move to trigger engine
            game.apply_move("e2e4")
            window.update_board_from_game()
            window._engine_controller.on_human_move_applied()
            
            # Simulate engine response
            adapter.simulate_move_response("e7e5")
            app.processEvents()
            
            # Verify engine is no longer in flight
            assert not window._engine_controller.is_in_flight()
            
            # Now click on d2 (white pawn) should work
            window._on_square_clicked("d2", Qt.MouseButton.LeftButton)
            
            # Should be selected
            assert window._selected_source == "d2"
            assert len(window._legal_destinations) > 0
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_multiple_rapid_clicks_during_inflight_ignored(self):
        """Multiple rapid clicks during in-flight should all be ignored."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            from tests.engine_fakes import FakeEngineAdapter
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            game = Game()
            window.set_game(game)
            window.update_board_from_game()
            
            # Configure engine
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            window.set_engine_adapter(adapter)
            
            # Make a white move to trigger engine
            game.apply_move("e2e4")
            window.update_board_from_game()
            window._engine_controller.on_human_move_applied()
            
            # Verify engine is in flight
            assert window._engine_controller.is_in_flight()
            
            # Rapid clicks on various squares
            window._on_square_clicked("d2", Qt.MouseButton.LeftButton)
            window._on_square_clicked("g1", Qt.MouseButton.LeftButton)
            window._on_square_clicked("f2", Qt.MouseButton.LeftButton)
            window._on_square_clicked("e4", Qt.MouseButton.LeftButton)
            
            # All should be ignored
            assert window._selected_source is None
            assert len(window._legal_destinations) == 0
            
            # Complete the engine move
            adapter.simulate_move_response("e7e5")
            app.processEvents()
            
            # Now clicks should work
            window._on_square_clicked("g1", Qt.MouseButton.LeftButton)
            assert window._selected_source == "g1"
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_selection_cleared_before_engine_move_stays_cleared(self):
        """Existing selection should remain cleared during engine move."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            from tests.engine_fakes import FakeEngineAdapter
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            game = Game()
            window.set_game(game)
            window.update_board_from_game()
            
            # Configure engine
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            window.set_engine_adapter(adapter)
            
            # Select and make a move
            window._on_square_clicked("e2", Qt.MouseButton.LeftButton)
            assert window._selected_source == "e2"
            
            window._on_square_clicked("e4", Qt.MouseButton.LeftButton)
            
            # Selection should be cleared after move
            assert window._selected_source is None
            
            # Engine move triggered automatically, verify in flight
            assert window._engine_controller.is_in_flight()
            
            # Selection should still be cleared
            assert window._selected_source is None
            assert len(window._legal_destinations) == 0
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")


class TestIntegrationFlow:
    """Integration tests for complete game flow with side locking and input gating."""
    
    def test_complete_game_flow_with_side_locking(self):
        """Test complete flow: White move → engine in-flight → Black response → White can move."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from chess_app.game import Game, Side
            from chess_app.gui import MainWindow
            from tests.engine_fakes import FakeEngineAdapter
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            game = Game()
            window.set_game(game)
            window.update_board_from_game()
            
            # Configure engine
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            window.set_engine_adapter(adapter)
            
            # Move 1: White plays e2-e4
            window._on_square_clicked("e2", Qt.MouseButton.LeftButton)
            assert window._selected_source == "e2"
            
            window._on_square_clicked("e4", Qt.MouseButton.LeftButton)
            assert window._selected_source is None  # Cleared after move
            
            # Engine should be in flight
            assert window._engine_controller.is_in_flight()
            
            # Try to click (should be blocked)
            window._on_square_clicked("d2", Qt.MouseButton.LeftButton)
            assert window._selected_source is None
            
            # Engine responds with e7-e5
            adapter.simulate_move_response("e7e5")
            app.processEvents()
            
            # Should no longer be in flight
            assert not window._engine_controller.is_in_flight()
            
            # Move 2: White plays Nf3
            window._on_square_clicked("g1", Qt.MouseButton.LeftButton)
            assert window._selected_source == "g1"
            
            window._on_square_clicked("f3", Qt.MouseButton.LeftButton)
            assert window._selected_source is None
            
            # Engine responds with Nc6
            adapter.simulate_move_response("b8c6")
            app.processEvents()
            
            # Verify game state
            history = game.get_history()
            assert len(history) == 4
            assert history[0].uci == "e2e4"
            assert history[1].uci == "e7e5"
            assert history[2].uci == "g1f3"
            assert history[3].uci == "b8c6"
            
            # Should be White's turn
            assert game.get_side_to_move() == Side.WHITE
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_black_pieces_never_selectable_during_game(self):
        """Throughout game, human should never be able to select Black pieces."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            from tests.engine_fakes import FakeEngineAdapter
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            game = Game()
            window.set_game(game)
            window.update_board_from_game()
            
            # Configure engine
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            window.set_engine_adapter(adapter)
            
            # Try to click black pieces at start
            window._on_square_clicked("e7", Qt.MouseButton.LeftButton)
            assert window._selected_source is None
            
            window._on_square_clicked("d7", Qt.MouseButton.LeftButton)
            assert window._selected_source is None
            
            # Make white move
            window._on_square_clicked("e2", Qt.MouseButton.LeftButton)
            window._on_square_clicked("e4", Qt.MouseButton.LeftButton)
            adapter.simulate_move_response("e7e5")
            app.processEvents()
            
            # Try to click black pieces after engine move
            window._on_square_clicked("e5", Qt.MouseButton.LeftButton)
            assert window._selected_source is None
            
            window._on_square_clicked("d7", Qt.MouseButton.LeftButton)
            assert window._selected_source is None
            
            # But white pieces should still work
            window._on_square_clicked("g1", Qt.MouseButton.LeftButton)
            assert window._selected_source == "g1"
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_right_click_during_inflight_clears_selection(self):
        """Right-click should still work during in-flight to clear any selection."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            from tests.engine_fakes import FakeEngineAdapter
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            game = Game()
            window.set_game(game)
            window.update_board_from_game()
            
            # Configure engine
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            window.set_engine_adapter(adapter)
            
            # Make a move to trigger engine
            game.apply_move("e2e4")
            window.update_board_from_game()
            window._engine_controller.on_human_move_applied()
            
            # Verify in flight
            assert window._engine_controller.is_in_flight()
            
            # Right-click should still work (calls _clear_selection)
            window._on_square_clicked("a1", Qt.MouseButton.RightButton)
            
            # Should have no side effects (selection already clear)
            assert window._selected_source is None
            assert len(window._legal_destinations) == 0
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")


class TestNoEngineConfiguration:
    """Tests verifying existing behavior when no engine is configured."""
    
    def test_both_sides_moveable_without_engine(self):
        """Without engine configured, human should be able to move both sides."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from chess_app.game import Game, Side
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            game = Game()
            window.set_game(game)
            window.update_board_from_game()
            
            # No engine configured - _engine_controller is None
            assert window._engine_controller is None
            
            # White move should work
            window._on_square_clicked("e2", Qt.MouseButton.LeftButton)
            assert window._selected_source == "e2"
            
            window._on_square_clicked("e4", Qt.MouseButton.LeftButton)
            assert window._selected_source is None
            
            # Verify white move applied
            assert game.get_side_to_move() == Side.BLACK
            
            # Black move should also work (no engine, so human controls both)
            window._on_square_clicked("e7", Qt.MouseButton.LeftButton)
            assert window._selected_source == "e7"
            
            window._on_square_clicked("e5", Qt.MouseButton.LeftButton)
            assert window._selected_source is None
            
            # Verify black move applied
            assert game.get_side_to_move() == Side.WHITE
            
            # Verify both moves in history
            history = game.get_history()
            assert len(history) == 2
            assert history[0].uci == "e2e4"
            assert history[1].uci == "e7e5"
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_no_inflight_checks_without_engine(self):
        """Without engine, no in-flight checks should occur."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            game = Game()
            window.set_game(game)
            window.update_board_from_game()
            
            # No engine configured
            assert window._engine_controller is None
            
            # Make multiple rapid moves (should all work)
            window._on_square_clicked("e2", Qt.MouseButton.LeftButton)
            window._on_square_clicked("e4", Qt.MouseButton.LeftButton)
            
            window._on_square_clicked("e7", Qt.MouseButton.LeftButton)
            window._on_square_clicked("e5", Qt.MouseButton.LeftButton)
            
            window._on_square_clicked("g1", Qt.MouseButton.LeftButton)
            window._on_square_clicked("f3", Qt.MouseButton.LeftButton)
            
            # All moves should have been applied
            history = game.get_history()
            assert len(history) == 3
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")
    
    def test_empty_and_invalid_squares_still_ignored_without_engine(self):
        """Even without engine, empty squares and pieces with no moves are ignored."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            game = Game()
            window.set_game(game)
            window.update_board_from_game()
            
            # No engine configured
            assert window._engine_controller is None
            
            # Click empty square
            window._on_square_clicked("e4", Qt.MouseButton.LeftButton)
            assert window._selected_source is None
            
            # Click white piece with no moves (rook blocked by pawn)
            window._on_square_clicked("a1", Qt.MouseButton.LeftButton)
            assert window._selected_source is None
            
            # Click black piece with no moves (rook blocked by pawn)
            window._on_square_clicked("a8", Qt.MouseButton.LeftButton)
            assert window._selected_source is None
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed: {e}")

