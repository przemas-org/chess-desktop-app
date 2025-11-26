"""Main entry point for the chess application."""

import sys
from PySide6.QtWidgets import QApplication
from chess_app.game import Game
from chess_app.gui import MainWindow


def main():
    """Main function to run the chess application.
    
    This function bootstraps the Qt application, creates a Game instance
    with the standard starting position, and displays it in the MainWindow
    via the BoardWidget.
    
    The GUI is initialized with the starting FEN from the Game model,
    maintaining clean separation between the domain layer (Game) and
    presentation layer (MainWindow/BoardWidget).
    """
    # Create the Qt application
    app = QApplication(sys.argv)
    
    # Create a new game with standard starting position
    game = Game()
    
    # Get the starting FEN from the game model
    starting_fen = game.export_fen()
    
    # Create the main window
    window = MainWindow()
    
    # Set the board position using FEN
    window.set_board_fen(starting_fen)
    
    # Show the window
    window.show()
    
    # Start the Qt event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
