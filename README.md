# Chess Desktop App

A chess desktop application built with Python. The application is designed for one human player to play a game with bot player.

## Features

- Basic chess application framework
- Modular project structure
- Ready for expansion

## Prerequisites

- Python 3.8 or higher
- Poetry (for dependency management)

## Installation

1. Install Poetry if you haven't already:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Clone the repository and navigate to the project directory:
```bash
cd chess_desktop_app
```

3. Install dependencies:
```bash
poetry install
```

## Usage

Run the application using Poetry:
```bash
poetry run chess-app
```

Or activate the virtual environment and run directly:
```bash
poetry shell
python -m chess_app.main
```

### Running the GUI

The GUI displays the current chess position using Unicode chess pieces. The application window shows:
- An 8×8 chessboard with classic beige/brown squares
- Chess pieces rendered as Unicode glyphs
- Automatic board scaling and centering on window resize

The board orientation is fixed with white at the bottom (standard chess perspective).

## Developer Guide

### The `Game` Model - Core API

The `Game` class in `chess_app/game.py` is the central abstraction for managing chess game state and rules. **All UI and application code should interact with the game through this class.** The `python-chess` library is used internally but its types (`chess.Board`, `chess.Move`, etc.) are intentionally not exposed - always use the `Game` class API.

#### Creating a Game

```python
from chess_app.game import Game

# Create a new game with standard starting position
game = Game()

# Create a game from a FEN (Forsyth-Edwards Notation) string
game = Game.from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")

# Create a game from a PGN (Portable Game Notation) string
pgn = """
[Event "Example Game"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0
"""
game = Game.from_pgn(pgn)
```

#### Listing Legal Moves

```python
# Get all legal moves in the current position
legal_moves = game.get_legal_moves()
for move in legal_moves:
    print(f"{move.san} ({move.uci}): {move.from_square} -> {move.to_square}")
```

#### Applying Moves

```python
# Apply a move using UCI notation (e.g., "e2e4")
game.apply_move("e2e4")

# Apply a move using a Move object
legal_moves = game.get_legal_moves()
game.apply_move(legal_moves[0])

# For pawn promotion, include the promotion piece in UCI (e.g., "e7e8q")
game.apply_move("e7e8q")  # Promote to queen
```

#### Undoing Moves

```python
# Undo the last move
game.undo()

# Safe to call multiple times - no-op when no moves to undo
game.undo()
game.undo()
```

#### Checking Game Status

```python
from chess_app.game import GameStatus, Side

# Get current game status
status = game.get_status()
if status == GameStatus.CHECKMATE:
    print("Checkmate!")
elif status == GameStatus.CHECK:
    print("Check!")
elif status == GameStatus.STALEMATE:
    print("Stalemate - Draw")

# Get whose turn it is
side = game.get_side_to_move()
print(f"{'White' if side == Side.WHITE else 'Black'} to move")

# Get move numbers and counters
print(f"Move {game.get_fullmove_number()}")
print(f"Halfmove clock: {game.get_halfmove_clock()}")
```

#### Accessing Move History

```python
# Get read-only tuple of all moves played
history = game.get_history()
for i, move in enumerate(history, 1):
    print(f"{i}. {move.san}")
```

#### Exporting Game State

```python
# Export current position as FEN
fen = game.export_fen()
print(fen)
# Example: "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"

# Export game as PGN with optional headers
pgn = game.export_pgn({
    "Event": "Casual Game",
    "Site": "Home",
    "Date": "2024.01.15",
    "White": "Player 1",
    "Black": "Player 2"
})
print(pgn)
```

#### Error Handling

The `Game` class raises specific exceptions for invalid operations:

```python
from chess_app.game import IllegalMoveError, InvalidFenError, InvalidPgnError

# IllegalMoveError - raised when attempting an illegal move
try:
    game.apply_move("e2e5")  # Illegal opening move
except IllegalMoveError as e:
    print(f"Illegal move: {e}")

# InvalidFenError - raised when creating game from invalid FEN
try:
    game = Game.from_fen("invalid fen string")
except InvalidFenError as e:
    print(f"Invalid FEN: {e}")

# InvalidPgnError - raised when creating game from invalid PGN
try:
    game = Game.from_pgn("not a valid pgn")
except InvalidPgnError as e:
    print(f"Invalid PGN: {e}")
```

#### Important Notes

- **Do not interact with `chess.Board` directly** - use the `Game` class API
- The `Game` class encapsulates all chess rules and state management
- All domain types (`Move`, `GameStatus`, `Side`) are defined in `chess_app/game.py`
- Move history is maintained automatically as moves are applied
- `undo()` is safe to call even when there are no moves to undo (no-op)
- FEN and PGN export/import provide full round-trip capability

### GUI Architecture

The application features a PySide6-based desktop GUI for displaying chess positions.

#### BoardWidget - FEN-View Component

The `BoardWidget` class (`chess_app/gui/board_widget.py`) is a pure view component that:
- Renders chess positions from FEN strings
- Operates independently of the `Game` model
- Displays pieces using Unicode chess glyphs (♔♕♖♗♘♙)
- Automatically scales and centers the board within available space
- Maintains fixed orientation: white at bottom, black at top (rank 1 at bottom, rank 8 at top)

**Key API:**
```python
from chess_app.gui import BoardWidget

widget = BoardWidget()
widget.set_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
# Board updates immediately
```

**Board Orientation:**
- Rank 8 (black pieces) at top
- Rank 1 (white pieces) at bottom
- Files a-h from left to right
- a1 square is dark (bottom-left)

#### MainWindow Integration

The `MainWindow` class integrates `BoardWidget` as its central widget and provides a FEN-based API:

```python
from chess_app.gui import MainWindow

window = MainWindow()
window.set_board_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
window.show()
```

Communication between `Game` model and GUI is via FEN strings only.

#### GUI Entry Point

The main entry point (`chess_app/main.py`) bootstraps the Qt application:

```python
from PySide6.QtWidgets import QApplication
from chess_app.game import Game
from chess_app.gui import MainWindow

app = QApplication([])
game = Game()
window = MainWindow()
window.set_board_fen(game.export_fen())
window.show()
app.exec()
```

Run via: `poetry run chess-app`

#### Environment Prerequisites

**Required:**
- Python 3.9 or higher
- PySide6 (installed via `poetry install`)
- Display server (X11, Wayland, or equivalent)

**Headless Environments:**
- GUI cannot run without a display server
- Tests gracefully skip in headless CI/CD environments
- For headless testing with GUI, use Xvfb or similar virtual display

**Font Requirements:**
- Unicode chess piece glyphs (U+2654-U+265F)
- Default font: "DejaVu Serif" (fallback to system default)
- Most modern systems include chess piece glyphs in default fonts

## Development

### Running Tests

```bash
poetry run pytest
```

### Running Tests with Coverage

```bash
poetry run pytest --cov=chess_app
```

### Adding Dependencies

```bash
poetry add <package-name>
```

### Adding Development Dependencies

```bash
poetry add --group dev <package-name>
```

## Project Structure

```
chess_desktop_app/
├── pyproject.toml          # Poetry configuration
├── README.md               # This file
├── chess_app/              # Main package
│   ├── __init__.py
│   └── main.py             # Entry point
└── tests/                  # Test directory
    └── __init__.py
```

## License

MIT

## Author

Your Name
