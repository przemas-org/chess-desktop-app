<!-- 3e74b417-5ff5-4b2d-bd8a-927847fb2aa5 84673608-dd0a-4ee9-927f-77638faa1bcf -->
# Basic GUI & Board Rendering – Feature Solution Design

## 1. Summary

Introduce a minimal desktop GUI using PySide6 with a main window hosting a dedicated board widget. The board widget renders an 8×8 chessboard from a FEN string using Unicode chess symbols, starting from the standard initial position, with fixed white-at-bottom orientation and correct resize behavior.

## 2. Context

- The existing project already encapsulates chess rules and state in a Game model, which exposes FEN import/export and hides python-chess types.
- The current entry point is a console-based main function that prints a welcome message and version.
- This feature is the first GUI step: no input handling, no game controls, just a visual board view.
- Future features will need the GUI to redraw after moves, so the board widget should already expose a simple refresh API based on FEN.

## 3. Functional Requirements

- Render a PySide6 main window containing only a central board area.
- Display the standard starting chess position on startup, sourced from a new Game instance or its exported FEN.
- Treat the board widget as a pure FEN-view component that accepts a FEN string from its owner and renders pieces accordingly.
- Use Unicode chess symbols for pieces, with white at the bottom and black at the top.
- Draw an 8×8 grid with alternating light and dark squares, no labels or borders beyond the squares themselves.
- Keep squares perfectly square during resize, centering the board and leaving uniform margins as needed.
- Provide a method on the board widget’s public API to update the FEN and trigger a redraw, suitable for future integration with game logic.

## 4. Non-functional Requirements

- **Simplicity**: Keep responsibilities clear: Game remains headless domain logic; the new GUI layer is a thin rendering wrapper.
- **Responsiveness**: Board redraws should be smooth with no noticeable lag on typical desktop hardware.
- **Maintainability**: GUI code should live in a dedicated module or package, with clear separation between rendering logic and FEN parsing.
- **Portability**: Avoid platform-specific Qt features; rely on standard PySide6 widgets and painting APIs.

## 5. Proposed Design

### 5.1 Overall Architecture

- Extend the main entry point to bootstrap a Qt application instead of printing to the console.
- Introduce a dedicated GUI module that defines a main window class and a board widget class.
- On startup, the main function will:
- Create a new Game instance using the default constructor (standard position).
- Obtain the FEN string from the Game model.
- Instantiate the main window, creating a board widget.
- Pass the FEN string into the board widget via a setter-like method before showing the window.

### 5.2 Board Widget Responsibilities

- Represent the logical board state internally as an 8×8 structure derived from the piece-placement field of the FEN string.
- Maintain the current FEN string as internal state, updating the derived board representation on changes.
- Implement a public method (for example, a method named set_fen) that:
- Accepts a full FEN string.
- Parses the piece-placement section and validates basic assumptions (8 ranks, 8 files when expanded).
- Updates the internal board representation.
- Triggers a repaint via the Qt update mechanism.
- Implement custom painting logic that:
- Computes square size as the minimum of available width and height divided by eight, truncated to an integer.
- Centers the 8×8 board in the available widget rectangle by computing equal horizontal and vertical margins.
- Iterates over ranks and files, drawing light or dark rectangles based on their parity.
- Draws the appropriate Unicode character centered in each non-empty square.

### 5.3 FEN to Board Mapping

- Use only the first field of the FEN string (piece placement) for rendering; other fields are ignored by this widget.
- Parse the piece-placement field rank by rank, from rank 8 down to rank 1, matching FEN’s convention.
- For each rank:
- Walk through each character; digits represent consecutive empty squares, letters represent pieces.
- Uppercase letters correspond to white pieces, lowercase to black pieces.
- Map rank 8 to the top row of the widget and rank 1 to the bottom row to keep white at the bottom.
- Maintain a deterministic mapping from FEN piece symbols to Unicode code points (for example, one mapping table shared by the widget).

### 5.4 Unicode Piece Rendering

- Define a static mapping from piece identifiers (e.g., white king, black pawn) to the standard Unicode chess glyphs.
- Choose a font family that reliably supports these glyphs on most platforms (for example, a generic sans-serif fallback, with Qt selecting an appropriate system font).
- In the paint logic:
- Configure the painter’s font size relative to the square size (for example, slightly smaller than the square to ensure margins).
- Align text to the center of each square using Qt’s text alignment features.

### 5.5 Layout and Resize Behavior

- Place the board widget as the central widget of the main window.
- Ensure the board widget’s size hint is square-ish (width and height equal) to encourage a square layout.
- In the board widget’s paint logic:
- Determine the drawable square side length as the minimum of the widget’s current width and height divided by eight.
- Compute horizontal and vertical offsets to center the 8×8 area within the widget.
- Do not stretch or distort; if the window is very wide or very tall, excess space becomes padding around the centered board.

### 5.6 Main Window and Application Bootstrap

- Create a Qt application object in the main entry point.
- Create a main window class that:
- Sets window title and an initial reasonable size.
- Creates a board widget instance and sets it as the central widget.
- At startup:
- Instantiate Game from the core model.
- Retrieve the starting FEN via its export function.
- Call the board widget’s FEN setter before showing the window.

### 5.7 Future Integration Considerations

- The board widget’s public API is intentionally limited to FEN-based updates and does not know about the Game type or python-chess.
- Future move-handling features can:
- Use the Game model to apply moves and then call the board widget’s FEN setter with the updated FEN.
- Add interaction handling (mouse events) in the widget or higher-level controller classes without changing the basic rendering responsibilities.

## 6. System Components

- **Game model (existing)**:
- Manages chess rules and state, exposes FEN export used as the data source for the initial board.
- **GUI module (new)**:
- Main window class responsible for owning and displaying the board widget.
- Board widget class responsible solely for converting FEN into an internal 8×8 representation and painting it.
- **Application entry point (updated)**:
- Initializes the Qt application environment.
- Bridges the Game model and the board widget by providing the initial FEN string.

## 7. Sequence Diagrams (Textual)

- **Startup and initial render**:

1. User starts the application via the existing script entry point.
2. The main function creates a Game instance.
3. The Game instance returns the FEN for the standard starting position.
4. The main function creates the Qt application and main window.
5. The main window creates a board widget and passes the FEN to its FEN setter method.
6. The board widget parses the FEN into its internal 8×8 representation.
7. Qt shows the main window; the board widget’s paint logic draws the board and pieces.

- **Future redraw after move (design intent only)**:

1. A controller or main window applies a move to the Game model.
2. The Game model updates its board state and can again export the new FEN.
3. The controller calls the board widget’s FEN setter with the new FEN.
4. The board widget updates its internal representation and triggers a repaint.

## 8. Data Model Changes

- No changes to the existing core Game model, enums, or move structures.
- The board widget maintains its own internal representation of the current board:
- An 8×8 structure where each element represents either an empty square or a piece with color and type, derived from the FEN string.
- This representation is local to the GUI layer and not exposed beyond the widget.

## 9. Affected Services / Modules

- **chess_app/game.py**: Used as-is; no modifications required for this feature.
- **chess_app/main.py**: Updated to bootstrap the Qt GUI instead of printing to the console, and to bridge the Game model and the board widget using a FEN string.
- **New GUI module**: Introduced under the chess_app package to house the main window and board widget classes.
- **Project configuration**: pyproject configuration extended to include PySide6 as a runtime dependency.

## 10. Risks and Alternatives

- **Risk: FEN parsing bugs in the widget**
- Mitigation: Limit parsing to the well-defined piece-placement field, add unit tests that validate rank/file expansion and symbol mapping.
- **Risk: Font or Unicode glyph availability**
- Mitigation: Use common system fonts and verify glyph presence during development; if issues appear later, a sprite-based renderer can be introduced behind the same board widget interface.
- **Alternative: Use image sprites instead of Unicode**
- Deferred: Unicode is acceptable for this iteration; switching to images later can be done inside the widget without changing its public API.
- **Alternative: Directly expose the Game model to the widget**
- Rejected: Violates the pure FEN-view requirement and couples GUI to domain types, making testing and reuse harder.

## 11. Open Questions

- Should the window title or icon include any specific branding text beyond a generic chess label, or is a simple default acceptable for now?
- Is there any preferred default window size or aspect ratio for the initial release, beyond ensuring that the board fits comfortably on common laptop screens?

### To-dos

- [ ] Define a new GUI module with a main window class and wire it into the existing main entry point to start a PySide6 application.
- [ ] Implement the board widget that parses FEN into an 8×8 representation and paints an 8×8 Unicode-based chessboard with proper resize behavior.
- [ ] Add unit tests to validate FEN-to-board mapping and Unicode piece mapping logic independently of the GUI painting.