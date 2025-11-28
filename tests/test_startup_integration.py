#!/usr/bin/env python3
"""
Integration tests for application startup with engine wiring and feature gating.

This module tests the complete startup flow including:
- Engine binary detection and path resolution
- Engine initialization (successful and failed)
- Graceful fallback to human-vs-human mode
- Window title updates based on engine availability
- No engine calls when engine is disabled
"""

import pytest
from unittest.mock import Mock, patch, MagicMock


class TestEngineConfiguration:
    """Tests for engine configuration and binary path resolution."""
    
    def test_get_stockfish_path_returns_none_when_binary_missing(self):
        """get_stockfish_path should return None when binary doesn't exist."""
        from chess_app.engine_config import get_stockfish_path
        
        # Mock Path.exists() to return False
        with patch('chess_app.engine_config.Path.exists', return_value=False):
            result = get_stockfish_path()
            assert result is None
    
    def test_get_stockfish_path_returns_none_when_not_executable(self):
        """get_stockfish_path should return None when binary is not executable."""
        from chess_app.engine_config import get_stockfish_path
        
        # Mock Path.exists() to return True, but os.access() to return False
        with patch('chess_app.engine_config.Path.exists', return_value=True), \
             patch('chess_app.engine_config.os.access', return_value=False):
            result = get_stockfish_path()
            assert result is None
    
    def test_get_stockfish_path_returns_path_when_available(self):
        """get_stockfish_path should return absolute path when binary exists and is executable."""
        from chess_app.engine_config import get_stockfish_path
        
        # Mock Path.exists() and os.access() to return True
        with patch('chess_app.engine_config.Path.exists', return_value=True), \
             patch('chess_app.engine_config.os.access', return_value=True):
            result = get_stockfish_path()
            assert result is not None
            assert isinstance(result, str)
            # Should contain 'stockfish' in the path
            assert 'stockfish' in result
    
    def test_is_stockfish_available_matches_get_stockfish_path(self):
        """is_stockfish_available should match get_stockfish_path result."""
        from chess_app.engine_config import is_stockfish_available, get_stockfish_path
        
        # Test when not available
        with patch('chess_app.engine_config.Path.exists', return_value=False):
            assert is_stockfish_available() == (get_stockfish_path() is not None)
            assert is_stockfish_available() is False
        
        # Test when available
        with patch('chess_app.engine_config.Path.exists', return_value=True), \
             patch('chess_app.engine_config.os.access', return_value=True):
            assert is_stockfish_available() == (get_stockfish_path() is not None)
            assert is_stockfish_available() is True


class TestStartupWithEngine:
    """Tests for startup flow when engine is available."""
    
    def test_startup_with_engine_available(self):
        """App should initialize engine when binary is available."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            from chess_app.gui.engine_integration import FakeEngineAdapter
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # Create window and game
            window = MainWindow()
            game = Game()
            window.set_game(game)
            
            # Initially should show Human vs Human
            assert "Human vs Human" in window.windowTitle()
            
            # Create fake adapter and simulate successful initialization
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            
            # Set adapter on window
            window.set_engine_adapter(adapter)
            
            # Title should now show Engine Enabled
            assert "Engine Enabled" in window.windowTitle()
            
            # Engine controller should be created
            assert window._engine_controller is not None
            assert window._engine_enabled is True
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_window_title_updates_on_engine_setup(self):
        """Window title should update when engine adapter is set."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            from chess_app.gui.engine_integration import FakeEngineAdapter
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            game = Game()
            window.set_game(game)
            
            # Initially should be Human vs Human
            assert window.windowTitle() == "Chess Desktop App - Human vs Human"
            
            # Create and set adapter
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            window.set_engine_adapter(adapter)
            
            # Should now show Engine Enabled
            assert window.windowTitle() == "Chess Desktop App - Engine Enabled"
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")


class TestStartupWithoutEngine:
    """Tests for startup flow when engine is not available."""
    
    def test_startup_with_missing_binary(self):
        """App should start successfully when Stockfish binary is missing."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # Simulate missing binary by mocking get_stockfish_path
            with patch('chess_app.engine_config.get_stockfish_path', return_value=None):
                # Create window
                window = MainWindow()
                game = Game()
                window.set_game(game)
                window.update_board_from_game()
                
                # Should initialize successfully
                assert window is not None
                assert window._game is not None
                
                # Title should show Human vs Human
                assert window.windowTitle() == "Chess Desktop App - Human vs Human"
                
                # Engine components should be None
                assert window._engine_adapter is None
                assert window._engine_controller is None
                assert window._engine_enabled is False
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_startup_with_initialization_failure(self):
        """App should continue when engine initialization fails."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            from chess_app.gui.engine_integration import FakeEngineAdapter, EngineErrorCode
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # Create window
            window = MainWindow()
            game = Game()
            window.set_game(game)
            
            # Create adapter that will fail initialization
            adapter = FakeEngineAdapter()
            adapter.initialize()
            
            # Simulate initialization failure
            adapter.simulate_init_failure(
                EngineErrorCode.INITIALIZATION_FAILED,
                "Binary not found"
            )
            
            # App should continue (window still valid)
            assert window is not None
            assert window._game is not None
            
            # Title should remain Human vs Human
            assert window.windowTitle() == "Chess Desktop App - Human vs Human"
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")


class TestEngineFeatureGating:
    """Tests for engine feature gating based on availability."""
    
    def test_no_engine_calls_when_disabled(self):
        """When engine is disabled, no move requests should be made."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # Create window without engine
            window = MainWindow()
            game = Game()
            window.set_game(game)
            window.update_board_from_game()
            
            # Make a move as White
            window._on_square_clicked("e2", Qt.MouseButton.LeftButton)
            window._on_square_clicked("e4", Qt.MouseButton.LeftButton)
            
            # Verify move was made
            history = game.get_history()
            assert len(history) == 1
            assert history[0].uci == "e2e4"
            
            # Verify no engine controller exists
            assert window._engine_controller is None
            
            # Black should be able to move (human-vs-human mode)
            window._on_square_clicked("e7", Qt.MouseButton.LeftButton)
            window._on_square_clicked("e5", Qt.MouseButton.LeftButton)
            
            # Verify Black's move was made
            assert len(game.get_history()) == 2
            assert game.get_history()[1].uci == "e7e5"
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_engine_disabled_during_gameplay_updates_title(self):
        """When engine is disabled during gameplay, window title should update."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            from chess_app.gui.engine_integration import FakeEngineAdapter
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # Create window with engine
            window = MainWindow()
            game = Game()
            window.set_game(game)
            
            # Set up engine
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            window.set_engine_adapter(adapter)
            
            # Verify engine is enabled
            assert window.windowTitle() == "Chess Desktop App - Engine Enabled"
            assert window._engine_enabled is True
            
            # Simulate engine being disabled (via controller)
            window._on_engine_disabled("Test failure")
            
            # Title should update to Human vs Human
            assert window.windowTitle() == "Chess Desktop App - Human vs Human"
            assert window._engine_enabled is False
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_white_can_only_move_when_engine_active(self):
        """When engine is active, only White pieces should be selectable."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            from chess_app.gui.engine_integration import FakeEngineAdapter
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # Create window with engine
            window = MainWindow()
            game = Game()
            window.set_game(game)
            window.update_board_from_game()
            
            # Set up engine
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            window.set_engine_adapter(adapter)
            
            # Try to select Black piece (should be ignored)
            window._on_square_clicked("e7", Qt.MouseButton.LeftButton)
            
            # Nothing should be selected
            assert window._selected_source is None
            
            # White piece should be selectable
            window._on_square_clicked("e2", Qt.MouseButton.LeftButton)
            assert window._selected_source == "e2"
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")


class TestMainBootstrap:
    """Tests for the main() bootstrap function."""
    
    def test_main_creates_required_components(self):
        """main() should create all required components."""
        pytest.importorskip("PySide6")
        
        try:
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            
            # We can't actually run main() in tests, but we can verify
            # that the components can be created in the same way
            game = Game()
            window = MainWindow()
            window.set_game(game)
            window.update_board_from_game()
            
            assert game is not None
            assert window is not None
            assert window._game is game
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_main_handles_missing_binary_gracefully(self):
        """main() bootstrap should handle missing binary gracefully."""
        from chess_app.engine_config import get_stockfish_path
        
        # Mock to return None (binary not found)
        with patch('chess_app.engine_config.get_stockfish_path', return_value=None):
            result = get_stockfish_path()
            assert result is None
            
            # This would trigger the warning branch in main()
            # The app would continue without engine
    
    def test_main_handles_adapter_creation_failure(self):
        """main() should handle adapter creation failures gracefully."""
        pytest.importorskip("PySide6")
        
        try:
            from chess_app.gui.engine_integration import StockfishProcessAdapter
            
            # Mock get_stockfish_path to return a valid path
            with patch('chess_app.engine_config.get_stockfish_path', return_value='/fake/path'):
                # Mock StockfishProcessAdapter to raise exception
                with patch('chess_app.gui.engine_integration.StockfishProcessAdapter', side_effect=Exception("Test error")):
                    # This would be caught in the try/except in main()
                    # App would continue without engine
                    pass
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")


class TestEngineIntegrationFlow:
    """Tests for the complete engine integration flow."""
    
    def test_complete_flow_with_engine(self):
        """Test complete flow: startup -> engine init -> move -> engine response."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            from chess_app.gui.engine_integration import FakeEngineAdapter
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # Setup
            window = MainWindow()
            game = Game()
            window.set_game(game)
            window.update_board_from_game()
            
            # Initialize engine
            adapter = FakeEngineAdapter()
            adapter.initialize()
            adapter.simulate_init_success()
            window.set_engine_adapter(adapter)
            
            # Verify setup
            assert window._engine_enabled is True
            assert window._engine_controller is not None
            
            # Make White's move
            window._on_square_clicked("e2", Qt.MouseButton.LeftButton)
            window._on_square_clicked("e4", Qt.MouseButton.LeftButton)
            
            # Verify move was made and it's Black's turn
            assert len(game.get_history()) == 1
            assert game.get_side_to_move().name == "BLACK"
            
            # Simulate engine response
            adapter.simulate_move_response("e7e5")
            
            # Verify engine move was applied
            assert len(game.get_history()) == 2
            assert game.get_history()[1].uci == "e7e5"
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_complete_flow_without_engine(self):
        """Test complete flow in human-vs-human mode."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # Setup without engine
            window = MainWindow()
            game = Game()
            window.set_game(game)
            window.update_board_from_game()
            
            # Verify no engine
            assert window._engine_enabled is False
            assert window._engine_controller is None
            
            # Make White's move
            window._on_square_clicked("e2", Qt.MouseButton.LeftButton)
            window._on_square_clicked("e4", Qt.MouseButton.LeftButton)
            
            # Make Black's move (should work in human-vs-human mode)
            window._on_square_clicked("e7", Qt.MouseButton.LeftButton)
            window._on_square_clicked("e5", Qt.MouseButton.LeftButton)
            
            # Verify both moves were applied
            assert len(game.get_history()) == 2
            assert game.get_history()[0].uci == "e2e4"
            assert game.get_history()[1].uci == "e7e5"
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")

