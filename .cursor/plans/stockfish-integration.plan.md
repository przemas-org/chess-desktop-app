<!-- 93871737-b05e-42ee-80ee-d899bf770790 69626876-1c77-4f5c-a829-3aff0f99c3d5 -->
# Stockfish Integration – Feature Solution Design

### 1. Summary

Stockfish will be integrated as a long-lived background engine process that always plays Black against a human playing White. After each valid human move, the app will asynchronously query Stockfish for a reply, validate the returned move against the current game position, and apply it on the board if legal; on failures or missing engine, the app gracefully falls back to human-vs-human without breaking the UI.

### 2. Context

- The domain layer uses python-chess (wrapped by the `Game` class in `game.py`) and exposes FEN export, legal move generation, move application, game status, and side-to-move.
- The GUI layer is built with Qt for Python (PySide6). `MainWindow` in `gui/main_window.py` owns a `Game` instance and orchestrates move selection via `BoardWidget` in `gui/board_widget.py` using FEN.
- Currently, all moves are human-driven via mouse clicks; there is no concept of an engine-controlled side or external engine process.

### 3. Functional Requirements

- Engine role and side:
- Stockfish acts as the opponent, controlling the Black pieces for the whole game; the human always plays White.
- No switching of sides or hint/analysis mode in this version.
- Invocation rules:
- After each successful human move, if it is now Black to move and the engine feature is enabled and healthy, the app requests a move from Stockfish.
- Engine moves are automatically applied with no extra UI controls.
- UCI interaction:
- On startup, launch a single Stockfish process and perform the minimal UCI handshake.
- For each engine turn, send a `position` command using the current FEN and then `go movetime 100`.
- Parse the `bestmove` line and extract the UCI move string.
- Reply validation and error handling:
- Treat a move as valid only if it is legal in the current `Game` position (using the existing domain rules).
- If the engine returns an illegal move, ignore it once, immediately re-query for a new best move, and if still illegal, stop engine play for the rest of the game and log an error.
- If the engine does not reply within a reasonable timeout (roughly 500–1000 ms after a `go movetime 100`), log an error and stop engine play for the remainder of the game.
- Side locking and interaction:
- The engine-controlled side (Black) is locked: the user cannot move Black pieces, regardless of whose turn it is.
- The human can only make moves for White, and only when it is White’s turn according to the `Game` state.
- Engine availability and feature gating:
- The Stockfish binary is bundled inside the application at a known path; the app starts the engine only from this bundled location, never from user-provided paths.
- If the binary is missing, not executable, or fails to start, the app starts normally but with engine play disabled for that session.
- Testing:
- Automated tests simulate engine responses by mocking the engine interface; no real Stockfish process is launched in CI.

### 4. Non-functional Requirements

- Responsiveness:
- The Qt GUI event loop must remain responsive while waiting for engine replies. No blocking reads or long-running computations in the UI thread.
- Robustness and isolation:
- Engine failures (crashes, timeouts, malformed output) must not corrupt `Game` state or freeze the UI.
- When disabled (by configuration or runtime failure), the app behaves as pure human-vs-human, preserving existing behavior.
- Simplicity of configuration:
- No user-facing configuration UI for engine selection, options, or search parameters; paths and constants live in code.
- Security:
- Only the bundled Stockfish binary is executed; no dynamic lookup from environment variables, PATH, or user input.

### 5. Proposed Design

- Engine integration model:
- Introduce an engine abstraction in the GUI layer that exposes a simple asynchronous API: "given the current game position, request a reply move for Black and be notified when the result (or failure) is available".
- Implement this abstraction with a Qt-based process adapter around a single long-lived Stockfish process, using non-blocking reads and Qt signals/slots.
- Process management strategy (Stockfish lifecycle):
- On application startup, attempt to launch Stockfish from a fixed relative path inside the package (for example, under a dedicated `engines` or `resources` folder within the app distribution).
- After starting the process, perform the minimal UCI handshake (`uci` / `uciok`, optional `isready`) once, then mark the engine as ready.
- Keep the process alive for the entire session; do not restart between moves.
- If the process fails to start, handshake fails, or it exits unexpectedly, mark the engine as permanently unavailable for that session.
- Engine request/response flow:
- When a human move completes successfully and it becomes Black’s turn, the controller constructs the current position from the domain by exporting FEN from the `Game` instance.
- The engine adapter sends `position fen <FEN>` followed by `go movetime 100` to the Stockfish process.
- The adapter maintains internal state indicating that a request is in flight and starts a one-shot Qt timer for the timeout window (e.g., 1000 ms).
- As engine output arrives, the adapter buffers lines and looks for a `bestmove` line associated with the active request; once found, it extracts the UCI move string and cancels the timeout timer.
- The adapter notifies the controller with a structured result (success with UCI move, or error such as timeout or malformed output).
- Applying engine moves and validation:
- On a successful engine response, the controller asks the domain to validate and apply the suggested move. This can be done by attempting to apply the UCI move through the existing move-application API, which already enforces legality.
- If application succeeds, the controller refreshes the board view from the updated `Game` state using the existing FEN-based update path.
- If the move is illegal or cannot be parsed, the controller will, as per requirements, attempt one more query to the engine using the same position; if the second response is also invalid, it logs the problem and disables engine play for the remainder of the game.
- Side locking and move routing:
- The controller will track which side is engine-controlled (Black, fixed in v1) and use the domain’s knowledge of side-to-move and piece ownership to decide whether to accept a user click as a potential move source.
- When the user left-clicks a square, the controller first checks whether that square contains a piece belonging to the human-controlled side and whether it is that side’s turn; only then does it compute and show legal destinations.
- While an engine move request is in flight (after a White move), the controller ignores or short-circuits any further user move attempts until the engine move, timeout, or failure has been resolved.
- Error and timeout handling:
- If a timeout fires before a `bestmove` is seen, the adapter reports a timeout error; the controller logs the error and disables engine play going forward.
- If the engine process crashes or exits while in use, the adapter transitions to an error state, and any further engine requests immediately fail; the controller treats this equivalently to a timeout case.
- Feature gating and fallback behavior:
- Engine enabling is determined once at startup: the app attempts to start and initialize Stockfish; on success, engine features are enabled; on failure, the app runs in pure human-vs-human mode.
- Runtime disablement (due to illegal move responses, timeouts, or crashes) flips an internal flag so that no further engine calls are made in the current session. The rest of the game can continue with two human-controlled sides if desired.

### 6. System Components

- Stockfish process adapter (Qt-based engine wrapper):
- New component in the GUI layer responsible for interacting with the Stockfish binary using `QProcess`.
- Responsibilities:
- Launch and manage the long-lived Stockfish process from the known binary path.
- Implement the UCI handshake and readiness tracking.
- Provide an asynchronous request API for computing a best move given a FEN position.
- Handle output parsing (tracking `bestmove` lines), timeouts, and process errors.
- Expose high-level signals or callbacks to deliver results (UCI move or failure) back to the controller.
- Engine controller (bridging `Game` and Stockfish):
- New small orchestration component owned by `MainWindow` that knows about:
- The current `Game` instance.
- Which side is engine-controlled (Black for v1).
- Whether engine play is currently enabled and healthy.
- Responsibilities:
- After each successful human move, decide whether to invoke the engine based on side-to-move and engine state.
- When the engine result arrives, validate and apply it through the domain layer and refresh the board.
- Implement the re-query-on-illegal-move logic and final disablement policy.
- Track in-flight engine requests and prevent concurrent overlapping requests.
- Domain model adjustments:
- The domain already exposes methods to get the side to move, legal moves, and apply moves from UCI, which are sufficient for validating engine replies.
- Optionally, add a small helper to query which side occupies a given square, allowing the controller to enforce that only White pieces can be selected for moves by the user.
- GUI integration points:
- `MainWindow` will be extended to:
- Own an instance of the engine controller.
- Initialize the engine controller after `Game` has been set, and shut it down on window close.
- Call into the engine controller after a human move is applied and the board has been updated.
- Consult the engine controller (and domain helpers) when handling square selection so that Black pieces cannot be moved by the user.
- `BoardWidget` remains a FEN-based, engine-agnostic view; no changes are required beyond its existing click and highlight behavior.
- Configuration and binary path:
- Introduce a small configuration constant in the GUI or application bootstrap code that defines the relative path to the bundled Stockfish binary.
- This constant will be the single source of truth for the engine location, simplifying packing and distribution.

### 7. Sequence Diagrams (Textual)

- Application startup with engine:

1. Application entry point constructs the Qt application, creates a new `Game`, and instantiates `MainWindow`.
2. `MainWindow` sets its `Game` reference and initializes the board view from the game’s initial FEN.
3. `MainWindow` (or a helper) constructs the Stockfish process adapter with the configured binary path.
4. The adapter starts the Stockfish process and runs the UCI handshake; on success, it marks itself as ready and notifies the engine controller; on failure, the engine controller marks engine play as disabled.

- Human move followed by engine reply:

1. User selects a White piece square; the controller verifies that it is White’s turn and that the selected square contains a White piece; legal destinations are highlighted.
2. User clicks a legal destination; the controller applies the resulting move to the `Game` and updates the board via FEN.
3. The controller observes that it is now Black to move, engine play is enabled, and no engine request is in flight; it asks the engine adapter for a best move for the current FEN.
4. The adapter sends the `position` and `go movetime 100` commands to Stockfish, starts a timeout timer, and waits for output.
5. Stockfish outputs a `bestmove` line; the adapter parses the UCI move, cancels the timer, and returns the move to the controller.
6. The controller attempts to apply the move to the `Game`. If successful, it updates the board from the new FEN and clears the in-flight flag.

- Timeout or invalid move path:

1. After a human move, the controller requests an engine reply.
2. If the timeout timer fires before a valid `bestmove` is parsed, the adapter reports a timeout error.
3. The controller logs the issue, disables engine play for the current session, and does not attempt further engine calls.
4. If the engine returns an illegal move, the controller discards it and immediately performs one more request from the same position; on a second illegal move, it logs an error and disables engine play for the remainder of the game.

### 8. Data Model Changes

- Engine state tracking:
- Introduce an internal engine state for the controller (for example, values such as disabled, initializing, ready, error) to drive behavior and prevent invalid calls.
- Track whether a request is currently in progress to avoid overlapping `go` commands.
- Engine role configuration:
- Add a small configuration flag or constant representing the engine-controlled side; for v1, this is hard-coded to Black but can later be generalized.
- Optional domain helper:
- Add a read-only helper in the `Game` domain model to query which side (if any) occupies a given square. This keeps the knowledge of piece ownership in the domain layer and allows the controller to enforce side locking without parsing FEN in the GUI.

### 9. Affected Services / Modules

- `chess_app/main.py`:
- Bootstrap adjustments to create and wire the engine-related components (through `MainWindow`) at application startup.
- `chess_app/game.py`:
- Possible addition of a small read-only helper for querying the piece owner of a square (if chosen over doing this in the GUI).
- No changes to core move application, legal move generation, or FEN/PGN functionality are required.
- `chess_app/gui/main_window.py`:
- Extend the main window to:
- Own the engine controller.
- Enforce that only White pieces can be selected and moved by the user.
- Trigger engine requests after successful human moves and handle engine responses.
- `chess_app/gui/board_widget.py`:
- No semantic changes expected; only indirect impact via selection and highlight logic driven by the controller.
- New GUI module for the Stockfish adapter and engine controller:
- A dedicated module under the GUI package that contains the Stockfish `QProcess` wrapper and the engine controller orchestration logic.
- Tests under `tests/`:
- New tests validating engine integration behavior using mocked engine interfaces and simulated engine outputs.

### 10. Risks and Alternatives

- Risks:
- Stockfish process could hang or produce unexpected output, leading to stalled engine responses; mitigated by explicit timeouts and robust parsing that ignores unknown lines.
- Hard-coded binary path may differ between development and packaged distributions; mitigated by centralizing the path in one configuration constant and documenting packaging expectations.
- Concurrency edge cases if multiple engine requests are triggered quickly (e.g., due to repeated user clicks) could lead to overlapping `go` commands; mitigated by enforcing a strict "one in-flight request" policy and temporarily ignoring user moves while waiting for the engine.
- Alternatives considered:
- Using python-chess’s built-in engine helpers with a worker thread instead of `QProcess`. This would provide a more Pythonic engine abstraction but introduces thread management and is less idiomatic for Qt-based apps compared to a `QProcess`-centric design.
- Spawning a fresh Stockfish process per move. This simplifies lifecycle management but is significantly less efficient and makes time controls and future features (like analysis mode) harder to implement; the long-lived process is preferred.

### 11. Open Questions / Future Decisions

- Packaging details for the Stockfish binary (exact folder layout, naming conventions, and multi-OS handling) will need to be finalized when preparing distribution artifacts.
- The exact timeout value (between 500 ms and 1000 ms) can be tuned based on empirical responsiveness during manual testing on target machines.
- Future versions may introduce user controls to configure which side the engine plays, to toggle engine play mid-game, or to request hints/analysis; the proposed engine abstraction and controller are designed to support these extensions later without major refactoring.

### To-dos

- [ ] Design the engine abstraction and Stockfish QProcess adapter API in the GUI layer, including request/response and error signaling.
- [ ] Define the engine controller responsibilities and its integration with the Game domain model and MainWindow (including side locking and in-flight request handling).
- [ ] Plan how application startup wires the engine components (binary path configuration, lifecycle) into the existing main entry point and main window.
- [ ] Define the testing strategy with mocked engine implementations, covering valid replies, illegal moves, timeouts, and missing-engine scenarios.