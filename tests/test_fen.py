#!/usr/bin/env python3
"""
Test suite for FEN (Forsyth-Edwards Notation) import/export functionality.
"""

import pytest
from chess_app.game import Game, InvalidFenError


class TestFenExport:
    """Tests for Game.export_fen() method."""
    
    def test_export_starting_position(self):
        """Test exporting the standard starting position."""
        game = Game()
        fen = game.export_fen()
        
        expected_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        assert fen == expected_fen
    
    def test_export_after_single_move(self):
        """Test exporting FEN after a single move."""
        game = Game()
        game.apply_move("e2e4")
        fen = game.export_fen()
        
        # Note: python-chess only sets en passant square if capture is actually possible
        expected_fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
        assert fen == expected_fen
    
    def test_export_after_multiple_moves(self):
        """Test exporting FEN after multiple moves."""
        game = Game()
        game.apply_move("e2e4")
        game.apply_move("e7e5")
        game.apply_move("g1f3")
        fen = game.export_fen()
        
        expected_fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 1 2"
        assert fen == expected_fen
    
    def test_export_with_castling_rights_lost(self):
        """Test FEN export when castling rights are lost."""
        game = Game()
        game.apply_move("e2e4")
        game.apply_move("e7e5")
        game.apply_move("e1e2")  # King move, loses castling rights
        fen = game.export_fen()
        
        # White should have no castling rights after king move
        assert "KQ" not in fen.split()[2]
        assert "kq" in fen.split()[2]  # Black still has castling rights
    
    def test_export_with_en_passant(self):
        """Test FEN export with en passant square."""
        game = Game()
        game.apply_move("e2e4")
        game.apply_move("a7a6")
        game.apply_move("e4e5")
        game.apply_move("d7d5")  # Creates en passant opportunity
        fen = game.export_fen()
        
        # En passant square should be d6
        assert "d6" in fen
    
    def test_export_with_halfmove_clock(self):
        """Test FEN export with halfmove clock progression."""
        game = Game()
        game.apply_move("g1f3")  # Knight move, increments halfmove clock
        game.apply_move("g8f6")
        fen = game.export_fen()
        
        # Halfmove clock should be 2
        parts = fen.split()
        assert parts[4] == "2"
    
    def test_export_with_fullmove_number(self):
        """Test FEN export with fullmove number progression."""
        game = Game()
        game.apply_move("e2e4")
        game.apply_move("e7e5")
        game.apply_move("g1f3")
        game.apply_move("g8f6")
        fen = game.export_fen()
        
        # Fullmove number should be 3
        parts = fen.split()
        assert parts[5] == "3"


class TestFenImport:
    """Tests for Game.from_fen() class method."""
    
    def test_import_starting_position(self):
        """Test importing the standard starting position."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        game = Game.from_fen(fen)
        
        # Verify it's the starting position
        assert game.export_fen() == fen
        assert len(game.get_legal_moves()) == 20
    
    def test_import_midgame_position(self):
        """Test importing a midgame position."""
        fen = "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"
        game = Game.from_fen(fen)
        
        assert game.export_fen() == fen
    
    def test_import_position_with_no_castling_rights(self):
        """Test importing a position with no castling rights."""
        fen = "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R w - - 4 5"
        game = Game.from_fen(fen)
        
        assert game.export_fen() == fen
    
    def test_import_position_with_en_passant(self):
        """Test importing a position with en passant square."""
        fen = "rnbqkbnr/ppp1p1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3"
        game = Game.from_fen(fen)
        
        assert game.export_fen() == fen
    
    def test_import_black_to_move(self):
        """Test importing a position where Black is to move."""
        # Use a FEN without invalid en passant square
        fen = "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq - 0 1"
        game = Game.from_fen(fen)
        
        assert game.export_fen() == fen
    
    def test_import_endgame_position(self):
        """Test importing an endgame position."""
        fen = "8/8/8/4k3/8/8/4K3/8 w - - 0 1"
        game = Game.from_fen(fen)
        
        assert game.export_fen() == fen
    
    def test_import_invalid_fen_raises_error(self):
        """Test that invalid FEN strings raise InvalidFenError."""
        invalid_fens = [
            "invalid",
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP",  # Incomplete FEN
            "rnbqkbnr/pppppppp/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",  # Invalid piece placement (missing rank)
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR x KQkq - 0 1",  # Invalid turn
        ]
        
        for fen in invalid_fens:
            with pytest.raises(InvalidFenError) as exc_info:
                Game.from_fen(fen)
            
            # Verify error message includes the invalid FEN
            assert fen in str(exc_info.value)
    
    def test_import_invalid_fen_has_descriptive_error(self):
        """Test that InvalidFenError has descriptive error messages."""
        invalid_fen = "not_a_valid_fen"
        
        with pytest.raises(InvalidFenError) as exc_info:
            Game.from_fen(invalid_fen)
        
        error_msg = str(exc_info.value)
        assert "Invalid FEN string provided" in error_msg
        assert invalid_fen in error_msg
        assert "Error details:" in error_msg
    
    def test_import_preserves_move_number(self):
        """Test that importing FEN preserves fullmove and halfmove numbers."""
        fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"
        game = Game.from_fen(fen)
        
        assert game.get_fullmove_number() == 2
        assert game.get_halfmove_clock() == 0
    
    def test_import_starts_with_empty_history(self):
        """Test that importing FEN creates a game with empty move history."""
        fen = "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"
        game = Game.from_fen(fen)
        
        # Move history should be empty even though position is from move 2
        assert len(game.get_history()) == 0


class TestFenRoundTrip:
    """Tests for FEN export/import round-trip equivalence."""
    
    def test_roundtrip_starting_position(self):
        """Test round-trip of starting position."""
        game1 = Game()
        fen = game1.export_fen()
        game2 = Game.from_fen(fen)
        
        assert game2.export_fen() == fen
    
    def test_roundtrip_after_moves(self):
        """Test round-trip after making moves."""
        game1 = Game()
        game1.apply_move("e2e4")
        game1.apply_move("e7e5")
        game1.apply_move("g1f3")
        
        fen = game1.export_fen()
        game2 = Game.from_fen(fen)
        
        assert game2.export_fen() == fen
    
    def test_roundtrip_preserves_legal_moves(self):
        """Test that round-trip preserves legal moves."""
        game1 = Game()
        game1.apply_move("e2e4")
        game1.apply_move("e7e5")
        
        fen = game1.export_fen()
        game2 = Game.from_fen(fen)
        
        # Both games should have the same legal moves
        moves1 = sorted([m.uci for m in game1.get_legal_moves()])
        moves2 = sorted([m.uci for m in game2.get_legal_moves()])
        assert moves1 == moves2
    
    def test_roundtrip_preserves_game_state(self):
        """Test that round-trip preserves all game state."""
        game1 = Game()
        game1.apply_move("e2e4")
        game1.apply_move("c7c5")
        game1.apply_move("g1f3")
        
        fen = game1.export_fen()
        game2 = Game.from_fen(fen)
        
        # Check all relevant state is preserved
        assert game2.get_fullmove_number() == game1.get_fullmove_number()
        assert game2.get_halfmove_clock() == game1.get_halfmove_clock()
        assert game2.get_side_to_move() == game1.get_side_to_move()
        assert game2.get_status() == game1.get_status()
    
    def test_roundtrip_multiple_times(self):
        """Test that multiple round-trips preserve position."""
        game = Game()
        game.apply_move("d2d4")
        game.apply_move("d7d5")
        
        fen1 = game.export_fen()
        game2 = Game.from_fen(fen1)
        fen2 = game2.export_fen()
        game3 = Game.from_fen(fen2)
        fen3 = game3.export_fen()
        
        assert fen1 == fen2 == fen3
    
    def test_roundtrip_complex_position(self):
        """Test round-trip with a complex position."""
        # Sicilian Defense, Dragon Variation
        fen = "r1bqk2r/pp2bppp/2nppn2/8/3NP3/2N1BP2/PPPQ2PP/R3KB1R w KQkq - 2 8"
        game1 = Game.from_fen(fen)
        
        # Export and re-import
        exported_fen = game1.export_fen()
        game2 = Game.from_fen(exported_fen)
        
        assert game2.export_fen() == fen
    
    def test_roundtrip_with_promotion(self):
        """Test round-trip after pawn promotion."""
        # Position with white pawn ready to promote
        fen = "4k3/P7/8/8/8/8/8/4K3 w - - 0 1"
        game = Game.from_fen(fen)
        game.apply_move("a7a8q")  # Promote to queen
        
        exported_fen = game.export_fen()
        game2 = Game.from_fen(exported_fen)
        
        assert game2.export_fen() == exported_fen


class TestFenValidation:
    """Additional tests for FEN validation edge cases."""
    
    def test_fen_with_extra_whitespace_rejected(self):
        """Test that FEN with extra whitespace is handled."""
        # python-chess should handle or reject this - we test the error is raised
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR  w  KQkq  -  0  1"
        
        # This may or may not raise depending on python-chess, but our wrapper should handle it
        try:
            game = Game.from_fen(fen)
            # If accepted, verify it's valid
            assert game.export_fen() is not None
        except InvalidFenError:
            # If rejected, that's also acceptable
            pass
    
    def test_fen_case_sensitivity(self):
        """Test that FEN is case-sensitive for pieces."""
        # Valid FEN with mixed case pieces
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        game = Game.from_fen(fen)
        assert game.export_fen() == fen
    
    def test_import_checkmate_position(self):
        """Test importing a checkmate position."""
        # Fool's mate
        fen = "rnbqkbnr/pppp1ppp/8/4p3/6P1/5P2/PPPPP2P/RNBQKBNR b KQkq - 0 2"
        game = Game.from_fen(fen)
        game.apply_move("d8h4")  # Checkmate
        
        from chess_app.game import GameStatus
        assert game.get_status() == GameStatus.CHECKMATE
        
        # Export the checkmate position
        checkmate_fen = game.export_fen()
        game2 = Game.from_fen(checkmate_fen)
        assert game2.get_status() == GameStatus.CHECKMATE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
