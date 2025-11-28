"""
Engine configuration and binary path resolution.

This module provides platform-specific Stockfish binary path resolution
and availability checking. It serves as the single source of truth for
engine binary locations in the application.
"""

import os
import sys
from pathlib import Path
from typing import Optional


def _get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns the directory containing the chess_app package.
    
    Returns:
        Path object pointing to the project root.
    """
    # This file is in chess_app/engine_config.py
    # Project root is one level up from chess_app
    return Path(__file__).parent.parent


def _get_platform_binary_name() -> str:
    """
    Get the platform-specific Stockfish binary name.
    
    Returns:
        The binary filename for the current platform.
    """
    if sys.platform.startswith('linux'):
        return 'stockfish-linux'
    elif sys.platform.startswith('win'):
        return 'stockfish-windows.exe'
    elif sys.platform.startswith('darwin'):
        return 'stockfish-macos'
    else:
        # Fallback for unknown platforms
        return 'stockfish'


def get_stockfish_path() -> Optional[str]:
    """
    Get the absolute path to the Stockfish binary for the current platform.
    
    This function:
    1. Determines the appropriate binary name for the platform
    2. Constructs the path relative to the project root
    3. Checks if the binary exists and is executable
    4. Returns the path if valid, None otherwise
    
    The expected directory structure is:
        project_root/
            stockfish/
                stockfish-linux
                stockfish-windows.exe
                stockfish-macos
            chess_app/
                ...
    
    Returns:
        Absolute path to the Stockfish binary if available and executable,
        None otherwise.
    
    Example:
        path = get_stockfish_path()
        if path:
            adapter = StockfishProcessAdapter(path)
        else:
            # Run in human-vs-human mode
            pass
    """
    project_root = _get_project_root()
    binary_name = _get_platform_binary_name()
    binary_path = project_root / 'stockfish' / binary_name
    
    # Check if the file exists
    if not binary_path.exists():
        return None
    
    # Check if the file is executable
    if not os.access(str(binary_path), os.X_OK):
        return None
    
    return str(binary_path)


def is_stockfish_available() -> bool:
    """
    Check if Stockfish binary is available on this system.
    
    This is a convenience wrapper around get_stockfish_path() that
    returns a boolean instead of the path.
    
    Returns:
        True if Stockfish binary exists and is executable, False otherwise.
    
    Example:
        if is_stockfish_available():
            print("Engine features enabled")
        else:
            print("Running in human-vs-human mode")
    """
    return get_stockfish_path() is not None

