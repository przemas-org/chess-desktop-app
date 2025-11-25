#!/usr/bin/env python3
"""
Comprehensive I/O test suite for FEN/PGN import-export and error handling.

This module extends the test coverage with focused scenarios for:
- FEN: Initialize from FEN, apply moves, verify export matches expected positions
- FEN: Invalid input error handling with meaningful messages
- PGN: Round-trip testing (export → import → verify)
- PGN: Malformed/incompatible PGN error handling
- PGN: Result header consistency with board state
- All tests are deterministic without external engines or tablebases
"""

import pytest
from chess_app.game import Game, GameStatus, InvalidFenError, InvalidPgnError, Side


class TestFenSequenceScenarios:
    """Tests that initialize from FEN, apply moves, and verify export."""
    
    def test_fen_import_apply_moves_export(self):
        """Import custom position, apply moves, verify export FEN."""
        # Start from a specific opening position (Sicilian Defense after 1.e4 c5)
        fen = "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
        game = Game.from_fen(fen)
        
        # Apply a sequence of moves
        game.apply_move("g1f3")  # Nf3
        game.apply_move("d7d6")  # d6
        game.apply_move("d2d4")  # d4
        
        # Export and verify expected position
        exported_fen = game.export_fen()
        # Note: python-chess only sets en passant square if capture is actually possible
        expected_fen = "rnbqkbnr/pp2pppp/3p4/2p5/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 3"
        assert exported_fen == expected_fen
    
    def test_fen_complex_position_with_castling(self):
        """Test position where castling rights change during play."""
        # Position where white can still castle, black cannot
        fen = "r3k2r/pppppppp/8/8/8/8/PPPPPPPP/R3K2R w KQkq - 0 1"
        game = Game.from_fen(fen)
        
        # White castles kingside
        game.apply_move("e1g1")
        
        exported_fen = game.export_fen()
        # After white castles, white loses castling rights but black keeps them
        assert "KQ" not in exported_fen
        assert "kq" in exported_fen
        assert "R4RK1" in exported_fen  # Verify king and rook positions after castling
    
    def test_fen_en_passant_capture_sequence(self):
        """Test en passant opportunity creation and capture."""
        # Position setup for en passant - white pawn on e5, black just moved f7-f5
        fen = "rnbqkbnr/ppppp1pp/8/3pPp2/8/8/PPPP1PPP/RNBQKBNR w KQkq f6 0 3"
        game = Game.from_fen(fen)
        
        # Capture en passant
        game.apply_move("e5f6")
        
        exported_fen = game.export_fen()
        # After en passant capture, the captured pawn is gone and capturing pawn advances
        assert "5P2" in exported_fen  # Pawn on f6
        # The d-pawn remains on d5 in the FEN
        assert exported_fen.count('p') < fen.count('p')  # Verify pawn was captured
    
    def test_fen_promotion_sequence(self):
        """Test pawn promotion from FEN position."""
        # White pawn ready to promote, black king far away
        fen = "8/P7/8/8/8/8/7k/K7 w - - 0 1"
        game = Game.from_fen(fen)
        
        # Promote to queen
        game.apply_move("a7a8q")
        
        exported_fen = game.export_fen()
        assert "Q7" in exported_fen  # Queen on a8
        assert len(game.get_history()) == 1
        assert game.get_history()[0].promotion == "q"
    
    def test_fen_halfmove_clock_progression(self):
        """Test halfmove clock increments correctly with non-pawn moves."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        game = Game.from_fen(fen)
        
        # Make non-pawn, non-capture moves
        game.apply_move("g1f3")
        game.apply_move("g8f6")
        game.apply_move("b1c3")
        
        exported_fen = game.export_fen()
        parts = exported_fen.split()
        assert parts[4] == "3"  # Halfmove clock should be 3
    
    def test_fen_halfmove_clock_resets_on_pawn_move(self):
        """Test halfmove clock resets after pawn move."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 5 1"
        game = Game.from_fen(fen)
        
        # Make a pawn move
        game.apply_move("e2e4")
        
        exported_fen = game.export_fen()
        parts = exported_fen.split()
        assert parts[4] == "0"  # Halfmove clock should reset
    
    def test_fen_fullmove_number_progression(self):
        """Test fullmove number increments after black's move."""
        fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        game = Game.from_fen(fen)
        
        assert game.get_fullmove_number() == 1
        
        game.apply_move("e2e4")
        assert game.get_fullmove_number() == 1
        
        game.apply_move("e7e5")
        assert game.get_fullmove_number() == 2


class TestFenErrorHandling:
    """Comprehensive tests for FEN error handling."""
    
    def test_invalid_fen_empty_string(self):
        """Empty string should raise InvalidFenError."""
        with pytest.raises(InvalidFenError) as exc_info:
            Game.from_fen("")
        
        assert "Invalid FEN string provided" in str(exc_info.value)
        assert "''" in str(exc_info.value)
    
    def test_invalid_fen_incomplete(self):
        """Incomplete FEN (missing fields) is accepted by python-chess (auto-completes)."""
        # python-chess auto-completes incomplete FEN strings
        incomplete_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR"
        
        # This actually succeeds with python-chess
        game = Game.from_fen(incomplete_fen)
        assert game is not None
        # Verify it was completed with defaults
        fen = game.export_fen()
        assert " w " in fen  # Default to white's turn
    
    def test_invalid_fen_wrong_piece_placement(self):
        """Invalid piece placement should raise InvalidFenError."""
        # Missing a rank in piece placement
        invalid_fen = "rnbqkbnr/pppppppp/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        
        with pytest.raises(InvalidFenError) as exc_info:
            Game.from_fen(invalid_fen)
        
        assert "Invalid FEN string provided" in str(exc_info.value)
    
    def test_invalid_fen_invalid_turn_indicator(self):
        """Invalid turn indicator should raise InvalidFenError."""
        invalid_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR x KQkq - 0 1"
        
        with pytest.raises(InvalidFenError) as exc_info:
            Game.from_fen(invalid_fen)
        
        assert "Invalid FEN string provided" in str(exc_info.value)
        assert "x" in str(exc_info.value)
    
    def test_invalid_fen_invalid_castling_rights(self):
        """Invalid castling rights format should raise InvalidFenError."""
        invalid_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w XYZ - 0 1"
        
        with pytest.raises(InvalidFenError) as exc_info:
            Game.from_fen(invalid_fen)
        
        assert "Invalid FEN string provided" in str(exc_info.value)
    
    def test_invalid_fen_nonsense_string(self):
        """Complete nonsense string should raise InvalidFenError."""
        with pytest.raises(InvalidFenError) as exc_info:
            Game.from_fen("this is not a valid fen string")
        
        error_msg = str(exc_info.value)
        assert "Invalid FEN string provided" in error_msg
        assert "this is not a valid fen string" in error_msg
    
    def test_invalid_fen_error_message_includes_details(self):
        """Error messages should include helpful details."""
        invalid_fen = "invalid_fen"
        
        with pytest.raises(InvalidFenError) as exc_info:
            Game.from_fen(invalid_fen)
        
        error_msg = str(exc_info.value)
        assert "Invalid FEN string provided" in error_msg
        assert invalid_fen in error_msg
        assert "Error details:" in error_msg


class TestPgnImport:
    """Tests for PGN import functionality."""
    
    def test_pgn_import_simple_game(self):
        """Import a simple complete game from PGN."""
        pgn = """
[Event "Test Game"]
[Site "Test"]
[Date "2024.01.01"]
[Round "1"]
[White "Player 1"]
[Black "Player 2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 1-0
"""
        game = Game.from_pgn(pgn)
        
        # Verify move history
        history = game.get_history()
        assert len(history) == 5
        assert history[0].san == "e4"
        assert history[1].san == "e5"
        assert history[2].san == "Nf3"
        assert history[3].san == "Nc6"
        assert history[4].san == "Bb5"
    
    def test_pgn_import_with_minimal_headers(self):
        """Import PGN with minimal headers."""
        pgn = """
1. d4 d5 2. c4 e6
"""
        game = Game.from_pgn(pgn)
        
        history = game.get_history()
        assert len(history) == 4
        assert history[0].san == "d4"
        assert history[3].san == "e6"
    
    def test_pgn_import_preserves_final_position(self):
        """Imported PGN should result in correct final position."""
        pgn = """
[Event "Scholar's Mate"]
[Result "1-0"]

1. e4 e5 2. Bc4 Nc6 3. Qh5 Nf6 4. Qxf7# 1-0
"""
        game = Game.from_pgn(pgn)
        
        # Verify checkmate
        assert game.get_status() == GameStatus.CHECKMATE
        assert game.get_side_to_move() == Side.BLACK
        
        # Verify position has queen on f7
        fen = game.export_fen()
        assert "Q" in fen  # White queen exists
    
    def test_pgn_import_move_history_matches_moves(self):
        """Move history from PGN should match all moves."""
        pgn = """
1. e4 c5 2. Nf3 d6 3. d4 cxd4 4. Nxd4 Nf6 5. Nc3 a6
"""
        game = Game.from_pgn(pgn)
        
        history = game.get_history()
        assert len(history) == 10
        
        # Verify specific moves
        assert history[0].uci == "e2e4"
        assert history[1].uci == "c7c5"
        assert history[4].uci == "d2d4"
        assert history[5].uci == "c5d4"  # Capture
    
    def test_pgn_import_with_promotion(self):
        """Import PGN with pawn promotion."""
        # Very simple endgame with clear promotion
        pgn = """
[Result "*"]

1. a4 h5 2. a5 h4 3. a6 h3 4. axb7 hxg2 5. bxa8=Q gxh1=Q *
"""
        game = Game.from_pgn(pgn)
        
        history = game.get_history()
        # Check that we have promotion moves
        assert len(history) == 10
        
        # Second-to-last move should be white's promotion
        white_promotion = history[-2]
        assert white_promotion.promotion == "q"
        assert "a8" in white_promotion.uci
        
        # Last move should be black's promotion
        black_promotion = history[-1]
        assert black_promotion.promotion == "q"
        assert "h1" in black_promotion.uci
    
    def test_pgn_import_result_header_preserved(self):
        """PGN import should preserve the Result header for re-export."""
        pgn = """
[Event "Test"]
[Result "1/2-1/2"]

1. e4 e5 2. Nf3 Nc6 1/2-1/2
"""
        game = Game.from_pgn(pgn)
        
        # The result should be stored internally
        assert game._result == "1/2-1/2"
        
        # Export and check result is preserved
        exported_pgn = game.export_pgn()
        assert "[Result \"1/2-1/2\"]" in exported_pgn


class TestPgnExport:
    """Tests for PGN export functionality."""
    
    def test_pgn_export_simple_game(self):
        """Export a simple game to PGN."""
        game = Game()
        game.apply_move("e2e4")
        game.apply_move("e7e5")
        game.apply_move("g1f3")
        
        pgn = game.export_pgn()
        
        # Verify PGN structure
        assert "[Event " in pgn
        assert "[Result " in pgn
        assert "1. e4 e5" in pgn
        assert "2. Nf3" in pgn
    
    def test_pgn_export_with_custom_headers(self):
        """Export PGN with custom headers."""
        game = Game()
        game.apply_move("d2d4")
        game.apply_move("d7d5")
        
        headers = {
            "Event": "World Championship",
            "Site": "London",
            "Date": "2024.01.15",
            "White": "Alice",
            "Black": "Bob",
        }
        
        pgn = game.export_pgn(headers)
        
        assert "[Event \"World Championship\"]" in pgn
        assert "[Site \"London\"]" in pgn
        assert "[Date \"2024.01.15\"]" in pgn
        assert "[White \"Alice\"]" in pgn
        assert "[Black \"Bob\"]" in pgn
    
    def test_pgn_export_ongoing_game_result(self):
        """Ongoing game should have Result '*'."""
        game = Game()
        game.apply_move("e2e4")
        
        pgn = game.export_pgn()
        
        assert "[Result \"*\"]" in pgn
    
    def test_pgn_export_checkmate_result_white_wins(self):
        """Checkmate should result in correct winner (1-0)."""
        game = Game()
        # Scholar's mate
        game.apply_move("e2e4")
        game.apply_move("e7e5")
        game.apply_move("f1c4")
        game.apply_move("b8c6")
        game.apply_move("d1h5")
        game.apply_move("g8f6")
        game.apply_move("h5f7")  # Checkmate
        
        pgn = game.export_pgn()
        
        assert game.get_status() == GameStatus.CHECKMATE
        assert "[Result \"1-0\"]" in pgn
    
    def test_pgn_export_checkmate_result_black_wins(self):
        """Checkmate by Black should result in 0-1."""
        game = Game()
        # Fool's mate
        game.apply_move("f2f3")
        game.apply_move("e7e6")
        game.apply_move("g2g4")
        game.apply_move("d8h4")  # Checkmate
        
        pgn = game.export_pgn()
        
        assert game.get_status() == GameStatus.CHECKMATE
        assert "[Result \"0-1\"]" in pgn
    
    def test_pgn_export_stalemate_result(self):
        """Stalemate should result in 1/2-1/2."""
        # Create stalemate position
        fen = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
        game = Game.from_fen(fen)
        
        pgn = game.export_pgn()
        
        assert game.get_status() == GameStatus.STALEMATE
        assert "[Result \"1/2-1/2\"]" in pgn
    
    def test_pgn_export_move_notation(self):
        """Verify PGN move notation is correct."""
        game = Game()
        game.apply_move("e2e4")
        game.apply_move("c7c5")
        game.apply_move("g1f3")
        game.apply_move("d7d6")
        game.apply_move("d2d4")
        game.apply_move("c5d4")
        game.apply_move("f3d4")
        
        pgn = game.export_pgn()
        
        # Check move formatting
        assert "1. e4 c5" in pgn
        assert "2. Nf3 d6" in pgn
        assert "3. d4 cxd4" in pgn
        assert "4. Nxd4" in pgn


class TestPgnRoundTrip:
    """Tests for PGN export → import → verify scenarios."""
    
    def test_pgn_roundtrip_basic(self):
        """Basic round-trip: game → PGN → game."""
        game1 = Game()
        game1.apply_move("e2e4")
        game1.apply_move("e7e5")
        game1.apply_move("g1f3")
        game1.apply_move("b8c6")
        
        # Export to PGN
        pgn = game1.export_pgn()
        
        # Import from PGN
        game2 = Game.from_pgn(pgn)
        
        # Verify positions match
        assert game1.export_fen() == game2.export_fen()
    
    def test_pgn_roundtrip_preserves_move_history(self):
        """Round-trip should preserve move history."""
        game1 = Game()
        moves = ["d2d4", "d7d5", "c2c4", "e7e6", "b1c3", "g8f6"]
        
        for move in moves:
            game1.apply_move(move)
        
        # Round-trip
        pgn = game1.export_pgn()
        game2 = Game.from_pgn(pgn)
        
        # Compare move histories
        history1 = game1.get_history()
        history2 = game2.get_history()
        
        assert len(history1) == len(history2)
        for m1, m2 in zip(history1, history2):
            assert m1.uci == m2.uci
            assert m1.san == m2.san
    
    def test_pgn_roundtrip_preserves_game_state(self):
        """Round-trip should preserve all game state."""
        game1 = Game()
        game1.apply_move("e2e4")
        game1.apply_move("c7c5")
        game1.apply_move("g1f3")
        
        pgn = game1.export_pgn()
        game2 = Game.from_pgn(pgn)
        
        # Check all state is preserved
        assert game1.get_side_to_move() == game2.get_side_to_move()
        assert game1.get_status() == game2.get_status()
        assert game1.get_fullmove_number() == game2.get_fullmove_number()
        assert game1.get_halfmove_clock() == game2.get_halfmove_clock()
    
    def test_pgn_roundtrip_with_captures(self):
        """Round-trip with capture moves."""
        game1 = Game()
        game1.apply_move("e2e4")
        game1.apply_move("d7d5")
        game1.apply_move("e4d5")  # Capture
        game1.apply_move("d8d5")  # Recapture
        
        pgn = game1.export_pgn()
        game2 = Game.from_pgn(pgn)
        
        assert game1.export_fen() == game2.export_fen()
        assert len(game2.get_history()) == 4
    
    def test_pgn_roundtrip_with_castling(self):
        """Round-trip with castling moves."""
        game1 = Game()
        game1.apply_move("e2e4")
        game1.apply_move("e7e5")
        game1.apply_move("g1f3")
        game1.apply_move("b8c6")
        game1.apply_move("f1c4")
        game1.apply_move("g8f6")
        game1.apply_move("e1g1")  # Castle kingside
        
        pgn = game1.export_pgn()
        game2 = Game.from_pgn(pgn)
        
        assert game1.export_fen() == game2.export_fen()
        # Verify castling was recorded
        history = game2.get_history()
        assert "O-O" in [m.san for m in history]
    
    def test_pgn_roundtrip_complex_game(self):
        """Round-trip with a complex game sequence."""
        game1 = Game()
        
        # Play a longer sequence
        moves = [
            "e2e4", "c7c5", "g1f3", "d7d6", "d2d4", "c5d4",
            "f3d4", "g8f6", "b1c3", "a7a6", "f1e2", "e7e5",
            "d4b3", "f8e7", "e1g1", "e8g8"
        ]
        
        for move in moves:
            game1.apply_move(move)
        
        pgn = game1.export_pgn()
        game2 = Game.from_pgn(pgn)
        
        assert game1.export_fen() == game2.export_fen()
        assert len(game2.get_history()) == len(moves)
    
    def test_pgn_roundtrip_multiple_times(self):
        """Multiple round-trips should preserve state."""
        game1 = Game()
        game1.apply_move("d2d4")
        game1.apply_move("g8f6")
        
        # First round-trip
        pgn1 = game1.export_pgn()
        game2 = Game.from_pgn(pgn1)
        
        # Second round-trip
        pgn2 = game2.export_pgn()
        game3 = Game.from_pgn(pgn2)
        
        # All should match
        assert game1.export_fen() == game2.export_fen() == game3.export_fen()


class TestPgnErrorHandling:
    """Tests for PGN error handling with invalid inputs."""
    
    def test_pgn_empty_string(self):
        """Empty PGN string should raise InvalidPgnError."""
        with pytest.raises(InvalidPgnError) as exc_info:
            Game.from_pgn("")
        
        error_msg = str(exc_info.value)
        assert "Failed to parse PGN" in error_msg
        assert "no valid game found" in error_msg
    
    def test_pgn_invalid_whitespace_only(self):
        """Whitespace-only PGN should raise InvalidPgnError."""
        with pytest.raises(InvalidPgnError) as exc_info:
            Game.from_pgn("   \n\n  \t  ")
        
        assert "Failed to parse PGN" in str(exc_info.value)
    
    def test_pgn_malformed_headers(self):
        """Malformed headers should be handled gracefully."""
        # PGN with malformed header but valid moves
        pgn = """
[Event "Test"
[Incomplete Header

1. e4 e5
"""
        # This might parse or fail depending on python-chess behavior
        # We test that it either succeeds or raises InvalidPgnError
        try:
            game = Game.from_pgn(pgn)
            # If it succeeds, verify it at least got the moves
            assert len(game.get_history()) > 0
        except InvalidPgnError:
            # If it fails, that's also acceptable
            pass
    
    def test_pgn_invalid_move_notation(self):
        """Invalid move notation is handled by python-chess (logs error, returns partial game)."""
        pgn = """
[Event "Test"]

1. e4 e5 2. Qx9 
"""
        # python-chess logs the error but still returns a game with valid moves
        game = Game.from_pgn(pgn)
        # Should have parsed the valid moves before the error
        assert len(game.get_history()) >= 2
    
    def test_pgn_illegal_move_sequence(self):
        """Illegal move sequence is handled by python-chess (logs error, returns partial game)."""
        pgn = """
[Event "Test"]

1. e4 e5 2. Nc6
"""
        # python-chess logs the error but still returns a game with valid moves
        game = Game.from_pgn(pgn)
        # Should have parsed the valid moves before the error
        assert len(game.get_history()) >= 2
    
    def test_pgn_nonsense_string(self):
        """Complete nonsense string returns game with no moves in python-chess."""
        # python-chess is very lenient - it parses even nonsense as an empty game
        game = Game.from_pgn("this is not valid PGN at all!")
        # Should have empty move history
        assert len(game.get_history()) == 0
    
    def test_pgn_error_message_quality(self):
        """Error messages should be meaningful for truly invalid PGN."""
        invalid_pgn = ""  # Empty string definitely fails
        
        with pytest.raises(InvalidPgnError) as exc_info:
            Game.from_pgn(invalid_pgn)
        
        error_msg = str(exc_info.value)
        assert "Failed to parse PGN" in error_msg
        assert "no valid game found" in error_msg


class TestResultHeaderConsistency:
    """Tests for Result header consistency with board state."""
    
    def test_result_checkmate_white_wins(self):
        """Checkmate by White should have Result 1-0."""
        game = Game()
        # Scholar's mate
        game.apply_move("e2e4")
        game.apply_move("e7e5")
        game.apply_move("f1c4")
        game.apply_move("b8c6")
        game.apply_move("d1h5")
        game.apply_move("g8f6")
        game.apply_move("h5f7")  # Checkmate
        
        pgn = game.export_pgn()
        assert game.get_status() == GameStatus.CHECKMATE
        assert "[Result \"1-0\"]" in pgn
    
    def test_result_checkmate_black_wins(self):
        """Checkmate by Black should have Result 0-1."""
        game = Game()
        # Fool's mate
        game.apply_move("f2f3")
        game.apply_move("e7e6")
        game.apply_move("g2g4")
        game.apply_move("d8h4")  # Checkmate
        
        pgn = game.export_pgn()
        assert game.get_status() == GameStatus.CHECKMATE
        assert "[Result \"0-1\"]" in pgn
    
    def test_result_stalemate(self):
        """Stalemate should have Result 1/2-1/2."""
        fen = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
        game = Game.from_fen(fen)
        
        pgn = game.export_pgn()
        assert game.get_status() == GameStatus.STALEMATE
        assert "[Result \"1/2-1/2\"]" in pgn
    
    def test_result_draw_insufficient_material(self):
        """Draw by insufficient material should have Result 1/2-1/2."""
        # King vs king
        fen = "8/8/8/4k3/8/8/4K3/8 w - - 0 1"
        game = Game.from_fen(fen)
        
        pgn = game.export_pgn()
        assert game.get_status() == GameStatus.DRAW_INSUFFICIENT_MATERIAL
        assert "[Result \"1/2-1/2\"]" in pgn
    
    def test_result_ongoing_game(self):
        """Ongoing game should have Result *."""
        game = Game()
        game.apply_move("e2e4")
        game.apply_move("e7e5")
        
        pgn = game.export_pgn()
        assert game.get_status() in [GameStatus.ONGOING, GameStatus.CHECK]
        assert "[Result \"*\"]" in pgn
    
    def test_result_consistency_after_undo(self):
        """Result should update correctly after undo."""
        game = Game()
        # Create checkmate
        game.apply_move("f2f3")
        game.apply_move("e7e6")
        game.apply_move("g2g4")
        game.apply_move("d8h4")  # Checkmate
        
        pgn1 = game.export_pgn()
        assert "[Result \"0-1\"]" in pgn1
        
        # Undo checkmate
        game.undo()
        pgn2 = game.export_pgn()
        assert "[Result \"*\"]" in pgn2
    
    def test_result_preserved_from_imported_pgn(self):
        """Result from imported PGN should be used in export."""
        pgn_in = """
[Event "Test"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 1-0
"""
        game = Game.from_pgn(pgn_in)
        pgn_out = game.export_pgn()
        
        # Result should be preserved even though game is not actually checkmate
        assert "[Result \"1-0\"]" in pgn_out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
