#!/usr/bin/env python3
"""
Unit tests for domain helpers related to side-to-move and piece ownership.

This module validates:
- get_side_to_move() returns correct side after various game operations
- get_piece_side() correctly identifies piece ownership across different positions
- Edge cases and invalid inputs are handled gracefully
- Integration with apply_move() and undo() operations
"""

import pytest
from chess_app.game import Game, Side


class TestSideToMove:
    """Tests for the get_side_to_move() helper method."""
    
    def test_initial_position_white_to_move(self):
        """Starting position should have White to move."""
        game = Game()
        assert game.get_side_to_move() == Side.WHITE
    
    def test_after_one_move_black_to_move(self):
        """After White's first move, it should be Black to move."""
        game = Game()
        game.apply_move("e2e4")
        assert game.get_side_to_move() == Side.BLACK
    
    def test_after_two_moves_white_to_move(self):
        """After both sides move once, it should be White to move again."""
        game = Game()
        game.apply_move("e2e4")
        game.apply_move("e7e5")
        assert game.get_side_to_move() == Side.WHITE
    
    def test_side_to_move_alternates(self):
        """Side to move should alternate correctly through a game sequence."""
        game = Game()
        moves = ["e2e4", "e7e5", "g1f3", "b8c6", "f1c4", "g8f6"]
        expected_sides = [Side.BLACK, Side.WHITE, Side.BLACK, Side.WHITE, Side.BLACK, Side.WHITE]
        
        for move, expected_side in zip(moves, expected_sides):
            game.apply_move(move)
            assert game.get_side_to_move() == expected_side
    
    def test_side_to_move_after_undo(self):
        """Side to move should revert correctly after undo."""
        game = Game()
        
        # Initially White to move
        assert game.get_side_to_move() == Side.WHITE
        
        # After White moves, Black to move
        game.apply_move("e2e4")
        assert game.get_side_to_move() == Side.BLACK
        
        # After undo, back to White to move
        game.undo()
        assert game.get_side_to_move() == Side.WHITE
    
    def test_side_to_move_from_custom_fen_white(self):
        """Side to move should be correctly determined from FEN with White to move."""
        fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
        game = Game.from_fen(fen)
        assert game.get_side_to_move() == Side.WHITE
    
    def test_side_to_move_from_custom_fen_black(self):
        """Side to move should be correctly determined from FEN with Black to move."""
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
        game = Game.from_fen(fen)
        assert game.get_side_to_move() == Side.BLACK


class TestPieceOwnershipStartingPosition:
    """Tests for get_piece_side() on the starting position."""
    
    def test_white_pieces_rank_1(self):
        """All pieces on rank 1 should be White."""
        game = Game()
        
        # Test all squares on rank 1
        for file in "abcdefgh":
            square = f"{file}1"
            assert game.get_piece_side(square) == Side.WHITE, \
                f"Square {square} should contain a White piece"
    
    def test_white_pawns_rank_2(self):
        """All pieces on rank 2 should be White pawns."""
        game = Game()
        
        # Test all squares on rank 2
        for file in "abcdefgh":
            square = f"{file}2"
            assert game.get_piece_side(square) == Side.WHITE, \
                f"Square {square} should contain a White pawn"
    
    def test_empty_squares_ranks_3_to_6(self):
        """All squares on ranks 3-6 should be empty in starting position."""
        game = Game()
        
        # Test all squares on ranks 3-6
        for rank in "3456":
            for file in "abcdefgh":
                square = f"{file}{rank}"
                assert game.get_piece_side(square) is None, \
                    f"Square {square} should be empty"
    
    def test_black_pawns_rank_7(self):
        """All pieces on rank 7 should be Black pawns."""
        game = Game()
        
        # Test all squares on rank 7
        for file in "abcdefgh":
            square = f"{file}7"
            assert game.get_piece_side(square) == Side.BLACK, \
                f"Square {square} should contain a Black pawn"
    
    def test_black_pieces_rank_8(self):
        """All pieces on rank 8 should be Black."""
        game = Game()
        
        # Test all squares on rank 8
        for file in "abcdefgh":
            square = f"{file}8"
            assert game.get_piece_side(square) == Side.BLACK, \
                f"Square {square} should contain a Black piece"
    
    def test_specific_pieces_starting_position(self):
        """Test specific pieces in starting position."""
        game = Game()
        
        # White pieces
        assert game.get_piece_side("e1") == Side.WHITE  # King
        assert game.get_piece_side("d1") == Side.WHITE  # Queen
        assert game.get_piece_side("a1") == Side.WHITE  # Rook
        assert game.get_piece_side("h1") == Side.WHITE  # Rook
        assert game.get_piece_side("b1") == Side.WHITE  # Knight
        assert game.get_piece_side("g1") == Side.WHITE  # Knight
        
        # Black pieces
        assert game.get_piece_side("e8") == Side.BLACK  # King
        assert game.get_piece_side("d8") == Side.BLACK  # Queen
        assert game.get_piece_side("a8") == Side.BLACK  # Rook
        assert game.get_piece_side("h8") == Side.BLACK  # Rook
        assert game.get_piece_side("b8") == Side.BLACK  # Knight
        assert game.get_piece_side("g8") == Side.BLACK  # Knight


class TestPieceOwnershipAfterMoves:
    """Tests for get_piece_side() after moves are applied."""
    
    def test_piece_relocation_simple(self):
        """Piece ownership should follow the piece when it moves."""
        game = Game()
        
        # Initially e2 has White pawn, e4 is empty
        assert game.get_piece_side("e2") == Side.WHITE
        assert game.get_piece_side("e4") is None
        
        # After e2-e4, e2 is empty, e4 has White pawn
        game.apply_move("e2e4")
        assert game.get_piece_side("e2") is None
        assert game.get_piece_side("e4") == Side.WHITE
    
    def test_piece_relocation_multiple_moves(self):
        """Track piece ownership through multiple moves."""
        game = Game()
        
        # Move White pawn e2-e4
        game.apply_move("e2e4")
        assert game.get_piece_side("e4") == Side.WHITE
        assert game.get_piece_side("e2") is None
        
        # Move Black pawn e7-e5
        game.apply_move("e7e5")
        assert game.get_piece_side("e5") == Side.BLACK
        assert game.get_piece_side("e7") is None
        
        # Move White knight g1-f3
        game.apply_move("g1f3")
        assert game.get_piece_side("f3") == Side.WHITE
        assert game.get_piece_side("g1") is None
        
        # Move Black knight b8-c6
        game.apply_move("b8c6")
        assert game.get_piece_side("c6") == Side.BLACK
        assert game.get_piece_side("b8") is None
    
    def test_captured_square_becomes_empty_then_occupied(self):
        """After a capture, the square should show the capturing side."""
        # Position where White can capture on e5
        fen = "rnbqkbnr/pppp1ppp/8/4p3/3P4/8/PPP1PPPP/RNBQKBNR w KQkq - 0 2"
        game = Game.from_fen(fen)
        
        # e5 has Black pawn, d4 has White pawn
        assert game.get_piece_side("e5") == Side.BLACK
        assert game.get_piece_side("d4") == Side.WHITE
        
        # After dxe5, e5 has White pawn, d4 is empty
        game.apply_move("d4e5")
        assert game.get_piece_side("e5") == Side.WHITE
        assert game.get_piece_side("d4") is None
    
    def test_piece_ownership_from_custom_fen(self):
        """Piece ownership should be correct from a custom FEN position."""
        # Position after 1.e4 e5 2.Nf3 Nc6 3.Bb5
        fen = "r1bqkbnr/pppp1ppp/2n5/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"
        game = Game.from_fen(fen)
        
        # White pieces
        assert game.get_piece_side("e4") == Side.WHITE  # Pawn
        assert game.get_piece_side("f3") == Side.WHITE  # Knight
        assert game.get_piece_side("b5") == Side.WHITE  # Bishop
        assert game.get_piece_side("e1") == Side.WHITE  # King
        
        # Black pieces
        assert game.get_piece_side("e5") == Side.BLACK  # Pawn
        assert game.get_piece_side("c6") == Side.BLACK  # Knight
        assert game.get_piece_side("e8") == Side.BLACK  # King
        
        # Empty squares
        assert game.get_piece_side("e2") is None  # Pawn moved from here
        assert game.get_piece_side("g1") is None  # Knight moved from here
        assert game.get_piece_side("d4") is None  # Empty center square


class TestEdgeCases:
    """Tests for edge cases and invalid inputs."""
    
    def test_invalid_square_notation_returns_none(self):
        """Invalid square strings should return None gracefully."""
        game = Game()
        
        # Various invalid square notations
        assert game.get_piece_side("z9") is None
        assert game.get_piece_side("i1") is None
        assert game.get_piece_side("a9") is None
        assert game.get_piece_side("invalid") is None
        assert game.get_piece_side("123") is None
        assert game.get_piece_side("e") is None
        assert game.get_piece_side("4") is None
        assert game.get_piece_side("ee4") is None
    
    def test_empty_string_returns_none(self):
        """Empty string should return None gracefully."""
        game = Game()
        assert game.get_piece_side("") is None
    
    def test_case_insensitivity(self):
        """Square notation should be case-insensitive."""
        game = Game()
        
        # Lowercase and uppercase should give same result
        assert game.get_piece_side("e2") == Side.WHITE
        assert game.get_piece_side("E2") == Side.WHITE
        assert game.get_piece_side("e4") is None
        assert game.get_piece_side("E4") is None
        
        # Mixed case
        assert game.get_piece_side("E2") == game.get_piece_side("e2")
        assert game.get_piece_side("H8") == game.get_piece_side("h8")
    
    def test_whitespace_in_square_notation(self):
        """Square notation with whitespace should be handled gracefully."""
        game = Game()
        
        # These should return None (invalid format)
        assert game.get_piece_side(" e2") is None
        assert game.get_piece_side("e2 ") is None
        assert game.get_piece_side(" e2 ") is None
        assert game.get_piece_side("e 2") is None


class TestIntegrationWithGameOperations:
    """Tests for get_piece_side() integration with other game operations."""
    
    def test_ownership_after_apply_move_reflects_new_position(self):
        """Piece ownership should immediately reflect changes after apply_move()."""
        game = Game()
        
        # Apply a series of moves and verify ownership after each
        game.apply_move("e2e4")
        assert game.get_piece_side("e4") == Side.WHITE
        assert game.get_piece_side("e2") is None
        
        game.apply_move("d7d5")
        assert game.get_piece_side("d5") == Side.BLACK
        assert game.get_piece_side("d7") is None
        
        game.apply_move("e4d5")  # Capture
        assert game.get_piece_side("d5") == Side.WHITE
        assert game.get_piece_side("e4") is None
    
    def test_ownership_after_undo_reverts_correctly(self):
        """Piece ownership should revert correctly after undo."""
        game = Game()
        
        # Initial state
        assert game.get_piece_side("e2") == Side.WHITE
        assert game.get_piece_side("e4") is None
        
        # After move
        game.apply_move("e2e4")
        assert game.get_piece_side("e2") is None
        assert game.get_piece_side("e4") == Side.WHITE
        
        # After undo, should revert
        game.undo()
        assert game.get_piece_side("e2") == Side.WHITE
        assert game.get_piece_side("e4") is None
    
    def test_ownership_after_multiple_undos(self):
        """Piece ownership should track correctly through multiple undos."""
        game = Game()
        
        # Apply several moves
        game.apply_move("e2e4")
        game.apply_move("e7e5")
        game.apply_move("g1f3")
        
        # Verify state
        assert game.get_piece_side("f3") == Side.WHITE
        assert game.get_piece_side("g1") is None
        
        # Undo back to starting position
        game.undo()
        assert game.get_piece_side("f3") is None
        assert game.get_piece_side("g1") == Side.WHITE
        
        game.undo()
        assert game.get_piece_side("e5") is None
        assert game.get_piece_side("e7") == Side.BLACK
        
        game.undo()
        assert game.get_piece_side("e4") is None
        assert game.get_piece_side("e2") == Side.WHITE
    
    def test_ownership_with_promotions(self):
        """Promoted pieces should show correct side ownership."""
        # Position where White can promote
        fen = "4k3/P7/8/8/8/8/8/4K3 w - - 0 1"
        game = Game.from_fen(fen)
        
        # Before promotion, a7 has White pawn
        assert game.get_piece_side("a7") == Side.WHITE
        assert game.get_piece_side("a8") is None
        
        # After promotion to queen, a8 has White piece
        game.apply_move("a7a8q")
        assert game.get_piece_side("a8") == Side.WHITE
        assert game.get_piece_side("a7") is None
    
    def test_ownership_after_castling(self):
        """Piece ownership should be correct after castling moves."""
        # Position where White can castle kingside
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQK2R w KQkq - 0 1"
        game = Game.from_fen(fen)
        
        # Before castling
        assert game.get_piece_side("e1") == Side.WHITE  # King
        assert game.get_piece_side("h1") == Side.WHITE  # Rook
        assert game.get_piece_side("g1") is None
        assert game.get_piece_side("f1") is None
        
        # After castling kingside
        game.apply_move("e1g1")
        assert game.get_piece_side("g1") == Side.WHITE  # King moved here
        assert game.get_piece_side("f1") == Side.WHITE  # Rook moved here
        assert game.get_piece_side("e1") is None        # King left
        assert game.get_piece_side("h1") is None        # Rook left
    
    def test_read_only_guarantee(self):
        """Calling get_piece_side() should not modify game state."""
        game = Game()
        initial_fen = game.export_fen()
        
        # Call get_piece_side() many times
        for _ in range(100):
            game.get_piece_side("e2")
            game.get_piece_side("e4")
            game.get_piece_side("a1")
            game.get_piece_side("h8")
            game.get_piece_side("invalid")
        
        # FEN should be unchanged
        assert game.export_fen() == initial_fen
        
        # History should be unchanged
        assert len(game.get_history()) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

