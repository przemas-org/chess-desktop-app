#!/usr/bin/env python3
"""
Quick test script to verify Game class methods work correctly.
"""

from chess_app.game import Game, IllegalMoveError

def test_basic_moves():
    """Test basic move application and history."""
    print("Test 1: Basic move application and history")
    game = Game()
    
    # Test get_legal_moves
    legal_moves = game.get_legal_moves()
    print(f"  Legal moves in starting position: {len(legal_moves)}")
    assert len(legal_moves) == 20, "Should have 20 legal moves in starting position"
    
    # Print first few moves as example
    print(f"  First 5 moves: {[m.san for m in legal_moves[:5]]}")
    
    # Apply a move using UCI string
    game.apply_move("e2e4")
    history = game.get_history()
    assert len(history) == 1, "History should have 1 move"
    assert history[0].uci == "e2e4", "Move UCI should be e2e4"
    assert history[0].san == "e4", "Move SAN should be e4"
    print(f"  Applied e2e4: san={history[0].san}, from={history[0].from_square}, to={history[0].to_square}")
    
    # Apply another move
    game.apply_move("e7e5")
    history = game.get_history()
    assert len(history) == 2, "History should have 2 moves"
    print(f"  Applied e7e5: History now has {len(history)} moves")
    
    print("  ✓ Test 1 passed\n")

def test_undo():
    """Test undo functionality."""
    print("Test 2: Undo functionality")
    game = Game()
    
    game.apply_move("e2e4")
    game.apply_move("e7e5")
    game.apply_move("g1f3")
    
    history = game.get_history()
    assert len(history) == 3, "Should have 3 moves"
    print(f"  After 3 moves: {[m.san for m in history]}")
    
    # Undo one move
    game.undo()
    history = game.get_history()
    assert len(history) == 2, "Should have 2 moves after undo"
    print(f"  After 1 undo: {[m.san for m in history]}")
    
    # Undo remaining moves
    game.undo()
    game.undo()
    history = game.get_history()
    assert len(history) == 0, "Should have 0 moves after undoing all"
    print(f"  After all undos: {len(history)} moves")
    
    # Test undo on empty history (should be no-op)
    game.undo()
    history = game.get_history()
    assert len(history) == 0, "Should still have 0 moves"
    print(f"  Extra undo (no-op): {len(history)} moves")
    
    print("  ✓ Test 2 passed\n")

def test_illegal_move():
    """Test illegal move detection."""
    print("Test 3: Illegal move detection")
    game = Game()
    
    try:
        game.apply_move("e2e5")  # Illegal move
        assert False, "Should have raised IllegalMoveError"
    except IllegalMoveError as e:
        print(f"  Caught expected error: {str(e)[:60]}...")
        print("  ✓ Test 3 passed\n")

def test_move_object_application():
    """Test applying Move objects."""
    print("Test 4: Applying Move objects")
    game = Game()
    
    # Get legal moves and apply one
    legal_moves = game.get_legal_moves()
    e4_move = next(m for m in legal_moves if m.uci == "e2e4")
    
    game.apply_move(e4_move)
    history = game.get_history()
    assert len(history) == 1, "Should have 1 move"
    assert history[0].uci == "e2e4", "Move should be e2e4"
    print(f"  Applied Move object: {history[0].san}")
    print("  ✓ Test 4 passed\n")

def test_promotion():
    """Test pawn promotion moves."""
    print("Test 5: Pawn promotion")
    # Position where white pawn can promote
    fen = "4k3/P7/8/8/8/8/8/4K3 w - - 0 1"
    game = Game.from_fen(fen)
    
    legal_moves = game.get_legal_moves()
    promotion_moves = [m for m in legal_moves if m.promotion is not None]
    print(f"  Found {len(promotion_moves)} promotion moves")
    
    # Apply queen promotion
    game.apply_move("a7a8q")
    history = game.get_history()
    assert history[0].promotion == "q", "Should be queen promotion"
    print(f"  Applied promotion: {history[0].san}, promotion={history[0].promotion}")
    print("  ✓ Test 5 passed\n")

def test_history_immutability():
    """Test that get_history returns immutable tuple."""
    print("Test 6: History immutability")
    game = Game()
    game.apply_move("e2e4")
    
    history = game.get_history()
    assert isinstance(history, tuple), "History should be a tuple"
    
    # Verify we can't modify it
    try:
        history[0] = None
        assert False, "Should not be able to modify tuple"
    except TypeError:
        print("  Cannot modify history tuple (as expected)")
        print("  ✓ Test 6 passed\n")

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Game class methods")
    print("=" * 60 + "\n")
    
    test_basic_moves()
    test_undo()
    test_illegal_move()
    test_move_object_application()
    test_promotion()
    test_history_immutability()
    
    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)
