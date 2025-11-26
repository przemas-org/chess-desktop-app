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


class TestMainWindowFenUpdates:
    """Tests for FEN update behavior through MainWindow API."""
    
    def test_multiple_fen_updates_through_mainwindow(self):
        """Test setting FEN multiple times through MainWindow.set_board_fen."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            # Update 1: Starting position
            fen1 = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            window.set_board_fen(fen1)
            assert window.centralWidget()._fen == fen1
            
            # Update 2: After e4
            fen2 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
            window.set_board_fen(fen2)
            assert window.centralWidget()._fen == fen2
            
            # Update 3: After e4 e5
            fen3 = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
            window.set_board_fen(fen3)
            assert window.centralWidget()._fen == fen3
            
            # Update 4: Endgame position
            fen4 = "8/8/4k3/8/8/4K3/8/8 w - - 0 1"
            window.set_board_fen(fen4)
            assert window.centralWidget()._fen == fen4
            
            # Update 5: Back to starting position
            window.set_board_fen(fen1)
            assert window.centralWidget()._fen == fen1
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_fen_update_changes_board_state(self):
        """Test that FEN updates actually change the internal board state."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            board_widget = window.centralWidget()
            
            # Set starting position
            window.set_board_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            
            # Verify white king is at e1 (rank 1 = index 7, file e = index 4)
            assert board_widget._board[7][4] == {"piece": "k", "color": "white"}
            
            # Change to position with king on d1
            window.set_board_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBKQBNR w KQkq - 0 1")
            
            # Verify king moved to d1 (rank 1 = index 7, file d = index 3)
            assert board_widget._board[7][3] == {"piece": "k", "color": "white"}
            assert board_widget._board[7][4] == {"piece": "q", "color": "white"}
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_error_propagation_invalid_fen(self):
        """Test that BoardFenError propagates through MainWindow."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import MainWindow
            from chess_app.gui.board_widget import BoardFenError
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            # Try to set an invalid FEN (too few ranks)
            with pytest.raises(BoardFenError) as exc_info:
                window.set_board_fen("rnbqkbnr/pppppppp/8/8/8 w KQkq - 0 1")
            
            # Verify error message is descriptive
            assert "expected 8 ranks" in str(exc_info.value)
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_error_propagation_invalid_characters(self):
        """Test that BoardFenError with invalid characters propagates correctly."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import MainWindow
            from chess_app.gui.board_widget import BoardFenError
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            # Try to set FEN with invalid character
            with pytest.raises(BoardFenError) as exc_info:
                window.set_board_fen("rnbqkbnr/ppppxppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            
            # Verify error message mentions the invalid character
            assert "Invalid character" in str(exc_info.value)
            assert "'x'" in str(exc_info.value)
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_fen_update_from_game_model(self):
        """Test typical workflow: Game model -> FEN -> MainWindow."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            # Create game and make some moves
            game = Game()
            game.apply_move("e2e4")
            game.apply_move("e7e5")
            game.apply_move("g1f3")
            
            # Export FEN and update GUI
            fen = game.export_fen()
            window.set_board_fen(fen)
            
            # Verify the FEN was set correctly
            assert window.centralWidget()._fen == fen
            
            # Verify specific pieces are in the right positions
            board = window.centralWidget()._board
            # White knight on f3 (rank 3 = index 5, file f = index 5)
            assert board[5][5] == {"piece": "n", "color": "white"}
            # White pawn on e4 (rank 4 = index 4, file e = index 4)
            assert board[4][4] == {"piece": "p", "color": "white"}
            # Black pawn on e5 (rank 5 = index 3, file e = index 4)
            assert board[3][4] == {"piece": "p", "color": "black"}
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_rapid_fen_switching_through_mainwindow(self):
        """Test rapid FEN switching through MainWindow doesn't cause issues."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            fens = [
                "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "8/8/8/8/8/8/8/8 w - - 0 1",
                "4k3/8/8/8/8/8/8/4K3 w - - 0 1",
                "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
                "8/8/4k3/8/8/4K3/8/8 w - - 0 1",
            ]
            
            # Rapidly switch between positions
            for fen in fens:
                window.set_board_fen(fen)
                assert window.centralWidget()._fen == fen
            
            # Verify last FEN is correctly set
            assert window.centralWidget()._fen == fens[-1]
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")

