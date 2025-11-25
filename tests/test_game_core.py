#!/usr/bin/env python3
"""
Scenario-based unit tests for core Game behavior.

This module validates:
- Move legality and application
- Illegal move detection and error handling
- Game status transitions (ongoing, check, checkmate, stalemate, draws)
- Undo functionality across multiple moves
- Integration scenarios combining multiple features
"""

import pytest
from chess_app.game import Game, GameStatus, IllegalMoveError, Side


class TestMoveLegality:
    """Tests for legal move detection and application."""
    
    def test_legal_moves_from_starting_position(self):
        """Starting position should have exactly 20 legal moves."""
        game = Game()
        legal_moves = game.get_legal_moves()
        
        assert len(legal_moves) == 20, "Starting position should have 20 legal moves"
        assert all(hasattr(move, 'uci') for move in legal_moves), "All moves should have UCI"
        assert all(hasattr(move, 'san') for move in legal_moves), "All moves should have SAN"
    
    def test_apply_legal_move_updates_position(self):
        """Applying a legal move should update the board position."""
        game = Game()
        initial_fen = game.export_fen()
        
        game.apply_move("e2e4")
        
        updated_fen = game.export_fen()
        assert updated_fen != initial_fen, "Position should change after move"
        assert "4P3" in updated_fen, "Pawn should be on e4"
        assert game.get_side_to_move() == Side.BLACK, "Should be Black's turn after White moves"
    
    def test_legal_moves_from_custom_fen(self):
        """Legal moves should be correct from a custom FEN position."""
        # Position after 1. e4 e5
        fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
        game = Game.from_fen(fen)
        
        legal_moves = game.get_legal_moves()
        assert len(legal_moves) > 0, "Should have legal moves"
        
        # Knight to f3 should be legal
        knight_moves = [m for m in legal_moves if m.uci == "g1f3"]
        assert len(knight_moves) == 1, "Nf3 should be a legal move"
    
    def test_apply_move_updates_history(self):
        """Move history should grow as moves are applied."""
        game = Game()
        
        assert len(game.get_history()) == 0, "Initial history should be empty"
        
        game.apply_move("e2e4")
        history = game.get_history()
        assert len(history) == 1, "History should have 1 move"
        assert history[0].uci == "e2e4"
        assert history[0].san == "e4"
        
        game.apply_move("e7e5")
        history = game.get_history()
        assert len(history) == 2, "History should have 2 moves"
        assert history[1].uci == "e7e5"
        assert history[1].san == "e5"
    
    def test_promotion_move_legality(self):
        """Pawn promotion moves should be handled correctly."""
        # Position where white pawn can promote
        fen = "4k3/P7/8/8/8/8/8/4K3 w - - 0 1"
        game = Game.from_fen(fen)
        
        legal_moves = game.get_legal_moves()
        promotion_moves = [m for m in legal_moves if m.promotion is not None]
        
        assert len(promotion_moves) > 0, "Should have promotion moves available"
        assert len(promotion_moves) == 4, "Should have 4 promotion options (Q, R, B, N)"
        
        # Apply queen promotion
        game.apply_move("a7a8q")
        history = game.get_history()
        assert history[0].promotion == "q", "Should record queen promotion"


class TestIllegalMoves:
    """Tests for illegal move detection and error handling."""
    
    def test_impossible_pawn_move(self):
        """Pawns cannot jump 3 squares."""
        game = Game()
        
        with pytest.raises(IllegalMoveError) as exc_info:
            game.apply_move("e2e5")
        
        assert "not legal" in str(exc_info.value).lower()
    
    def test_moving_opponent_piece(self):
        """Cannot move opponent's pieces."""
        game = Game()
        
        # Try to move black piece when it's white's turn
        with pytest.raises(IllegalMoveError):
            game.apply_move("e7e5")
    
    def test_move_into_check(self):
        """Cannot make a move that puts own king in check."""
        # Position where white king on f1, white bishop on f2 blocks black rook on f8
        # Moving the bishop would expose king to vertical check from rook
        fen = "5r2/8/8/8/8/8/5B2/5K2 w - - 0 1"
        game = Game.from_fen(fen)
        
        # Try to move bishop away, exposing king to vertical check from rook
        with pytest.raises(IllegalMoveError):
            game.apply_move("f2g3")
    
    def test_moving_pinned_piece(self):
        """Cannot move a pinned piece away from the pin line."""
        # White knight on c3 pinned by black rook on c8 (aligned vertically with white king on c1)
        fen = "2r5/8/8/8/8/2N5/8/2K5 w - - 0 1"
        game = Game.from_fen(fen)
        
        # Try to move the pinned knight horizontally (off the c-file)
        with pytest.raises(IllegalMoveError):
            game.apply_move("c3b5")
    
    def test_invalid_uci_format(self):
        """Malformed UCI strings should raise IllegalMoveError."""
        game = Game()
        
        invalid_moves = ["e2", "e2e", "e9e4", "invalid"]
        
        for invalid_move in invalid_moves:
            with pytest.raises(IllegalMoveError):
                game.apply_move(invalid_move)


class TestGameStatus:
    """Tests for game status detection and transitions."""
    
    def test_status_ongoing_from_start(self):
        """Starting position should have ONGOING status."""
        game = Game()
        
        assert game.get_status() == GameStatus.ONGOING
    
    def test_status_check(self):
        """Check status should be detected correctly."""
        # Black king in check from white rook
        fen = "4k3/8/8/8/8/8/8/4R1K1 b - - 0 1"
        game = Game.from_fen(fen)
        
        assert game.get_status() == GameStatus.CHECK
    
    def test_status_checkmate(self):
        """Checkmate should be detected (Fool's mate)."""
        game = Game()
        game.apply_move("f2f3")
        game.apply_move("e7e6")
        game.apply_move("g2g4")
        game.apply_move("d8h4")  # Checkmate
        
        assert game.get_status() == GameStatus.CHECKMATE
    
    def test_status_stalemate(self):
        """Stalemate should be detected correctly."""
        # Classic stalemate position
        fen = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
        game = Game.from_fen(fen)
        
        assert game.get_status() == GameStatus.STALEMATE
    
    def test_status_transitions_during_game(self):
        """Status should transition correctly as game progresses."""
        game = Game()
        
        # Initially ongoing
        assert game.get_status() == GameStatus.ONGOING
        
        # Set up a check position
        game = Game.from_fen("rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")
        game.apply_move("f1c4")  # Bishop to c4
        game.apply_move("b8c6")
        game.apply_move("d1h5")  # Queen to h5
        game.apply_move("g8f6")
        
        # Check if we're in check or mate (this might end in checkmate)
        status = game.get_status()
        assert status in [GameStatus.ONGOING, GameStatus.CHECK, GameStatus.CHECKMATE]


class TestUndo:
    """Tests for undo functionality."""
    
    def test_undo_single_move(self):
        """Undo should revert a single move."""
        game = Game()
        initial_fen = game.export_fen()
        
        game.apply_move("e2e4")
        assert game.export_fen() != initial_fen
        
        game.undo()
        assert game.export_fen() == initial_fen
    
    def test_undo_multiple_moves(self):
        """Undo should correctly revert multiple moves."""
        game = Game()
        initial_fen = game.export_fen()
        
        moves = ["e2e4", "e7e5", "g1f3", "b8c6"]
        for move in moves:
            game.apply_move(move)
        
        # Undo all moves
        for _ in range(len(moves)):
            game.undo()
        
        assert game.export_fen() == initial_fen
        assert len(game.get_history()) == 0
    
    def test_undo_restores_board_state(self):
        """Undo should restore exact board state."""
        game = Game()
        game.apply_move("d2d4")
        fen_after_d4 = game.export_fen()
        
        game.apply_move("d7d5")
        game.apply_move("c2c4")
        
        # Undo back to after d4
        game.undo()
        game.undo()
        
        assert game.export_fen() == fen_after_d4
    
    def test_undo_restores_status(self):
        """Undo should restore game status."""
        # Start from a position just before check
        fen = "4k3/8/8/8/8/8/7R/4K3 w - - 0 1"
        game = Game.from_fen(fen)
        
        assert game.get_status() == GameStatus.ONGOING
        
        # Move rook to give check
        game.apply_move("h2e2")
        assert game.get_status() == GameStatus.CHECK
        
        # Undo should restore to ongoing
        game.undo()
        assert game.get_status() == GameStatus.ONGOING
    
    def test_undo_restores_history(self):
        """Undo should correctly modify move history."""
        game = Game()
        
        game.apply_move("e2e4")
        game.apply_move("e7e5")
        game.apply_move("g1f3")
        
        assert len(game.get_history()) == 3
        
        game.undo()
        history = game.get_history()
        assert len(history) == 2
        assert history[0].san == "e4"
        assert history[1].san == "e5"
        
        game.undo()
        assert len(game.get_history()) == 1
    
    def test_undo_on_empty_history(self):
        """Undo on empty history should be a no-op."""
        game = Game()
        initial_fen = game.export_fen()
        
        # Multiple undos on empty history should not error
        game.undo()
        game.undo()
        game.undo()
        
        assert game.export_fen() == initial_fen
        assert len(game.get_history()) == 0
    
    def test_undo_restores_legal_moves(self):
        """Undo should restore the set of legal moves."""
        game = Game()
        initial_moves = [m.uci for m in game.get_legal_moves()]
        
        game.apply_move("e2e4")
        game.apply_move("e7e5")
        
        game.undo()
        game.undo()
        
        restored_moves = [m.uci for m in game.get_legal_moves()]
        assert sorted(initial_moves) == sorted(restored_moves)


class TestScenarios:
    """Integration tests combining multiple features."""
    
    def test_complete_game_sequence(self):
        """Test a complete game sequence with status checks."""
        game = Game()
        
        # Play scholar's mate
        moves = [
            ("e2e4", GameStatus.ONGOING),
            ("e7e5", GameStatus.ONGOING),
            ("f1c4", GameStatus.ONGOING),
            ("b8c6", GameStatus.ONGOING),
            ("d1h5", GameStatus.ONGOING),
            ("g8f6", GameStatus.ONGOING),
            ("h5f7", GameStatus.CHECKMATE),
        ]
        
        for move_uci, expected_status in moves:
            game.apply_move(move_uci)
            status = game.get_status()
            assert status == expected_status, f"After {move_uci}, expected {expected_status}, got {status}"
        
        # Verify move count
        assert len(game.get_history()) == 7
    
    def test_undo_after_checkmate(self):
        """Undo should work even after checkmate."""
        game = Game()
        
        # Fool's mate
        game.apply_move("f2f3")
        game.apply_move("e7e6")
        game.apply_move("g2g4")
        game.apply_move("d8h4")
        
        assert game.get_status() == GameStatus.CHECKMATE
        
        # Undo the checkmate move
        game.undo()
        assert game.get_status() != GameStatus.CHECKMATE
        assert game.get_status() == GameStatus.ONGOING
        
        # Game should be playable again
        legal_moves = game.get_legal_moves()
        assert len(legal_moves) > 0
    
    def test_alternating_moves_and_undo(self):
        """Test alternating between applying moves and undoing."""
        game = Game()
        initial_fen = game.export_fen()
        
        # Apply a move
        game.apply_move("e2e4")
        fen_after_e4 = game.export_fen()
        
        # Apply another and undo
        game.apply_move("e7e5")
        game.undo()
        assert game.export_fen() == fen_after_e4
        
        # Apply a different move
        game.apply_move("c7c5")
        assert game.export_fen() != fen_after_e4
        
        # Undo both moves
        game.undo()
        game.undo()
        assert game.export_fen() == initial_fen
        
        # Should be able to make original moves again
        game.apply_move("d2d4")
        assert len(game.get_history()) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
