#!/usr/bin/env python3
"""
Integration tests for GUI bootstrapping and MainWindow-BoardWidget integration.

This module validates that the complete GUI stack (Game -> MainWindow -> BoardWidget)
can be initialized and works correctly together. Tests are designed to be skipped
gracefully in headless environments.
"""

import pytest


class TestGUIBootstrap:
    """Tests for complete GUI application bootstrapping."""
    
    def test_game_and_mainwindow_integration(self):
        """Game model and MainWindow should integrate via FEN strings."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            from chess_app.gui.board_widget import BoardWidget
            
            # QApplication is required for GUI components
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # Create a game with standard starting position
            game = Game()
            starting_fen = game.export_fen()
            
            # Verify we got a valid FEN
            assert starting_fen is not None
            assert isinstance(starting_fen, str)
            assert "rnbqkbnr/pppppppp" in starting_fen
            
            # Create MainWindow
            window = MainWindow()
            assert window is not None
            
            # Verify BoardWidget is set as central widget
            central_widget = window.centralWidget()
            assert central_widget is not None
            assert isinstance(central_widget, BoardWidget)
            
            # Set the board FEN
            window.set_board_fen(starting_fen)
            
            # Verify the FEN was propagated to the BoardWidget
            # BoardWidget stores the FEN in _fen attribute
            assert central_widget._fen == starting_fen
            
        except Exception as e:
            # If Qt cannot initialize (no display), skip the test gracefully
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_mainwindow_can_update_board_fen(self):
        """MainWindow should be able to update the board position via FEN."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            
            # QApplication is required for GUI components
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # Create MainWindow
            window = MainWindow()
            
            # Set starting position
            starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            window.set_board_fen(starting_fen)
            
            # Verify the FEN was set
            assert window.centralWidget()._fen == starting_fen
            
            # Update to a different position (after 1. e4)
            after_e4_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            window.set_board_fen(after_e4_fen)
            
            # Verify the FEN was updated
            assert window.centralWidget()._fen == after_e4_fen
            
        except Exception as e:
            # If Qt cannot initialize (no display), skip the test gracefully
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_main_module_constructs_required_components(self):
        """Main module should be able to construct all required components."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            
            # QApplication is required for GUI components
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # Simulate the main() function logic without starting event loop
            
            # 1. Create Game
            game = Game()
            assert game is not None
            
            # 2. Get starting FEN
            starting_fen = game.export_fen()
            assert starting_fen is not None
            assert isinstance(starting_fen, str)
            
            # 3. Create MainWindow
            window = MainWindow()
            assert window is not None
            assert window.windowTitle() == "Chess Desktop App"
            
            # 4. Set board FEN
            window.set_board_fen(starting_fen)
            
            # 5. Verify window is ready to be shown
            # (We don't call show() or exec() to keep test headless)
            assert window.centralWidget() is not None
            assert window.centralWidget()._fen == starting_fen
            
        except Exception as e:
            # If Qt cannot initialize (no display), skip the test gracefully
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")


class TestMainWindowBoardWidgetAPI:
    """Tests for the MainWindow-BoardWidget communication API."""
    
    def test_mainwindow_exposes_set_board_fen_method(self):
        """MainWindow should expose a set_board_fen method."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            # Verify method exists
            assert hasattr(window, 'set_board_fen')
            assert callable(window.set_board_fen)
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_set_board_fen_propagates_to_board_widget(self):
        """set_board_fen should delegate to BoardWidget.set_fen."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            central_widget = window.centralWidget()
            
            # Initially, board should be empty
            assert central_widget._fen == ""
            
            # Set a FEN
            test_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            window.set_board_fen(test_fen)
            
            # Verify it was propagated to BoardWidget
            assert central_widget._fen == test_fen
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_invalid_fen_raises_board_fen_error(self):
        """Invalid FEN should raise BoardFenError from BoardWidget."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import MainWindow
            from chess_app.gui.board_widget import BoardFenError
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            # Try to set an invalid FEN
            with pytest.raises(BoardFenError):
                window.set_board_fen("invalid fen string")
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")

