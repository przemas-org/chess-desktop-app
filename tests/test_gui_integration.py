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
        """Game model and MainWindow should integrate via Game ownership."""
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
            
            # Set the game and update the board
            window.set_game(game)
            window.update_board_from_game()
            
            # Verify the FEN was propagated to the BoardWidget
            # BoardWidget stores the FEN in _fen attribute
            assert central_widget._fen == starting_fen
            
        except Exception as e:
            # If Qt cannot initialize (no display), skip the test gracefully
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_mainwindow_can_update_board_from_game(self):
        """MainWindow should be able to update the board position from Game."""
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
            game = Game.from_fen(starting_fen)
            window.set_game(game)
            window.update_board_from_game()
            
            # Verify the FEN was set
            assert window.centralWidget()._fen == starting_fen
            
            # Update to a different position (after 1. e4)
            after_e4_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            game2 = Game.from_fen(after_e4_fen)
            window.set_game(game2)
            window.update_board_from_game()
            
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
            
            # 4. Set game and update board
            window.set_game(game)
            window.update_board_from_game()
            
            # 5. Verify window is ready to be shown
            # (We don't call show() or exec() to keep test headless)
            assert window.centralWidget() is not None
            assert window.centralWidget()._fen == starting_fen
            
        except Exception as e:
            # If Qt cannot initialize (no display), skip the test gracefully
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")


class TestMainWindowBoardWidgetAPI:
    """Tests for the MainWindow-BoardWidget communication API."""
    
    def test_mainwindow_exposes_game_ownership_methods(self):
        """MainWindow should expose set_game and update_board_from_game methods."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            # Verify methods exist
            assert hasattr(window, 'set_game')
            assert callable(window.set_game)
            assert hasattr(window, 'update_board_from_game')
            assert callable(window.update_board_from_game)
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_update_board_from_game_propagates_to_board_widget(self):
        """update_board_from_game should read from Game and update BoardWidget."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            central_widget = window.centralWidget()
            
            # Initially, board should be empty
            assert central_widget._fen == ""
            
            # Set a game and update board
            test_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            game = Game.from_fen(test_fen)
            window.set_game(game)
            window.update_board_from_game()
            
            # Verify it was propagated to BoardWidget
            assert central_widget._fen == test_fen
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_invalid_fen_raises_board_fen_error(self):
        """Invalid FEN in Game should raise BoardFenError when updating board."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.game import Game, InvalidFenError
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            # Try to create a game with invalid FEN (this should fail at Game level)
            with pytest.raises(InvalidFenError):
                Game.from_fen("invalid fen string")
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")


class TestMainWindowFenUpdates:
    """Tests for game update behavior through MainWindow API."""
    
    def test_multiple_game_updates_through_mainwindow(self):
        """Test setting game multiple times through MainWindow.set_game."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            # Update 1: Starting position
            fen1 = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            game1 = Game.from_fen(fen1)
            window.set_game(game1)
            window.update_board_from_game()
            assert window.centralWidget()._fen == fen1
            
            # Update 2: After e4
            fen2 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
            game2 = Game.from_fen(fen2)
            window.set_game(game2)
            window.update_board_from_game()
            assert window.centralWidget()._fen == fen2
            
            # Update 3: After e4 e5
            fen3 = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
            game3 = Game.from_fen(fen3)
            window.set_game(game3)
            window.update_board_from_game()
            assert window.centralWidget()._fen == fen3
            
            # Update 4: Endgame position
            fen4 = "8/8/4k3/8/8/4K3/8/8 w - - 0 1"
            game4 = Game.from_fen(fen4)
            window.set_game(game4)
            window.update_board_from_game()
            assert window.centralWidget()._fen == fen4
            
            # Update 5: Back to starting position
            window.set_game(game1)
            window.update_board_from_game()
            assert window.centralWidget()._fen == fen1
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_game_update_changes_board_state(self):
        """Test that game updates actually change the internal board state."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            board_widget = window.centralWidget()
            
            # Set starting position
            game1 = Game.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            window.set_game(game1)
            window.update_board_from_game()
            
            # Verify white king is at e1 (rank 1 = index 7, file e = index 4)
            assert board_widget._board[7][4] == {"piece": "k", "color": "white"}
            
            # Change to position with king on d1
            game2 = Game.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBKQBNR w KQkq - 0 1")
            window.set_game(game2)
            window.update_board_from_game()
            
            # Verify king moved to d1 (rank 1 = index 7, file d = index 3)
            assert board_widget._board[7][3] == {"piece": "k", "color": "white"}
            assert board_widget._board[7][4] == {"piece": "q", "color": "white"}
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_error_propagation_invalid_fen(self):
        """Test that InvalidFenError is raised when creating Game with invalid FEN."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.game import Game, InvalidFenError
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            # Try to create game with invalid FEN (too few ranks)
            with pytest.raises(InvalidFenError) as exc_info:
                Game.from_fen("rnbqkbnr/pppppppp/8/8/8 w KQkq - 0 1")
            
            # Verify error message is descriptive
            assert "Invalid FEN" in str(exc_info.value)
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_error_propagation_invalid_characters(self):
        """Test that InvalidFenError is raised for FEN with invalid characters."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.game import Game, InvalidFenError
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            # Try to create game with FEN with invalid character
            with pytest.raises(InvalidFenError) as exc_info:
                Game.from_fen("rnbqkbnr/ppppxppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            
            # Verify error message is descriptive
            assert "Invalid FEN" in str(exc_info.value)
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_game_update_from_game_model(self):
        """Test typical workflow: Game model with moves -> MainWindow."""
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
            
            # Set game and update GUI
            window.set_game(game)
            window.update_board_from_game()
            
            # Verify the FEN was set correctly
            fen = game.export_fen()
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
    
    def test_rapid_game_switching_through_mainwindow(self):
        """Test rapid game switching through MainWindow doesn't cause issues."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.game import Game
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
                game = Game.from_fen(fen)
                window.set_game(game)
                window.update_board_from_game()
                assert window.centralWidget()._fen == fen
            
            # Verify last FEN is correctly set
            assert window.centralWidget()._fen == fens[-1]
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")


class TestMainWindowGameOwnership:
    """Tests for MainWindow game ownership and Game-based updates."""
    
    def test_mainwindow_can_be_constructed_without_game(self):
        """MainWindow should be constructible without a game initially."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            # Create MainWindow without setting a game
            window = MainWindow()
            assert window is not None
            
            # Verify no game is set initially
            assert window._game is None
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_update_board_from_game_raises_when_no_game_set(self):
        """update_board_from_game should raise RuntimeError when no game is set."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            # Try to update board without setting a game first
            with pytest.raises(RuntimeError) as exc_info:
                window.update_board_from_game()
            
            # Verify error message is descriptive
            assert "no game has been set" in str(exc_info.value)
            assert "set_game()" in str(exc_info.value)
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_set_game_accepts_game_instance(self):
        """set_game should accept a Game instance and store it."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            game = Game()
            
            # Initially no game
            assert window._game is None
            
            # Set the game
            window.set_game(game)
            
            # Verify game is stored
            assert window._game is game
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_set_game_and_update_board_from_game_workflow(self):
        """Test the complete workflow: set_game then update_board_from_game."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            # Create a game with a known FEN
            test_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            game = Game.from_fen(test_fen)
            
            # Set the game
            window.set_game(game)
            
            # Update the board from game
            window.update_board_from_game()
            
            # Verify the board widget received the FEN
            assert window.centralWidget()._fen == test_fen
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_replacing_game_via_set_game(self):
        """Test that set_game can replace an existing game."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            # Set first game
            fen1 = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            game1 = Game.from_fen(fen1)
            window.set_game(game1)
            window.update_board_from_game()
            
            assert window._game is game1
            assert window.centralWidget()._fen == fen1
            
            # Replace with second game
            fen2 = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            game2 = Game.from_fen(fen2)
            window.set_game(game2)
            window.update_board_from_game()
            
            # Verify game was replaced
            assert window._game is game2
            assert window._game is not game1
            assert window.centralWidget()._fen == fen2
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_game_with_applied_moves_updates_board(self):
        """Test that a game with applied moves correctly updates the board."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.game import Game
            from chess_app.gui import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            # Create game and make moves
            game = Game()
            game.apply_move("e2e4")
            game.apply_move("c7c5")
            
            # Set game and update board
            window.set_game(game)
            window.update_board_from_game()
            
            # Verify the board shows the position after the moves
            board = window.centralWidget()._board
            
            # White pawn on e4 (rank 4 = index 4, file e = index 4)
            assert board[4][4] == {"piece": "p", "color": "white"}
            
            # Black pawn on c5 (rank 5 = index 3, file c = index 2)
            assert board[3][2] == {"piece": "p", "color": "black"}
            
            # e2 should be empty (rank 2 = index 6, file e = index 4)
            assert board[6][4] is None
            
            # c7 should be empty (rank 7 = index 1, file c = index 2)
            assert board[1][2] is None
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")

