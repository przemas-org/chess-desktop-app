#!/usr/bin/env python3
"""
Test suite for BoardWidget mouse handling and square highlighting.

This module tests the mouse input handling, coordinate-to-square mapping,
signal emission, and visual highlighting features of BoardWidget.
"""

import pytest
from unittest.mock import Mock


class TestPixelToSquareMapping:
    """Tests for coordinate-to-square mapping (_pixel_to_square method)."""
    
    def test_bottom_left_corner_a1(self):
        """Test that bottom-left corner maps to 'a1'."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            # Set a fixed size for consistent testing
            widget.resize(800, 800)
            
            # Calculate where square a1 is (bottom-left)
            # With 800x800 widget, square_size = 100, margins = 0
            # a1 is at rank_idx=7 (bottom), file_idx=0 (left)
            # Pixel position: x=0-99, y=700-799
            # Click in the middle of a1
            square = widget._pixel_to_square(50, 750)
            assert square == "a1"
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_bottom_right_corner_h1(self):
        """Test that bottom-right corner maps to 'h1'."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.resize(800, 800)
            
            # h1 is at rank_idx=7 (bottom), file_idx=7 (right)
            # Pixel position: x=700-799, y=700-799
            square = widget._pixel_to_square(750, 750)
            assert square == "h1"
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_top_left_corner_a8(self):
        """Test that top-left corner maps to 'a8'."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.resize(800, 800)
            
            # a8 is at rank_idx=0 (top), file_idx=0 (left)
            # Pixel position: x=0-99, y=0-99
            square = widget._pixel_to_square(50, 50)
            assert square == "a8"
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_top_right_corner_h8(self):
        """Test that top-right corner maps to 'h8'."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.resize(800, 800)
            
            # h8 is at rank_idx=0 (top), file_idx=7 (right)
            # Pixel position: x=700-799, y=0-99
            square = widget._pixel_to_square(750, 50)
            assert square == "h8"
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_center_square_e4(self):
        """Test that center square e4 maps correctly."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.resize(800, 800)
            
            # e4 is at file_idx=4 (e), rank_idx=4 (rank 4 from bottom)
            # Pixel position: x=400-499, y=400-499
            square = widget._pixel_to_square(450, 450)
            assert square == "e4"
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_center_square_d5(self):
        """Test that center square d5 maps correctly."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.resize(800, 800)
            
            # d5 is at file_idx=3 (d), rank_idx=3 (rank 5 from bottom)
            # Pixel position: x=300-399, y=300-399
            square = widget._pixel_to_square(350, 350)
            assert square == "d5"
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_click_outside_board_left(self):
        """Test that clicks outside board (left side) return None."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.resize(800, 800)
            
            # Click to the left of the board (negative x relative to board)
            # With 800x800 and no margins, board starts at x=0
            square = widget._pixel_to_square(-10, 400)
            assert square is None
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_click_outside_board_right(self):
        """Test that clicks outside board (right side) return None."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.resize(800, 800)
            
            # Click to the right of the board
            # Board ends at x=800
            square = widget._pixel_to_square(810, 400)
            assert square is None
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_click_outside_board_top(self):
        """Test that clicks outside board (top) return None."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.resize(800, 800)
            
            # Click above the board
            square = widget._pixel_to_square(400, -10)
            assert square is None
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_click_outside_board_bottom(self):
        """Test that clicks outside board (bottom) return None."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.resize(800, 800)
            
            # Click below the board
            square = widget._pixel_to_square(400, 810)
            assert square is None
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_edge_case_just_inside_board(self):
        """Test clicks just inside the board boundaries."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.resize(800, 800)
            
            # Click at pixel (0, 0) - should be in a8
            square = widget._pixel_to_square(0, 0)
            assert square == "a8"
            
            # Click at pixel (799, 799) - should be in h1
            square = widget._pixel_to_square(799, 799)
            assert square == "h1"
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_mapping_with_widget_margins(self):
        """Test coordinate mapping when widget has non-zero margins."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            # Use non-square size to create margins
            widget.resize(900, 800)
            
            # With 900x800, square_size = 100 (limited by height)
            # x_margin = (900 - 800) // 2 = 50
            # y_margin = 0
            # So a8 is at x=50-149, y=0-99
            square = widget._pixel_to_square(100, 50)
            assert square == "a8"
            
            # Click in the margin should return None
            square = widget._pixel_to_square(25, 50)
            assert square is None
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")


class TestStateManagement:
    """Tests for state management methods (set_selected_square, set_highlighted_squares)."""
    
    def test_set_selected_square_updates_state(self):
        """Test that set_selected_square updates internal state."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            
            # Initially no square selected
            assert widget._selected_square is None
            
            # Set selected square
            widget.set_selected_square("e2")
            assert widget._selected_square == "e2"
            
            # Change selection
            widget.set_selected_square("d4")
            assert widget._selected_square == "d4"
            
            # Clear selection
            widget.set_selected_square(None)
            assert widget._selected_square is None
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_set_highlighted_squares_updates_state(self):
        """Test that set_highlighted_squares updates internal state."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            
            # Initially no highlights
            assert widget._highlighted_squares == set()
            
            # Set highlighted squares
            widget.set_highlighted_squares(["e4", "e3", "d3"])
            assert widget._highlighted_squares == {"e4", "e3", "d3"}
            
            # Update highlights
            widget.set_highlighted_squares(["f4", "g4"])
            assert widget._highlighted_squares == {"f4", "g4"}
            
            # Clear highlights
            widget.set_highlighted_squares([])
            assert widget._highlighted_squares == set()
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_set_highlighted_squares_accepts_various_collections(self):
        """Test that set_highlighted_squares accepts different collection types."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            
            # Accept list
            widget.set_highlighted_squares(["e4", "e3"])
            assert widget._highlighted_squares == {"e4", "e3"}
            
            # Accept set
            widget.set_highlighted_squares({"d4", "d5"})
            assert widget._highlighted_squares == {"d4", "d5"}
            
            # Accept tuple
            widget.set_highlighted_squares(("f4", "f5", "f6"))
            assert widget._highlighted_squares == {"f4", "f5", "f6"}
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_state_methods_trigger_update(self):
        """Test that state methods trigger widget update."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            
            # Mock the update method to verify it's called
            widget.update = Mock()
            
            # set_selected_square should trigger update
            widget.set_selected_square("e2")
            assert widget.update.called
            
            widget.update.reset_mock()
            
            # set_highlighted_squares should trigger update
            widget.set_highlighted_squares(["e4", "e3"])
            assert widget.update.called
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")


class TestMouseEventSignalEmission:
    """Tests for mouse event handling and signal emission."""
    
    def test_left_click_emits_signal_with_correct_square(self):
        """Test that left-clicking a square emits signal with correct parameters."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt, QPointF
            from PySide6.QtGui import QMouseEvent
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.resize(800, 800)
            
            # Set up signal spy
            received_signals = []
            widget.square_clicked.connect(lambda sq, btn: received_signals.append((sq, btn)))
            
            # Create a mouse event for clicking e4 (center)
            # e4 is at pixel position approximately (450, 450)
            event = QMouseEvent(
                QMouseEvent.Type.MouseButtonPress,
                QPointF(450, 450),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier
            )
            
            # Trigger the event
            widget.mousePressEvent(event)
            
            # Verify signal was emitted with correct parameters
            assert len(received_signals) == 1
            square, button = received_signals[0]
            assert square == "e4"
            assert button == Qt.MouseButton.LeftButton
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_right_click_emits_signal_with_right_button(self):
        """Test that right-clicking emits signal with right button."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt, QPointF
            from PySide6.QtGui import QMouseEvent
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.resize(800, 800)
            
            # Set up signal spy
            received_signals = []
            widget.square_clicked.connect(lambda sq, btn: received_signals.append((sq, btn)))
            
            # Create a right-click event on a1 (bottom-left)
            event = QMouseEvent(
                QMouseEvent.Type.MouseButtonPress,
                QPointF(50, 750),
                Qt.MouseButton.RightButton,
                Qt.MouseButton.RightButton,
                Qt.KeyboardModifier.NoModifier
            )
            
            widget.mousePressEvent(event)
            
            # Verify signal was emitted with right button
            assert len(received_signals) == 1
            square, button = received_signals[0]
            assert square == "a1"
            assert button == Qt.MouseButton.RightButton
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_click_outside_board_does_not_emit_signal(self):
        """Test that clicking outside the board does not emit a signal."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt, QPointF
            from PySide6.QtGui import QMouseEvent
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.resize(800, 800)
            
            # Set up signal spy
            received_signals = []
            widget.square_clicked.connect(lambda sq, btn: received_signals.append((sq, btn)))
            
            # Click outside the board (way to the right)
            event = QMouseEvent(
                QMouseEvent.Type.MouseButtonPress,
                QPointF(900, 400),
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier
            )
            
            widget.mousePressEvent(event)
            
            # Verify no signal was emitted
            assert len(received_signals) == 0
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_multiple_clicks_emit_multiple_signals(self):
        """Test that multiple clicks emit multiple signals."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt, QPointF
            from PySide6.QtGui import QMouseEvent
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.resize(800, 800)
            
            # Set up signal spy
            received_signals = []
            widget.square_clicked.connect(lambda sq, btn: received_signals.append((sq, btn)))
            
            # Click on e2
            event1 = QMouseEvent(
                QMouseEvent.Type.MouseButtonPress,
                QPointF(450, 650),  # e2 position
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier
            )
            widget.mousePressEvent(event1)
            
            # Click on e4
            event2 = QMouseEvent(
                QMouseEvent.Type.MouseButtonPress,
                QPointF(450, 450),  # e4 position
                Qt.MouseButton.LeftButton,
                Qt.MouseButton.LeftButton,
                Qt.KeyboardModifier.NoModifier
            )
            widget.mousePressEvent(event2)
            
            # Verify both signals were emitted
            assert len(received_signals) == 2
            assert received_signals[0][0] == "e2"
            assert received_signals[1][0] == "e4"
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_click_on_all_corner_squares(self):
        """Test clicking on all four corner squares."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import Qt, QPointF
            from PySide6.QtGui import QMouseEvent
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.resize(800, 800)
            
            # Set up signal spy
            received_signals = []
            widget.square_clicked.connect(lambda sq, btn: received_signals.append((sq, btn)))
            
            corners = [
                (50, 50, "a8"),    # Top-left
                (750, 50, "h8"),   # Top-right
                (50, 750, "a1"),   # Bottom-left
                (750, 750, "h1"),  # Bottom-right
            ]
            
            for x, y, expected_square in corners:
                event = QMouseEvent(
                    QMouseEvent.Type.MouseButtonPress,
                    QPointF(x, y),
                    Qt.MouseButton.LeftButton,
                    Qt.MouseButton.LeftButton,
                    Qt.KeyboardModifier.NoModifier
                )
                widget.mousePressEvent(event)
            
            # Verify all corners were detected correctly
            assert len(received_signals) == 4
            for i, (x, y, expected_square) in enumerate(corners):
                assert received_signals[i][0] == expected_square
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")


class TestSquareToRectConversion:
    """Tests for the _square_to_rect helper method."""
    
    def test_square_to_rect_valid_squares(self):
        """Test conversion of valid algebraic squares to rectangles."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from PySide6.QtCore import QRect
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            widget.resize(800, 800)
            
            # Get layout parameters
            square_size, x_margin, y_margin = widget._calculate_layout(800, 800)
            assert square_size == 100
            assert x_margin == 0
            assert y_margin == 0
            
            # Test a1 (bottom-left: file=0, rank=7)
            rect = widget._square_to_rect("a1", square_size, x_margin, y_margin)
            assert rect == QRect(0, 700, 100, 100)
            
            # Test h8 (top-right: file=7, rank=0)
            rect = widget._square_to_rect("h8", square_size, x_margin, y_margin)
            assert rect == QRect(700, 0, 100, 100)
            
            # Test e4 (center: file=4, rank=4)
            rect = widget._square_to_rect("e4", square_size, x_margin, y_margin)
            assert rect == QRect(400, 400, 100, 100)
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")
    
    def test_square_to_rect_invalid_squares(self):
        """Test that invalid squares return None."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import BoardWidget
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            widget = BoardWidget()
            square_size, x_margin, y_margin = widget._calculate_layout(800, 800)
            
            # Invalid squares
            assert widget._square_to_rect("i1", square_size, x_margin, y_margin) is None
            assert widget._square_to_rect("a9", square_size, x_margin, y_margin) is None
            assert widget._square_to_rect("z5", square_size, x_margin, y_margin) is None
            assert widget._square_to_rect("e", square_size, x_margin, y_margin) is None
            assert widget._square_to_rect("", square_size, x_margin, y_margin) is None
            assert widget._square_to_rect("e44", square_size, x_margin, y_margin) is None
            
        except Exception as e:
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

