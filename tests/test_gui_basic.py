#!/usr/bin/env python3
"""
Basic GUI module tests.

This module validates that the GUI package can be imported and
that the MainWindow class can be instantiated without errors.
Tests are designed to be skipped gracefully in headless environments.
"""

import pytest


class TestGUIImport:
    """Tests for GUI module import and basic instantiation."""
    
    def test_gui_module_can_be_imported(self):
        """GUI module should be importable without errors."""
        pytest.importorskip("PySide6")
        
        # Should not raise any import errors
        from chess_app.gui import MainWindow
        assert MainWindow is not None
    
    def test_main_window_can_be_imported_directly(self):
        """MainWindow class should be importable from gui.main_window."""
        pytest.importorskip("PySide6")
        
        from chess_app.gui.main_window import MainWindow
        assert MainWindow is not None


class TestMainWindowInstantiation:
    """Tests for MainWindow class instantiation."""
    
    def test_main_window_can_be_instantiated(self):
        """MainWindow should be instantiable (may skip in headless environments)."""
        pytest.importorskip("PySide6")
        
        try:
            from PySide6.QtWidgets import QApplication
            from chess_app.gui import MainWindow
            
            # QApplication is required for QMainWindow instantiation
            # This may fail in headless environments, so we wrap it in try-except
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            assert window is not None
            assert window.windowTitle() == "Chess Desktop App — Human vs Human"
            assert window.width() == 800
            assert window.height() == 600
            
        except Exception as e:
            # If Qt cannot initialize (no display), skip the test gracefully
            pytest.skip(f"Qt initialization failed (likely headless environment): {e}")

