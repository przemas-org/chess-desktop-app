#!/usr/bin/env python3
"""
Test script for Game class status and metadata access methods.
"""

from chess_app.game import Game, GameStatus, Side


def test_status_ongoing():
    """Test status detection for ongoing games."""
    print("Test 1: Ongoing game status")
    game = Game()
    
    status = game.get_status()
    assert status == GameStatus.ONGOING, f"Expected ONGOING, got {status}"
    print(f"  Starting position: {status.value}")
    
    # Make a few moves
    game.apply_move("e2e4")
    status = game.get_status()
    assert status == GameStatus.ONGOING, f"Expected ONGOING, got {status}"
    print(f"  After e4: {status.value}")
    
    print("  ✓ Test 1 passed\n")


def test_status_check():
    """Test status detection for check."""
    print("Test 2: Check status")
    # Position where black king is in check from white rook
    fen = "4k3/8/8/8/8/8/8/4R1K1 b - - 0 1"
    game = Game.from_fen(fen)
    
    status = game.get_status()
    assert status == GameStatus.CHECK, f"Expected CHECK, got {status}"
    print(f"  Black king in check from rook: {status.value}")
    print("  ✓ Test 2 passed\n")


def test_status_checkmate():
    """Test status detection for checkmate."""
    print("Test 3: Checkmate status")
    # Fool's mate position
    game = Game()
    game.apply_move("f2f3")
    game.apply_move("e7e6")
    game.apply_move("g2g4")
    game.apply_move("d8h4")
    
    status = game.get_status()
    assert status == GameStatus.CHECKMATE, f"Expected CHECKMATE, got {status}"
    print(f"  Fool's mate: {status.value}")
    print("  ✓ Test 3 passed\n")


def test_status_stalemate():
    """Test status detection for stalemate."""
    print("Test 4: Stalemate status")
    # Stalemate position: king and queen vs king
    fen = "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"
    game = Game.from_fen(fen)
    
    status = game.get_status()
    assert status == GameStatus.STALEMATE, f"Expected STALEMATE, got {status}"
    print(f"  Stalemate position: {status.value}")
    print("  ✓ Test 4 passed\n")


def test_status_insufficient_material():
    """Test status detection for insufficient material."""
    print("Test 5: Insufficient material status")
    # King vs king
    fen = "4k3/8/8/8/8/8/8/4K3 w - - 0 1"
    game = Game.from_fen(fen)
    
    status = game.get_status()
    assert status == GameStatus.DRAW_INSUFFICIENT_MATERIAL, \
        f"Expected DRAW_INSUFFICIENT_MATERIAL, got {status}"
    print(f"  King vs king: {status.value}")
    print("  ✓ Test 5 passed\n")


def test_status_fifty_move():
    """Test status detection for fifty-move rule."""
    print("Test 6: Fifty-move rule status")
    # Position with sufficient material but halfmove clock at 100 (fifty full moves)
    # King and queen vs king and rook - sufficient material but fifty-move rule triggered
    fen = "4k2r/8/8/8/8/8/8/4K2Q w - - 100 75"
    game = Game.from_fen(fen)
    
    status = game.get_status()
    assert status == GameStatus.DRAW_50_MOVE, \
        f"Expected DRAW_50_MOVE, got {status}"
    print(f"  Fifty-move rule triggered: {status.value}")
    print("  ✓ Test 6 passed\n")


def test_side_to_move():
    """Test side to move detection."""
    print("Test 7: Side to move")
    game = Game()
    
    side = game.get_side_to_move()
    assert side == Side.WHITE, f"Expected WHITE, got {side}"
    print(f"  Starting position: {side.value}")
    
    game.apply_move("e2e4")
    side = game.get_side_to_move()
    assert side == Side.BLACK, f"Expected BLACK, got {side}"
    print(f"  After White's move: {side.value}")
    
    game.apply_move("e7e5")
    side = game.get_side_to_move()
    assert side == Side.WHITE, f"Expected WHITE, got {side}"
    print(f"  After Black's move: {side.value}")
    
    print("  ✓ Test 7 passed\n")


def test_fullmove_number():
    """Test full-move number tracking."""
    print("Test 8: Full-move number")
    game = Game()
    
    fullmove = game.get_fullmove_number()
    assert fullmove == 1, f"Expected 1, got {fullmove}"
    print(f"  Starting position: move {fullmove}")
    
    game.apply_move("e2e4")
    fullmove = game.get_fullmove_number()
    assert fullmove == 1, f"Expected 1, got {fullmove}"
    print(f"  After White's first move: move {fullmove}")
    
    game.apply_move("e7e5")
    fullmove = game.get_fullmove_number()
    assert fullmove == 2, f"Expected 2, got {fullmove}"
    print(f"  After Black's first move: move {fullmove}")
    
    game.apply_move("g1f3")
    fullmove = game.get_fullmove_number()
    assert fullmove == 2, f"Expected 2, got {fullmove}"
    print(f"  After White's second move: move {fullmove}")
    
    game.apply_move("b8c6")
    fullmove = game.get_fullmove_number()
    assert fullmove == 3, f"Expected 3, got {fullmove}"
    print(f"  After Black's second move: move {fullmove}")
    
    print("  ✓ Test 8 passed\n")


def test_halfmove_clock():
    """Test half-move clock tracking."""
    print("Test 9: Half-move clock")
    game = Game()
    
    halfmove = game.get_halfmove_clock()
    assert halfmove == 0, f"Expected 0, got {halfmove}"
    print(f"  Starting position: halfmove clock = {halfmove}")
    
    # Knight move (no pawn move or capture)
    game.apply_move("g1f3")
    halfmove = game.get_halfmove_clock()
    assert halfmove == 1, f"Expected 1, got {halfmove}"
    print(f"  After Nf3: halfmove clock = {halfmove}")
    
    # Another knight move
    game.apply_move("g8f6")
    halfmove = game.get_halfmove_clock()
    assert halfmove == 2, f"Expected 2, got {halfmove}"
    print(f"  After Nf6: halfmove clock = {halfmove}")
    
    # Pawn move (resets counter)
    game.apply_move("e2e4")
    halfmove = game.get_halfmove_clock()
    assert halfmove == 0, f"Expected 0, got {halfmove}"
    print(f"  After e4 (pawn move): halfmove clock = {halfmove}")
    
    # Another pawn move
    game.apply_move("d7d5")
    halfmove = game.get_halfmove_clock()
    assert halfmove == 0, f"Expected 0, got {halfmove}"
    print(f"  After d5 (pawn move): halfmove clock = {halfmove}")
    
    # Capture (resets counter)
    game.apply_move("e4d5")
    halfmove = game.get_halfmove_clock()
    assert halfmove == 0, f"Expected 0, got {halfmove}"
    print(f"  After exd5 (capture): halfmove clock = {halfmove}")
    
    print("  ✓ Test 9 passed\n")


def test_metadata_from_fen():
    """Test metadata extraction from FEN position."""
    print("Test 10: Metadata from FEN")
    
    # FEN with specific metadata: Black to move, move 15, halfmove 7
    fen = "rnbqkb1r/pppp1ppp/5n2/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 7 15"
    game = Game.from_fen(fen)
    
    side = game.get_side_to_move()
    assert side == Side.BLACK, f"Expected BLACK, got {side}"
    print(f"  Side to move: {side.value}")
    
    fullmove = game.get_fullmove_number()
    assert fullmove == 15, f"Expected 15, got {fullmove}"
    print(f"  Full-move number: {fullmove}")
    
    halfmove = game.get_halfmove_clock()
    assert halfmove == 7, f"Expected 7, got {halfmove}"
    print(f"  Half-move clock: {halfmove}")
    
    print("  ✓ Test 10 passed\n")


def test_methods_are_readonly():
    """Test that status and metadata methods don't mutate state."""
    print("Test 11: Methods are read-only")
    game = Game()
    game.apply_move("e2e4")
    
    # Get initial state
    initial_fen = game._board.fen()
    
    # Call all the new methods multiple times
    for _ in range(3):
        game.get_status()
        game.get_side_to_move()
        game.get_fullmove_number()
        game.get_halfmove_clock()
    
    # Verify state hasn't changed
    final_fen = game._board.fen()
    assert initial_fen == final_fen, "Methods should not mutate state"
    print("  All methods called 3x each, state unchanged")
    print("  ✓ Test 11 passed\n")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Game class status and metadata methods")
    print("=" * 60 + "\n")
    
    test_status_ongoing()
    test_status_check()
    test_status_checkmate()
    test_status_stalemate()
    test_status_insufficient_material()
    test_status_fifty_move()
    test_side_to_move()
    test_fullmove_number()
    test_halfmove_clock()
    test_metadata_from_fen()
    test_methods_are_readonly()
    
    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
