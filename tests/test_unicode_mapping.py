#!/usr/bin/env python3
"""
Test suite for Unicode piece mapping in BoardWidget.

This module tests the PIECE_UNICODE mapping constant that converts
piece descriptors to Unicode chess glyphs.
"""

import pytest


class TestUnicodePieceMapping:
    """Tests for the PIECE_UNICODE constant."""
    
    def test_mapping_has_exactly_12_entries(self):
        """Test that the mapping contains exactly 12 piece combinations."""
        from chess_app.gui.board_widget import PIECE_UNICODE
        
        # Should have 6 piece types × 2 colors = 12 entries
        assert len(PIECE_UNICODE) == 12
    
    def test_white_pawn_unicode(self):
        """Test that white pawn maps to U+2659 (♙)."""
        from chess_app.gui.board_widget import PIECE_UNICODE
        
        assert PIECE_UNICODE[("p", "white")] == "\u2659"
    
    def test_white_knight_unicode(self):
        """Test that white knight maps to U+2658 (♘)."""
        from chess_app.gui.board_widget import PIECE_UNICODE
        
        assert PIECE_UNICODE[("n", "white")] == "\u2658"
    
    def test_white_bishop_unicode(self):
        """Test that white bishop maps to U+2657 (♗)."""
        from chess_app.gui.board_widget import PIECE_UNICODE
        
        assert PIECE_UNICODE[("b", "white")] == "\u2657"
    
    def test_white_rook_unicode(self):
        """Test that white rook maps to U+2656 (♖)."""
        from chess_app.gui.board_widget import PIECE_UNICODE
        
        assert PIECE_UNICODE[("r", "white")] == "\u2656"
    
    def test_white_queen_unicode(self):
        """Test that white queen maps to U+2655 (♕)."""
        from chess_app.gui.board_widget import PIECE_UNICODE
        
        assert PIECE_UNICODE[("q", "white")] == "\u2655"
    
    def test_white_king_unicode(self):
        """Test that white king maps to U+2654 (♔)."""
        from chess_app.gui.board_widget import PIECE_UNICODE
        
        assert PIECE_UNICODE[("k", "white")] == "\u2654"
    
    def test_black_pawn_unicode(self):
        """Test that black pawn maps to U+265F (♟)."""
        from chess_app.gui.board_widget import PIECE_UNICODE
        
        assert PIECE_UNICODE[("p", "black")] == "\u265F"
    
    def test_black_knight_unicode(self):
        """Test that black knight maps to U+265E (♞)."""
        from chess_app.gui.board_widget import PIECE_UNICODE
        
        assert PIECE_UNICODE[("n", "black")] == "\u265E"
    
    def test_black_bishop_unicode(self):
        """Test that black bishop maps to U+265D (♝)."""
        from chess_app.gui.board_widget import PIECE_UNICODE
        
        assert PIECE_UNICODE[("b", "black")] == "\u265D"
    
    def test_black_rook_unicode(self):
        """Test that black rook maps to U+265C (♜)."""
        from chess_app.gui.board_widget import PIECE_UNICODE
        
        assert PIECE_UNICODE[("r", "black")] == "\u265C"
    
    def test_black_queen_unicode(self):
        """Test that black queen maps to U+265B (♛)."""
        from chess_app.gui.board_widget import PIECE_UNICODE
        
        assert PIECE_UNICODE[("q", "black")] == "\u265B"
    
    def test_black_king_unicode(self):
        """Test that black king maps to U+265A (♚)."""
        from chess_app.gui.board_widget import PIECE_UNICODE
        
        assert PIECE_UNICODE[("k", "black")] == "\u265A"
    
    def test_all_white_pieces_present(self):
        """Test that all white pieces have mappings."""
        from chess_app.gui.board_widget import PIECE_UNICODE
        
        white_pieces = ["p", "n", "b", "r", "q", "k"]
        
        for piece in white_pieces:
            assert (piece, "white") in PIECE_UNICODE
            # Also verify it's a non-empty string
            assert isinstance(PIECE_UNICODE[(piece, "white")], str)
            assert len(PIECE_UNICODE[(piece, "white")]) > 0
    
    def test_all_black_pieces_present(self):
        """Test that all black pieces have mappings."""
        from chess_app.gui.board_widget import PIECE_UNICODE
        
        black_pieces = ["p", "n", "b", "r", "q", "k"]
        
        for piece in black_pieces:
            assert (piece, "black") in PIECE_UNICODE
            # Also verify it's a non-empty string
            assert isinstance(PIECE_UNICODE[(piece, "black")], str)
            assert len(PIECE_UNICODE[(piece, "black")]) > 0
    
    def test_invalid_piece_type_not_in_mapping(self):
        """Test that invalid piece types are not in the mapping."""
        from chess_app.gui.board_widget import PIECE_UNICODE
        
        # Invalid piece types should not be in the mapping
        assert ("x", "white") not in PIECE_UNICODE
        assert ("z", "black") not in PIECE_UNICODE
        assert ("", "white") not in PIECE_UNICODE
    
    def test_invalid_color_not_in_mapping(self):
        """Test that invalid colors are not in the mapping."""
        from chess_app.gui.board_widget import PIECE_UNICODE
        
        # Invalid colors should not be in the mapping
        assert ("p", "red") not in PIECE_UNICODE
        assert ("k", "blue") not in PIECE_UNICODE
        assert ("q", "") not in PIECE_UNICODE
    
    def test_white_and_black_pieces_are_different(self):
        """Test that white and black pieces have different Unicode glyphs."""
        from chess_app.gui.board_widget import PIECE_UNICODE
        
        pieces = ["p", "n", "b", "r", "q", "k"]
        
        for piece in pieces:
            white_glyph = PIECE_UNICODE[(piece, "white")]
            black_glyph = PIECE_UNICODE[(piece, "black")]
            
            # White and black versions should be different
            assert white_glyph != black_glyph
    
    def test_get_with_invalid_key_returns_none(self):
        """Test that using .get() with invalid keys returns None."""
        from chess_app.gui.board_widget import PIECE_UNICODE
        
        # Using .get() with invalid keys should return None (or default)
        assert PIECE_UNICODE.get(("invalid", "white")) is None
        assert PIECE_UNICODE.get(("p", "invalid")) is None
        assert PIECE_UNICODE.get(("x", "y"), "default") == "default"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

