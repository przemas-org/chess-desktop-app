---
name: Human vs AI Gameplay Loop Design
overview: ""
todos:
  - id: 3c6498f6-d54c-486c-bdc7-b704bbf8f8f1
    content: Add centralized game-status evaluation and game-end handling in the main window controller, including modal messages, title updates, and input locking.
    status: pending
  - id: 9f969b52-728f-4c14-85fd-23739a5190c4
    content: Introduce and enforce a GUI-level input-enabled flag in the main window, short-circuiting all board interaction when the game is over.
    status: pending
  - id: 7dca4137-0454-48f5-a44e-8f068616b684
    content: Update the engine controller to skip engine move requests when the game status is not ongoing or check.
    status: pending
  - id: 465d2501-948d-41f2-8fc0-070733bac468
    content: Extend engine-disabled handling in the main window to show a minimal message box and update title to indicate fallback to Human vs Human mode.
    status: pending
  - id: 845f5394-43d7-4887-af8e-b94eff2662be
    content: Plan and implement or update tests around the human-vs-engine loop, game-end detection, input locking, and engine failure behavior using the existing fake engine adapter.
    status: pending
---

# Human vs AI Gameplay Loop Design

## 1. Summary

Implement a complete Human (White) vs Engine (Black) gameplay loop on top of the existing game, engine, and GUI architecture. The feature covers automatic engine replies, terminal game-state detection, game-end UX, input locking after game over, and minimal user messaging for engine failures.

## 2. Context

- The domain model (`Game`) already exposes legal-move generation, move application, side-to-move, game status (including checkmate and several draw types), and FEN/PGN import/export.
- The engine layer consists of `EngineAdapter` and its Stockfish-based implementation, with `EngineController` coordinating automated Black moves and handling engine errors and retries.
- The GUI layer uses `MainWindow` as the controller and `BoardWidget` as a FEN-driven view, with two-click move selection, side locking, and basic engine integration already in place.
- Current behavior: after a successful human move, the window triggers an engine request (if configured), Black moves are applied via the controller, and the board is refreshed; there is no explicit game-end UX or input disabling.

## 3. Functional Requirements

1. After each valid human move, automatically request an engine reply when it is the engine side to move, as long as the game is not in a terminal state and the engine is enabled.
2. Apply the engine-provided move to the game state, validate it through the domain model, and refresh the board.
3. Maintain side-to-move semantics such that the human always controls White and the engine always controls Black in this version.
4. Detect terminal game states (checkmate and all draw conditions supported by the domain model, including stalemate and other draws) after every move, human or engine.
5. When a terminal state is detected, present a modal message box summarizing the result (e.g., “Checkmate — White wins”, “Draw by stalemate”) and update the main window title to reflect game over.
6. After any terminal state, disable further board input for the rest of the session; clicks should be ignored without altering game state.
7. Do not issue further engine requests once the game is no longer ongoing (including draws and checkmate) even if called from the GUI.
8. If the engine becomes unavailable or is disabled due to errors, notify the user with a minimal modal message and fall back to Human vs Human mode for the remainder of the session.

## 4. Non-functional Requirements

1. Preserve existing asynchronous, non-blocking engine behavior and UI responsiveness.
2. Keep engine interaction robust: no engine failure should corrupt game state or hang the UI, and the fallback path must be simple and predictable.
3. Maintain testability by continuing to route all engine behavior through abstracted interfaces, enabling reuse of fake adapters in tests.
4. Avoid adding configuration complexity for v1: engine side and difficulty are fixed (engine as Black, fast search), and new flows should not introduce runtime configuration UIs.

## 5. Proposed Design

### 5.1 Game lifecycle and status evaluation

- Centralize game-status evaluation in the main window controller as a small, reusable helper that is called after every successful move (both human and engine) and after initial game setup.
- The helper will query the domain model for the current status and side-to-move, and then:
- For non-terminal statuses (ongoing or check), update the window title with a concise textual indication (e.g., side to move, optional “in check” hint) without locking input.
- For terminal statuses (checkmate and all draw variants), delegate to a dedicated game-end handler.

### 5.2 Game-end handling and UX

- Introduce a game-end handler in the main window controller responsible for:
- Mapping the domain-level game status and side-to-move to a human-readable result (“Checkmate — White wins”, “Checkmate — Black wins”, “Draw by stalemate”, “Draw by insufficient material”, or a generic “Draw by repetition/other rule” for the remaining draw status).
- Displaying a modal message box with this result text, blocking interaction with the main window until dismissed.
- Updating the main window title to a game-over variant that includes the result (e.g., base title plus “Game Over — Checkmate (Black wins)”).
- Marking input as disabled for the rest of the session (see 5.3).
- The handler is called uniformly after any move (human or engine) that transitions the game into a terminal state.

### 5.3 Input locking after terminal states

- Add an internal, GUI-level “input enabled” flag in the main window controller that is set to enabled upon game initialization and set to disabled when a terminal state is detected.
- All user-input paths originating from board interaction (source selection, destination selection, and selection clearing) will check this flag and immediately return when input is disabled.
- Engine thinking/in-flight checks continue to function as an additional guard; when the game is over, the input flag will stop new move attempts from being started at all.
- Input locking is purely GUI-level; the domain model remains unchanged and can still be inspected or exported (e.g., for PGN export) after game over.

### 5.4 Engine triggering rules and terminal-state awareness

- Extend the engine controller’s human-move notification entry point to become terminal-state aware without changing its public signature:
- On entry, check the domain game status via the game model.
- If the status is not ongoing or check, return immediately without making any engine requests, ensuring that no new engine computation is started after game end.
- If the status is ongoing or check and it is the engine-controlled side to move, proceed with the existing FEN export and asynchronous move request, subject to the existing enabled and in-flight guards.
- After an engine move has been successfully applied to the domain game, the controller will behave as it already does (clearing in-flight state and emitting an “engine move applied” signal). The GUI reaction to this signal (see 5.5) will be responsible for performing the subsequent game-status evaluation and potential game-end handling.

### 5.5 Post-move update and status evaluation wiring

- Maintain the current pattern where the main window connects to the engine controller’s “move applied” signal to refresh the board display.
- Augment this connection so that, after the board is refreshed, the main window also invokes the shared game-status evaluation helper described in 5.1. This ensures that engine moves are treated identically to human moves in terms of game-end detection and UX.
- Similarly, after a successful human move is applied and the board is refreshed, the main window will call the same helper before (or alongside) notifying the engine controller, to catch human-delivered checkmates and draw states without requiring an engine response.

### 5.6 Window title semantics

- Define a simple, consistent title scheme that reflects both engine availability and basic game status while remaining minimal:
- While the game is ongoing: indicate whether the engine is enabled and optionally which side is to move (e.g., “Chess Desktop App — Engine Enabled (White to move)” or “Chess Desktop App — Human vs Human (Black to move)”).
- When the game ends: switch to a “game over” title that includes the outcome (e.g., “Chess Desktop App — Game Over: Checkmate (Black wins)” or “Chess Desktop App — Game Over: Draw by stalemate”), regardless of engine presence.
- Keep all detailed explanations inside the modal message; the title remains concise and is the only persistent status display.

### 5.7 Engine failure notification and fallback behavior

- Reuse the existing engine-controller signal that indicates permanent engine disablement and is already consumed by the main window.
- Extend the main-window handler for this signal so that, in addition to updating the engine-availability part of the title, it:
- Presents a minimal modal message box stating that an engine error occurred and that the application has switched to Human vs Human mode, without exposing low-level error codes to the user.
- Leaves the current game state untouched and keeps board input enabled (unless the game is already over), so the user can continue the game as a pure human-vs-human game from the current position.
- The engine controller and adapter logic for retries, timeouts, and process errors remain unchanged; only the user-facing notification and title updates are added on top.

## 6. System Components

1. Domain model component (`Game`):

- Already supports terminal-state detection and side-to-move queries; no structural changes required.
- Will continue to be the single source of truth for game rules and result calculation.

2. Engine coordination component (`EngineController`):

- Gains a simple precondition check for terminal game states before initiating new engine requests.
- Continues to validate engine moves through the domain model and to emit success or disablement signals as before.

3. Engine integration component (`EngineAdapter` and Stockfish implementation):

- No interface or behavior changes required for this feature beyond existing fast search settings; it remains an opaque provider of best-move suggestions.

4. GUI controller component (`MainWindow`):

- Becomes the central orchestrator of game lifecycle, responsible for calling game-status evaluation after moves, coordinating game-end UX, and managing the input-enabled flag.
- Enhances its response to engine disablement to include user messaging and maintain a clear distinction between engine vs human-only modes in the title.

5. GUI view component (`BoardWidget`):

- Remains a stateless FEN renderer with click signaling; no change to its API is needed.
- Input locking is handled entirely in the main window by ignoring click signals when appropriate.

## 7. Sequence Diagrams (Textual)

### 7.1 Human move with engine response, game continues

1. User performs a two-click move as White on the board.
2. Main window validates and applies the move to the domain game, then refreshes the board display from the new FEN.
3. Main window evaluates game status; result is ongoing or check, so it updates the title with current side-to-move and, if applicable, indicates check.
4. Main window notifies the engine controller of the applied human move.
5. Engine controller confirms the game is not in a terminal state and that it is the engine side to move, then exports the FEN and requests a move from the engine adapter.
6. Engine adapter sends UCI commands to Stockfish and, within the timeout, receives a best-move response and emits a move-ready signal.
7. Engine controller applies the move to the domain game, clears in-flight state, and emits its engine-move-applied signal.
8. Main window, in response, refreshes the board from the updated game state and re-runs the game-status evaluation; since the game is still ongoing or check, input remains enabled and the loop continues.

### 7.2 Human move resulting in checkmate (no engine reply)

1. User plays a White move that delivers checkmate.
2. Main window applies the move, refreshes the board, and calls the game-status evaluation helper.
3. The helper receives a checkmate status from the domain model and forwards control to the game-end handler.
4. The game-end handler determines the winner, shows a modal “Checkmate — White wins” message, updates the window title to a game-over variant, and disables further input.
5. Main window does not attempt to notify the engine controller for an engine reply (or, if it calls, the controller immediately returns due to the terminal-state precondition), ensuring no further engine activity.

### 7.3 Engine move resulting in stalemate

1. User plays a normal White move; steps 2–5 from 7.1 occur and the engine is requested to move.
2. Engine responds with a legal Black move that results in stalemate.
3. Engine controller applies the move to the domain game and emits its engine-move-applied signal.
4. Main window refreshes the board from the new position and then calls the game-status evaluation helper.
5. The helper detects stalemate, the game-end handler shows “Draw by stalemate”, updates the title to a draw game-over variant, and disables board input.
6. No further engine requests are issued for this game.

### 7.4 Engine failure mid-game

1. User plays a normal White move, the main window applies it, evaluates status as ongoing, and requests an engine move via the controller.
2. The engine adapter encounters an error (e.g., timeout or crash) and emits a failure signal, causing the controller to mark the engine as disabled and emit its engine-disabled signal with a reason.
3. Main window’s engine-disable handler updates its engine-enabled flag, adjusts the title to “Human vs Human”, and shows a minimal message box (“Engine error — switched to Human vs Human”).
4. The current game state remains unchanged; the user can continue playing moves for both sides, with no further engine interactions.

## 8. Data Model Changes

- No changes to the persistent or core domain data model are required.
- All new behavior is driven off existing domain concepts (status, side-to-move, move history) and GUI-level state flags.
- Any new GUI-level flags (such as input-enabled) are transient and scoped to the main window instance.

## 9. Affected Services / Modules

1. `chess_app/gui/main_window.py`:

- Add centralized game-status evaluation and game-end UX handling.
- Introduce and enforce an input-enabled flag in click-handling paths.
- Extend engine-disable handling to show a user-facing message and update titles.
- Adjust window-title updates to incorporate basic ongoing/terminal status information while keeping the title minimal.

2. `chess_app/gui/engine_controller.py`:

- Add a simple status check before issuing engine requests to ensure no moves are requested after terminal states.
- Keep existing engine-error behavior and signals; no interface changes.

3. `chess_app/game.py`:

- No functional changes, but further relied on as the canonical provider of status and side-to-move data.

4. Test modules (for implementation phase):

- GUI integration tests to verify the human-vs-engine loop, game-end UX, and input locking.
- Engine-controller tests to confirm that no engine requests are issued once the game is over.

## 10. Risks and Alternatives

1. **Risk: Inconsistent title and message text**

- If mapping from domain statuses to user-visible text is duplicated or scattered, it can drift over time.
- Mitigation: centralize string mapping logic in a small helper inside the main window controller so both title and modal messages derive from the same mapping.

2. **Risk: Subtle race conditions around engine responses and input locking**

- Edge cases where the user attempts a move while an engine move is completing could cause confusing behavior.
- Mitigation: continue to rely on the existing “in-flight” flag, keep engine responses asynchronous, and ensure that input-locking is driven solely by domain status after each applied move.

3. **Alternative: Domain-driven game lifecycle manager**

- An alternative would introduce a separate domain-level game-lifecycle component responsible for transitions and notifications, rather than having the main window orchestrate status evaluation.
- This is deferred for now in favor of a simpler GUI-controller-based approach that leverages the existing responsibilities and keeps the change set small.

## 11. Open Questions

1. Exact phrasing of game-end and engine-error messages (e.g., whether to include technical detail or keep them strictly minimal) may be refined during implementation but will default to short, user-friendly text.
2. The precise format of ongoing-status information in the window title (e.g., whether to show “White to move” vs. omitting it) can be tuned based on user feedback without affecting the architecture, as long as the title remains the sole persistent status display.