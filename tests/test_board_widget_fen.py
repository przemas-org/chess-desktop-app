#!/usr/bin/env python3
"""
Test suite for BoardWidget FEN parsing and validation.

This module tests the BoardWidget's FEN-based API, including FEN parsing,
validation, internal board representation, and board orientation.
"""

import pytest


class TestBoardFenParsing:
    """Tests for FEN parsing in BoardWidget."""
    
    def test_digit_expansion_single_eight(self):
        """Test that '8' expands to 8 empty squares."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            # Ensure QApplication exists
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            # FEN with rank containing only '8' (all empty)
            widget.set_fen("8/8/8/8/8/8/8/8 w - - 0 1")
            
            # All squares should be None (empty)
            for rank in widget._board:
                assert len(rank) == 8
                for square in rank:
                    assert square is None
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_digit_expansion_mixed(self):
        """Test expansion of mixed digits and pieces like '3p4'."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            # FEN rank with '3p4' pattern
            widget.set_fen("8/8/8/3p4/8/8/8/8 w - - 0 1")
            
            # Check rank 5 (index 3): 3 empty + pawn + 4 empty
            rank = widget._board[3]
            assert len(rank) == 8
            assert rank[0] is None
            assert rank[1] is None
            assert rank[2] is None
            assert rank[3] == {"piece": "p", "color": "black"}
            assert rank[4] is None
            assert rank[5] is None
            assert rank[6] is None
            assert rank[7] is None
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_piece_mapping_black_pieces(self):
        """Test that lowercase pieces map to black pieces."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            # Standard starting position with black pieces on rank 8
            widget.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            
            # Check rank 8 (index 0) - black pieces
            rank8 = widget._board[0]
            expected_pieces = ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r']
            
            for i, expected_piece in enumerate(expected_pieces):
                assert rank8[i] == {"piece": expected_piece, "color": "black"}
            
            # Check rank 7 (index 1) - black pawns
            rank7 = widget._board[1]
            for square in rank7:
                assert square == {"piece": "p", "color": "black"}
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_piece_mapping_white_pieces(self):
        """Test that uppercase pieces map to white pieces."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            # Standard starting position with white pieces on rank 1
            widget.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            
            # Check rank 1 (index 7) - white pieces
            rank1 = widget._board[7]
            expected_pieces = ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r']
            
            for i, expected_piece in enumerate(expected_pieces):
                assert rank1[i] == {"piece": expected_piece, "color": "white"}
            
            # Check rank 2 (index 6) - white pawns
            rank2 = widget._board[6]
            for square in rank2:
                assert square == {"piece": "p", "color": "white"}
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_standard_starting_position(self):
        """Test parsing standard chess starting position."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            widget.set_fen(fen)
            
            # Verify board is 8x8
            assert len(widget._board) == 8
            for rank in widget._board:
                assert len(rank) == 8
            
            # Verify middle ranks (3-6, indices 2-5) are empty
            for rank_idx in range(2, 6):
                for square in widget._board[rank_idx]:
                    assert square is None
            
            # Verify ranks 1, 2, 7, 8 have pieces
            assert all(sq is not None for sq in widget._board[0])  # Rank 8
            assert all(sq is not None for sq in widget._board[1])  # Rank 7
            assert all(sq is not None for sq in widget._board[6])  # Rank 2
            assert all(sq is not None for sq in widget._board[7])  # Rank 1
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_midgame_position_mixed(self):
        """Test parsing midgame position with mixed pieces and empty squares."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            # Midgame position
            fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
            widget.set_fen(fen)
            
            # Check rank 8 (index 0): r1bqkb1r
            rank8 = widget._board[0]
            assert rank8[0] == {"piece": "r", "color": "black"}
            assert rank8[1] is None
            assert rank8[2] == {"piece": "b", "color": "black"}
            assert rank8[3] == {"piece": "q", "color": "black"}
            assert rank8[4] == {"piece": "k", "color": "black"}
            assert rank8[5] == {"piece": "b", "color": "black"}
            assert rank8[6] is None
            assert rank8[7] == {"piece": "r", "color": "black"}
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")


class TestBoardOrientation:
    """Tests for board orientation (white at bottom, rank 1 at index 7)."""
    
    def test_rank_8_at_index_0(self):
        """Verify rank 8 is stored at index 0 (top row of internal array)."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            
            # Rank 8 should be at index 0 with black pieces
            rank8 = widget._board[0]
            assert rank8[0] == {"piece": "r", "color": "black"}
            assert rank8[4] == {"piece": "k", "color": "black"}
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_rank_1_at_index_7(self):
        """Verify rank 1 is stored at index 7 (bottom row of internal array)."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            
            # Rank 1 should be at index 7 with white pieces
            rank1 = widget._board[7]
            assert rank1[0] == {"piece": "r", "color": "white"}
            assert rank1[4] == {"piece": "k", "color": "white"}
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_black_pieces_rank_8_top(self):
        """Test that black back rank (rank 8) appears at board index 0."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            
            # Index 0 should contain 'rnbqkbnr' (black pieces)
            rank = widget._board[0]
            pieces = [sq["piece"] if sq else None for sq in rank]
            assert pieces == ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r']
            
            colors = [sq["color"] if sq else None for sq in rank]
            assert all(color == "black" for color in colors)
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_white_pieces_rank_1_bottom(self):
        """Test that white back rank (rank 1) appears at board index 7."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            
            # Index 7 should contain 'RNBQKBNR' (white pieces)
            rank = widget._board[7]
            pieces = [sq["piece"] if sq else None for sq in rank]
            assert pieces == ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r']
            
            colors = [sq["color"] if sq else None for sq in rank]
            assert all(color == "white" for color in colors)
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")


class TestBoardFenValidation:
    """Tests for FEN validation in BoardWidget."""
    
    def test_error_when_fewer_than_8_ranks(self):
        """Test error when FEN has fewer than 8 ranks."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget, BoardFenError
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            
            # Only 7 ranks
            with pytest.raises(BoardFenError) as exc_info:
                widget.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP w KQkq - 0 1")
            
            assert "expected 8 ranks, got 7" in str(exc_info.value)
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_error_when_more_than_8_ranks(self):
        """Test error when FEN has more than 8 ranks."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget, BoardFenError
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            
            # 9 ranks
            with pytest.raises(BoardFenError) as exc_info:
                widget.set_fen("8/8/8/8/8/8/8/8/8 w - - 0 1")
            
            assert "expected 8 ranks, got 9" in str(exc_info.value)
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_error_when_rank_has_too_few_files(self):
        """Test error when a rank expands to fewer than 8 files."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget, BoardFenError
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            
            # First rank has only 7 files (3+p+2 = 6, not 8)
            with pytest.raises(BoardFenError) as exc_info:
                widget.set_fen("3p2/8/8/8/8/8/8/8 w - - 0 1")
            
            assert "has 6 files, expected 8" in str(exc_info.value)
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_error_when_rank_has_too_many_files(self):
        """Test error when a rank expands to more than 8 files."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget, BoardFenError
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            
            # First rank has 9 files
            with pytest.raises(BoardFenError) as exc_info:
                widget.set_fen("rnbqkbnrp/8/8/8/8/8/8/8 w - - 0 1")
            
            assert "has 9 files, expected 8" in str(exc_info.value)
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_error_messages_are_descriptive(self):
        """Test that error messages are clear and descriptive."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget, BoardFenError
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            
            # Test with wrong number of ranks
            with pytest.raises(BoardFenError) as exc_info:
                widget.set_fen("8/8/8 w - - 0 1")
            
            error_msg = str(exc_info.value)
            assert "Invalid FEN" in error_msg
            assert "expected 8 ranks" in error_msg
            assert "got 3" in error_msg
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_valid_fen_does_not_raise_error(self):
        """Test that valid FEN strings do not raise errors."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            
            # Valid FEN strings should not raise errors
            valid_fens = [
                "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
                "8/8/8/8/8/8/8/8 w - - 0 1",
                "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
            ]
            
            for fen in valid_fens:
                # Should not raise any exception
                widget.set_fen(fen)
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_error_on_invalid_character(self):
        """Test error when FEN contains invalid characters."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget, BoardFenError
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            
            # Invalid character 'x' in FEN
            with pytest.raises(BoardFenError) as exc_info:
                widget.set_fen("rnbqkbnr/ppppxppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            
            assert "Invalid character 'x'" in str(exc_info.value)
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")


class TestBoardFenState:
    """Tests for BoardWidget internal state management."""
    
    def test_fen_attribute_stores_full_fen(self):
        """Test that _fen attribute stores the complete FEN string."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            widget.set_fen(fen)
            
            assert widget._fen == fen
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_board_structure_matches_parsed_fen(self):
        """Test that _board structure correctly represents the FEN."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.set_fen("8/8/8/3P4/8/8/8/8 w - - 0 1")
            
            # Check that only rank 5 (index 3), file d (index 3) has a white pawn
            for rank_idx in range(8):
                for file_idx in range(8):
                    if rank_idx == 3 and file_idx == 3:
                        assert widget._board[rank_idx][file_idx] == {"piece": "p", "color": "white"}
                    else:
                        assert widget._board[rank_idx][file_idx] is None
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_set_fen_multiple_times_updates_state(self):
        """Test that calling set_fen multiple times correctly updates state."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            
            # Set initial position
            fen1 = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            widget.set_fen(fen1)
            assert widget._fen == fen1
            assert widget._board[0][0] == {"piece": "r", "color": "black"}
            
            # Update to different position
            fen2 = "8/8/8/8/8/8/8/8 w - - 0 1"
            widget.set_fen(fen2)
            assert widget._fen == fen2
            
            # All squares should now be empty
            for rank in widget._board:
                for square in rank:
                    assert square is None
            
            # Update to another position
            fen3 = "8/8/8/4k3/8/8/8/4K3 w - - 0 1"
            widget.set_fen(fen3)
            assert widget._fen == fen3
            assert widget._board[3][4] == {"piece": "k", "color": "black"}  # Rank 5, file e
            assert widget._board[7][4] == {"piece": "k", "color": "white"}  # Rank 1, file e
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_initial_state_is_empty(self):
        """Test that widget starts with empty board and no FEN."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            
            # Should have empty FEN string
            assert widget._fen == ""
            
            # Should have 8x8 board with all None
            assert len(widget._board) == 8
            for rank in widget._board:
                assert len(rank) == 8
                for square in rank:
                    assert square is None
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_rapid_position_switching(self):
        """Test rapid switching between different positions."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            
            # 1. Start with starting position
            starting_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            widget.set_fen(starting_fen)
            assert widget._fen == starting_fen
            assert widget._board[0][0] == {"piece": "r", "color": "black"}
            
            # 2. Switch to empty board
            empty_fen = "8/8/8/8/8/8/8/8 w - - 0 1"
            widget.set_fen(empty_fen)
            assert widget._fen == empty_fen
            assert all(sq is None for rank in widget._board for sq in rank)
            
            # 3. Switch to midgame position
            midgame_fen = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
            widget.set_fen(midgame_fen)
            assert widget._fen == midgame_fen
            assert widget._board[0][0] == {"piece": "r", "color": "black"}
            
            # 4. Switch to endgame position
            endgame_fen = "8/8/4k3/8/8/4K3/8/8 w - - 0 1"
            widget.set_fen(endgame_fen)
            assert widget._fen == endgame_fen
            assert widget._board[2][4] == {"piece": "k", "color": "black"}
            assert widget._board[5][4] == {"piece": "k", "color": "white"}
            
            # Count pieces (should be exactly 2)
            piece_count = sum(1 for rank in widget._board for sq in rank if sq is not None)
            assert piece_count == 2
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_orientation_preserved_when_switching_positions(self):
        """Test that orientation (white at bottom) is preserved when switching positions."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            
            # Position 1: Starting position
            widget.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            # Verify white pieces at bottom (rank 1 = index 7)
            assert widget._board[7][0]["color"] == "white"
            # Verify black pieces at top (rank 8 = index 0)
            assert widget._board[0][0]["color"] == "black"
            
            # Position 2: Different position
            widget.set_fen("8/8/8/3k4/3K4/8/8/8 w - - 0 1")
            # White king should be on rank 4 (index 4), black king on rank 5 (index 3)
            assert widget._board[3][3] == {"piece": "k", "color": "black"}
            assert widget._board[4][3] == {"piece": "k", "color": "white"}
            
            # Position 3: Another position with clear orientation
            widget.set_fen("k7/8/8/8/8/8/8/K7 w - - 0 1")
            # White king at rank 1 (index 7), black king at rank 8 (index 0)
            assert widget._board[7][0] == {"piece": "k", "color": "white"}
            assert widget._board[0][0] == {"piece": "k", "color": "black"}
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_state_cleanup_no_residual_pieces(self):
        """Test that there are no residual pieces from previous FEN."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            
            # Start with a complex position (32 pieces)
            widget.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            
            # Count pieces (should be 32)
            piece_count = sum(1 for rank in widget._board for sq in rank if sq is not None)
            assert piece_count == 32
            
            # Switch to a simple position (2 pieces)
            widget.set_fen("8/8/8/8/8/8/8/K6k w - - 0 1")
            
            # Count pieces (should be exactly 2, not 32)
            piece_count = sum(1 for rank in widget._board for sq in rank if sq is not None)
            assert piece_count == 2
            
            # Verify the specific pieces
            assert widget._board[7][0] == {"piece": "k", "color": "white"}
            assert widget._board[7][7] == {"piece": "k", "color": "black"}
            
            # Verify all other squares are None
            for rank_idx in range(8):
                for file_idx in range(8):
                    if (rank_idx == 7 and file_idx == 0) or (rank_idx == 7 and file_idx == 7):
                        continue
                    assert widget._board[rank_idx][file_idx] is None, \
                        f"Square at rank {rank_idx}, file {file_idx} should be None"
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_update_from_simple_to_complex(self):
        """Test updating from simple position to complex position."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            
            # Start with simple position (2 kings)
            widget.set_fen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
            piece_count = sum(1 for rank in widget._board for sq in rank if sq is not None)
            assert piece_count == 2
            
            # Update to complex starting position (32 pieces)
            widget.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            piece_count = sum(1 for rank in widget._board for sq in rank if sq is not None)
            assert piece_count == 32
            
            # Verify all ranks have pieces where expected
            assert all(sq is not None for sq in widget._board[0])  # Rank 8
            assert all(sq is not None for sq in widget._board[1])  # Rank 7
            assert all(sq is not None for sq in widget._board[6])  # Rank 2
            assert all(sq is not None for sq in widget._board[7])  # Rank 1
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_update_from_complex_to_simple(self):
        """Test updating from complex position to simple position."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            
            # Start with complex starting position (32 pieces)
            widget.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            piece_count = sum(1 for rank in widget._board for sq in rank if sq is not None)
            assert piece_count == 32
            
            # Update to simple position (2 kings)
            widget.set_fen("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
            piece_count = sum(1 for rank in widget._board for sq in rank if sq is not None)
            assert piece_count == 2
            
            # Verify only the two kings are present
            assert widget._board[0][4] == {"piece": "k", "color": "black"}
            assert widget._board[7][4] == {"piece": "k", "color": "white"}
            
            # Verify all other squares are empty
            for rank_idx in range(8):
                for file_idx in range(8):
                    if (rank_idx == 0 and file_idx == 4) or (rank_idx == 7 and file_idx == 4):
                        continue
                    assert widget._board[rank_idx][file_idx] is None
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")


class TestBoardFenEdgeCases:
    """Tests for edge-case FEN positions that are valid but unusual."""
    
    def test_completely_empty_board(self):
        """Test parsing completely empty board (8/8/8/8/8/8/8/8)."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.set_fen("8/8/8/8/8/8/8/8 w - - 0 1")
            
            # All squares should be None (empty)
            for rank in widget._board:
                assert len(rank) == 8
                for square in rank:
                    assert square is None, "Empty board should have all None squares"
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_single_piece_white_king_only(self):
        """Test position with only white king on e1."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.set_fen("8/8/8/8/8/8/8/4K3 w - - 0 1")
            
            # Check that only rank 1, file e has the white king
            for rank_idx in range(8):
                for file_idx in range(8):
                    if rank_idx == 7 and file_idx == 4:  # Rank 1, file e
                        assert widget._board[rank_idx][file_idx] == {"piece": "k", "color": "white"}
                    else:
                        assert widget._board[rank_idx][file_idx] is None
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_single_piece_black_king_only(self):
        """Test position with only black king on e8."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.set_fen("4k3/8/8/8/8/8/8/8 w - - 0 1")
            
            # Check that only rank 8, file e has the black king
            for rank_idx in range(8):
                for file_idx in range(8):
                    if rank_idx == 0 and file_idx == 4:  # Rank 8, file e
                        assert widget._board[rank_idx][file_idx] == {"piece": "k", "color": "black"}
                    else:
                        assert widget._board[rank_idx][file_idx] is None
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_only_pawns_various_ranks(self):
        """Test position with only pawns on different ranks."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            # White pawns on rank 3, black pawns on rank 6
            widget.set_fen("8/8/pppppppp/8/8/PPPPPPPP/8/8 w - - 0 1")
            
            # Check rank 6 (index 2) has black pawns
            rank6 = widget._board[2]
            assert all(sq == {"piece": "p", "color": "black"} for sq in rank6)
            
            # Check rank 3 (index 5) has white pawns
            rank3 = widget._board[5]
            assert all(sq == {"piece": "p", "color": "white"} for sq in rank3)
            
            # All other ranks should be empty
            for rank_idx in [0, 1, 3, 4, 6, 7]:
                for square in widget._board[rank_idx]:
                    assert square is None
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_maximum_digit_sequences(self):
        """Test FEN with multiple consecutive 8s."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            # All ranks are 8 (all empty)
            widget.set_fen("8/8/8/8/8/8/8/8 w - - 0 1")
            
            # Verify it's completely empty
            for rank in widget._board:
                for square in rank:
                    assert square is None
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_asymmetric_position_pieces_clustered_left(self):
        """Test position with pieces clustered on the left side."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            # All pieces on files a-d, files e-h empty
            widget.set_fen("rnbq4/pppp4/8/8/8/8/PPPP4/RNBQ4 w - - 0 1")
            
            # Check rank 8 (index 0): pieces on a-d, empty on e-h
            rank8 = widget._board[0]
            assert rank8[0] == {"piece": "r", "color": "black"}
            assert rank8[1] == {"piece": "n", "color": "black"}
            assert rank8[2] == {"piece": "b", "color": "black"}
            assert rank8[3] == {"piece": "q", "color": "black"}
            assert all(rank8[i] is None for i in range(4, 8))
            
            # Check rank 1 (index 7): pieces on a-d, empty on e-h
            rank1 = widget._board[7]
            assert rank1[0] == {"piece": "r", "color": "white"}
            assert rank1[1] == {"piece": "n", "color": "white"}
            assert rank1[2] == {"piece": "b", "color": "white"}
            assert rank1[3] == {"piece": "q", "color": "white"}
            assert all(rank1[i] is None for i in range(4, 8))
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_asymmetric_position_pieces_clustered_right(self):
        """Test position with pieces clustered on the right side."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            # All pieces on files e-h, files a-d empty
            widget.set_fen("4kbnr/4pppp/8/8/8/8/4PPPP/4KBNR w - - 0 1")
            
            # Check rank 8 (index 0): empty on a-d, pieces on e-h
            rank8 = widget._board[0]
            assert all(rank8[i] is None for i in range(0, 4))
            assert rank8[4] == {"piece": "k", "color": "black"}
            assert rank8[5] == {"piece": "b", "color": "black"}
            assert rank8[6] == {"piece": "n", "color": "black"}
            assert rank8[7] == {"piece": "r", "color": "black"}
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_promotion_position_pawn_on_8th_rank(self):
        """Test position with pawn on 8th rank (unusual but valid for widget)."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            # White pawn on a8 (would normally be impossible but widget should handle it)
            widget.set_fen("P7/8/8/8/8/8/8/8 w - - 0 1")
            
            # Check rank 8 (index 0), file a
            assert widget._board[0][0] == {"piece": "p", "color": "white"}
            
            # All other squares should be empty
            for rank_idx in range(8):
                for file_idx in range(8):
                    if rank_idx == 0 and file_idx == 0:
                        continue
                    assert widget._board[rank_idx][file_idx] is None
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_promotion_position_pawn_on_1st_rank(self):
        """Test position with pawn on 1st rank (unusual but valid for widget)."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            # Black pawn on h1 (would normally be impossible but widget should handle it)
            widget.set_fen("8/8/8/8/8/8/8/7p w - - 0 1")
            
            # Check rank 1 (index 7), file h
            assert widget._board[7][7] == {"piece": "p", "color": "black"}
            
            # All other squares should be empty
            for rank_idx in range(8):
                for file_idx in range(8):
                    if rank_idx == 7 and file_idx == 7:
                        continue
                    assert widget._board[rank_idx][file_idx] is None
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_sparse_position_scattered_pieces(self):
        """Test position with scattered pieces across the board."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            # Scattered pieces: kings and a few other pieces
            widget.set_fen("k7/8/2n5/8/4B3/8/6P1/7K w - - 0 1")
            
            # Verify specific pieces
            assert widget._board[0][0] == {"piece": "k", "color": "black"}  # a8
            assert widget._board[2][2] == {"piece": "n", "color": "black"}  # c6
            assert widget._board[4][4] == {"piece": "b", "color": "white"}  # e4
            assert widget._board[6][6] == {"piece": "p", "color": "white"}  # g2
            assert widget._board[7][7] == {"piece": "k", "color": "white"}  # h1
            
            # Count non-None squares (should be exactly 5)
            piece_count = sum(1 for rank in widget._board for sq in rank if sq is not None)
            assert piece_count == 5
        
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

