"""Main entry point for the chess application."""

import sys
import logging
from PySide6.QtWidgets import QApplication
from chess_app.game import Game
from chess_app.gui import MainWindow
from chess_app.gui.engine_integration import StockfishProcessAdapter
from chess_app.engine_config import get_stockfish_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    stream=sys.stderr
)


def main():
    """Main function to run the chess application.
    
    This function bootstraps the Qt application, creates a Game instance
    with the standard starting position, and displays it in the MainWindow
    via the BoardWidget.
    
    The GUI is initialized with the starting FEN from the Game model,
    maintaining clean separation between the domain layer (Game) and
    presentation layer (MainWindow/BoardWidget).
    
    Engine initialization is attempted at startup. If Stockfish is not
    available or initialization fails, the application continues in
    human-vs-human mode with engine features disabled.
    """
    # Create the Qt application
    app = QApplication(sys.argv)
    
    # Create a new game with standard starting position
    game = Game()
    
    # Create the main window
    window = MainWindow()
    
    # Wire the game into the window and initialize the board display
    window.set_game(game)
    window.update_board_from_game()
    
    # Attempt to initialize engine
    stockfish_path = get_stockfish_path()
    
    if stockfish_path is None:
        # Stockfish binary not found or not executable
        logging.warning(
            "Stockfish binary not found or not executable. "
            "Running in human-vs-human mode. "
            "To enable engine features, place the Stockfish binary in the "
            "'stockfish/' directory at the project root."
        )
    else:
        # Stockfish binary found, attempt initialization
        try:
            adapter = StockfishProcessAdapter(stockfish_path)
            
            # Define signal handlers for initialization
            def on_initialized():
                """Handle successful engine initialization."""
                logging.info("Stockfish engine initialized successfully")
                window.set_engine_adapter(adapter)
            
            def on_initialization_failed(error_code, message):
                """Handle engine initialization failure."""
                logging.error(
                    f"Stockfish initialization failed: {message}. "
                    "Running in human-vs-human mode."
                )
                # App continues without engine
            
            # Connect signals
            adapter.initialized.connect(on_initialized)
            adapter.initialization_failed.connect(on_initialization_failed)
            
            # Start initialization (asynchronous)
            adapter.initialize()
            
        except Exception as e:
            # Catch any unexpected errors during adapter setup
            logging.error(
                f"Failed to create engine adapter: {e}. "
                "Running in human-vs-human mode."
            )
    
    # Show the window
    window.show()
    
    # Start the Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
