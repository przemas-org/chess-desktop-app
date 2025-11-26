<!-- 46d0f01d-d1f1-4d4f-8692-4f1248a2c337 4c837c66-a160-4a32-ae74-20352ac6ba95 -->
# Feature Design: Input Handling – Move Selection

## 1. Summary

Implement click-based move selection on the board so a user can play legal moves by clicking source and destination squares. The main window will own the game model, the board widget will handle rendering plus mouse interaction, and moves will be validated and applied via the existing game logic.

## 2. Context

- The game model is encapsulated in the `Game` class, which exposes legal move generation, move application, and FEN export.
- The GUI currently consists of a `MainWindow` that owns a central `BoardWidget`, and communicates only via FEN strings from an external caller (for example the `main` module or tests).
- The board widget renders an 8×8 board from FEN, with fixed white-at-bottom orientation and internal matrix representation, but has no input handling or highlighting yet.
- Tests already cover FEN propagation from `Game` through `MainWindow` into `BoardWidget`.

## 3. Functional Requirements

1. The main window must own a `Game` instance and be able to update the board display from the game state.
2. Clicking a square on the board should select it as a source if there is at least one legal move starting from that square; otherwise any selection must be cleared.
3. Once a source is selected, clicking a different square should attempt to treat it as a destination: if the source–destination pair forms a legal move, it must be executed in the game; if not, the current selection should be preserved without side effects.
4. Clicking the same square again must cancel the current selection.
5. Right-click anywhere on the board must cancel the current selection and clear highlights.
6. When a square is selected, that square must be visually highlighted and all legal destination squares from it must be highlighted as possible moves.
7. Only legal moves as defined by the game model may be considered for highlighting and execution; no GUI-only move validation is allowed.
8. After a legal move is executed, the game state must update, the board must refresh from the game’s FEN, and all selection and highlighting must be cleared.
9. For this feature, the user may play moves for both colors manually; there is no AI or side restriction.
10. Promotion moves must always auto-promote to a queen, without presenting a promotion choice UI.
11. Illegal sources or destinations must be handled silently, without dialogs or status messages.

## 4. Non-functional Requirements

- Maintain a clear separation of concerns: the board widget remains presentation-focused and FEN-based; the main window coordinates between user input and the game model.
- Ensure the click mapping between widget coordinates and algebraic square names is correct and easily adaptable for future board orientation features.
- Performance must be smooth for typical user interactions; recomputing legal moves from the game on each source selection is acceptable given the small problem size.
- The feature should be covered by unit tests for board input behavior and integration tests for end-to-end move execution and FEN updates.

## 5. Proposed Design

### 5.1 Ownership of the Game instance

- Extend the main window so that it owns a single `Game` instance as part of its internal state.
- Provide a method to set or replace the game instance from outside (for example `set_game`), primarily for testability and future features.
- Add a simple method (for example `update_board_from_game`) that reads the current FEN from the game and passes it to the existing board FEN API.

### 5.2 BoardWidget input and highlighting responsibilities

- Extend the board widget to:
- Track basic interaction state: currently selected source square (if any) and a set of highlighted destination squares.
- Map mouse click positions to board coordinates (file and rank indices) based on the existing layout calculation, then to algebraic square strings like "e2".
- Emit a Qt signal when a square is clicked, carrying the algebraic square name and information about the mouse button.
- Render highlighting for the selected source square and its possible destination squares during the paint pass.
- Highlighting style (v1):
- Use a tinted background overlay to distinguish the selected source square.
- Use another tint (or a slightly different transparency) for destination squares, without differentiating captures versus quiet moves at this stage.

### 5.3 MainWindow coordination and move execution

- Connect the board widget’s square-click signal to a handler in the main window that implements the two-click move UX using the game model.
- In the handler:
- On left-click with no current selection: query the game’s legal moves, filter those whose from-square equals the clicked square, and if the result is non-empty, set that square as the selection and compute the set of legal destination squares to pass back to the board widget for highlighting. If there are no legal moves from that square, clear selection and highlights.
- On left-click with an existing selection:
- If the clicked square is the same as the current selection, clear selection and highlights.
- Else, treat the clicked square as destination and check if there is a legal move from the selected source to this destination. If such a move exists, construct the appropriate move representation (including auto-queen promotion where relevant), apply it through the game’s move API, refresh the board from the game’s FEN, and clear selection and highlights. If no such move exists, do nothing other than possibly leaving highlights unchanged.
- On right-click (or equivalent secondary button), clear selection and highlights without touching the game state.
- Because the game already exposes a legal move list and move application, this handler should reuse these methods directly, converting square names to the game’s representation only via the domain move abstraction.

### 5.4 Signal and state interfaces between MainWindow and BoardWidget

- Add a Qt signal in the board widget to represent user clicks in terms of algebraic square names and mouse button.
- Add simple methods in the board widget to:
- Set or clear the selected square.
- Set or clear the collection of highlighted destination squares.
- The main window owns the selection semantics, but may delegate the storage of selected square and destinations to the board widget so that repainting is localized; alternatively, it can treat the board widget as a pure view and always send the current selection and highlight sets as parameters whenever they change.
- For v1, storing the selection state inside the board widget is acceptable, as long as the public API to control it is small and well-defined.

### 5.5 Promotion handling

- When constructing a move from the selected source and destination squares, detect promotion by asking the game (for example from its legal move list) whether any legal move from the source to that destination includes a promotion flag.
- For such moves, always select the queen promotion variant.
- Because the game model already represents promotion moves via its move data type, the main window should simply choose the appropriate move object and pass it back into the game apply-move method without additional rule handling.

### 5.6 Error and edge-case handling

- If move application raises a domain error (for example illegal move), catch it in the main window handler and treat it as an illegal destination: selection state remains unchanged and no user-visible error is shown.
- If any unexpected exception bubbles up from the game or the board conversion logic, it should be logged (if logging is available) but must not crash the GUI; the safest fallback is to clear selection and leave the board position unchanged.

## 6. System Components

- Game model component:
- Provides legal moves for the current position, move application, and FEN export.
- Remains independent of the GUI; no changes are required for basic click-to-move support, beyond possibly clarifying the move API documentation.
- Main window component:
- Owns the game instance and the board widget.
- Maintains connection between user input (square clicks) and the game’s move logic.
- Updates the board widget’s FEN whenever the game state changes.
- Board widget component:
- Continues to provide a FEN-based board view.
- Gains input handling (mouse click mapping to squares and signal emission) and simple highlighting state.

## 7. Interaction Flow (Sequence-Level Description)

1. Application startup:

- The main module creates a `Game` instance and a `MainWindow`.
- The main window receives the game instance (either via constructor or a setter) and calls its board update method to push the initial FEN into the board widget.

2. User clicks a square for the first time:

- The board widget maps mouse coordinates to a square, derives the algebraic name, and emits a square-click signal with button information.
- The main window receives the signal; since there is no current selection, it queries legal moves from the game and filters them by the clicked from-square.
- If moves exist, it marks that square as selected, computes destination squares, and instructs the board widget to update its selection and highlight state, triggering a repaint.
- If no moves exist, it clears any existing selection and ensures the board widget has no highlights.

3. User clicks a destination square:

- The board widget emits another square-click signal.
- The main window sees that a source is already selected and compares the new square with the existing selection.
- If they are equal, it clears selection and highlights via the board widget.
- If they differ, it checks the legal moves for a matching move from the selected source to the clicked destination.
- If a matching move is found, it applies the move through the game, refreshes the board from the game’s FEN via the main window’s update method, and clears all highlights.
- If no matching move is found, it leaves selection and highlight state unchanged.

4. User right-clicks anywhere:

- The board widget emits a signal indicating a right-click (or the main window identifies the button from the event).
- The main window clears any selection and instructs the board widget to clear highlighting, then triggers a repaint.

## 8. Data Model Changes

- Domain model (`Game` and related types):
- No structural changes are required; existing methods for legal moves and move application already provide what the GUI needs.
- Optional: add or clarify helper methods to convert from source and destination square strings to a specific domain move, or to surface legal moves in a way that is convenient for lookup by from/to squares plus promotion.
- GUI model (board widget internal state):
- Extend the board widget’s internal state with fields for selected square (as algebraic name or file/rank indices) and a set of highlighted destination squares.
- These fields drive rendering but do not affect the underlying game state.

## 9. Affected Modules

- `chess_app.gui.main_window`:
- Add ownership of the game instance, public API to set the game, and methods to refresh the board from the game and handle square-click signals.
- Wire up the signal-slot connection between the board widget and the main window.
- `chess_app.gui.board_widget`:
- Add mouse event handling, coordinate-to-square mapping, signaling of clicked squares, and highlighting state plus rendering logic.
- `chess_app.main`:
- Optionally simplified or slightly adjusted to pass the `Game` instance into the main window rather than only using FEN strings.
- `tests` (GUI-related test modules):
- Add unit tests for board click-to-square mapping and highlighting behavior.
- Add integration tests that drive clicks through Qt’s test utilities (or simulated calls) to verify that legal moves update the game and FEN, and that selection clears after moves.

## 10. Risks and Alternatives

- Risk: Mouse coordinate to square mapping errors could cause incorrect move selection, especially near board edges or under non-square window sizes.
- Mitigation: Rely on the existing layout helper, add unit tests for mapping, and manually verify a few known squares (corners and center).
- Risk: Tight coupling between the main window and board widget selection state could make future features like board orientation more complex.
- Mitigation: Keep the public API between these components small and semantic (set selected square, set destination highlights), and avoid exposing low-level drawing details.
- Risk: Silent failure on illegal destinations might confuse some users.
- Mitigation: This is acceptable for v1 per requirements; a later iteration can add subtle feedback such as a brief shake animation or transient highlight.
- Alternative design: Implement a separate controller object to manage interaction between the game and the board widget.
- Rejected for now to keep the architecture simple; the main window can act as this controller until the application grows more complex.

## 11. Open Questions

- None for this feature: the UX rules, ownership model, and interaction patterns for v1 are fully specified in the requirements. If future work introduces AI or multiple boards, this design can be revisited to extract a dedicated controller or view-model layer.

### To-dos

- [ ] Make MainWindow own a Game instance, expose a method to set or replace it, and add a helper to refresh the board from the game’s FEN.
- [ ] Extend BoardWidget with mouse handling, square coordinate mapping, highlighting state, and a signal that emits algebraic square names with mouse button info.
- [ ] In MainWindow, connect BoardWidget click signals to game move logic implementing the two-click UX, including auto-queen promotion and silent handling of illegal moves.
- [ ] Adjust the main application bootstrap code to pass the Game instance into MainWindow and use its refresh helper instead of manually pushing FEN.
- [ ] Add unit tests for BoardWidget click mapping and highlighting plus integration tests that simulate click sequences and verify move application, FEN updates, and clearing of highlights.