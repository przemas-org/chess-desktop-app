<!-- 9eb911a8-48bc-44e5-a63b-46ff9cc5fe01 b38607c1-8a22-4f81-bef1-39919b2cab3f -->
# Core Game Model & Rules – Feature Solution Design

### 1. Summary

- **Goal**: Introduce a core `Game` model as a thin, authoritative wrapper around `python-chess.Board` for standard chess rules.
- **Key capabilities**: Legal move generation, move application with undo, game status reporting, and FEN/PGN import-export for a single game.
- **Quality bar**: Scenario-based unit tests covering legal/illegal moves, check/checkmate, castling, en passant, and FEN/PGN round-trips.

### 2. Context

- **Application**: Desktop chess app (`chess_desktop_app`) using Python with Poetry; future UI will drive gameplay via this core model.
- **Rule engine**: `python-chess` (Board + PGN modules) is the single source of truth for rules, legality, and game outcomes.
- **Scope constraint**: Standard chess only (no variants, no Chess960); FEN/PGN must be standard and valid.

### 3. Functional Requirements

- **Initialization**
- Create a new standard game starting from the normal initial position.
- Initialize from a **full FEN** string (all fields present) representing a valid standard position.
- Initialize from a **single-game PGN** string (minimal headers; moves + result).
- **Move handling**
- Expose `get_legal_moves()` for the current side to move.
- Expose `apply_move()` that:
- Validates the move via `python-chess`; rejects illegal moves.
- Updates internal board state and move history.
- Updates game status.
- Expose `undo()` with arbitrary depth, reverting both board state and move history.
- **Status & metadata**
- Expose `get_status()` returning a `GameStatus` enum (e.g. `ONGOING`, `CHECK`, `CHECKMATE`, `STALEMATE`, `DRAW_50_MOVE`, `DRAW_INSUFFICIENT_MATERIAL`).
- Expose accessors for side to move, full-move number, half-move clock (from FEN/Board).
- Expose read-only move history (including enough info for UI and tests).
- **Import/export**
- `export_fen()` returns a full FEN string of the current position.
- `export_pgn()` returns a minimal single-game PGN (moves + result, optional headers).
- Import functions validate input and surface clear errors on invalid FEN/PGN.
- **Error handling**
- Illegal move application raises a custom `IllegalMoveError` with clear messaging.
- Invalid FEN/PGN raise explicit, documented exceptions (custom or mapped to `ValueError`).

### 4. Non-functional Requirements

- **Correctness**: Behavior must be fully aligned with `python-chess`; no divergence of rule logic.
- **Performance**: Single-board operations should be effectively O(1) per move from the app’s perspective; no unnecessary copying of board state.
- **Simplicity**: Model remains a thin wrapper; complex features (e.g., analysis, engines, variants, redo) are explicitly out of scope.
- **Testability**: Public API is deterministic and scenario-driven, enabling clear FEN → move → FEN/Status tests.
- **Extensibility**: Design should be easy to extend later (e.g., redo, annotations, engine integration) without breaking the core API.

### 5. Proposed Design

- **Core class: `Game`**
- Encapsulates a `python_chess.Board` instance and a simple move history list.
- Responsible for:
- Initializing board from standard start, FEN, or PGN.
- Providing legal moves in a UI-friendly representation.
- Validating and applying moves (delegated to `python-chess`).
- Maintaining move history and supporting undo.
- Computing and exposing `GameStatus`.
- Importing/exporting FEN and PGN.
- **Move representation**
- Introduce a lightweight domain `Move` DTO (e.g., dataclass) that wraps `python-chess.Move` while decoupling the UI from the library:
- Fields like: UCI string, optional SAN, from-square, to-square, optional promotion piece.
- `get_legal_moves()` returns a list of these `Move` objects.
- `apply_move()` accepts either a `Move` instance or a UCI string for simplicity.
- **Status representation: `GameStatus` enum**
- Enum values derived from `python-chess` state:
- `ONGOING` – default when game is not over and not in check.
- `CHECK` – `board.is_check()` true, but not terminal.
- `CHECKMATE` – `board.is_checkmate()`.
- `STALEMATE` – `board.is_stalemate()`.
- `DRAW_50_MOVE` – `board.can_claim_fifty_moves()` / `board.is_fifty_moves()`.
- `DRAW_INSUFFICIENT_MATERIAL` – `board.is_insufficient_material()`.
- Optionally, a generic `DRAW_OTHER` to encompass 3-fold repetition or other draw conditions if we choose to surface them.
- `get_status()` computes this on demand from the underlying `Board`.
- **History & undo**
- Maintain an internal `List[Move]` history ordered chronologically.
- When `apply_move()` is called and deemed legal:
- Convert to `python-chess.Move`.
- Call `board.push(move)`.
- Append a corresponding domain `Move` to history.
- `undo()`:
- Calls `board.pop()` if possible.
- Pops from the internal history list.
- No redo list maintained at this stage.
- **FEN integration**
- Initialization:
- `Game()` default constructor uses `chess.Board()` (standard start).
- `Game.from_fen(fen: str)` calls `chess.Board(fen=fen)`; invalid FEN results in a clear exception.
- Export:
- `export_fen()` simply delegates to `board.fen()`.
- **PGN integration**
- Import (single game):
- Use `python-chess.pgn.read_game()` from a `StringIO` to parse one game.
- Construct a new `Game` instance; replay `game.mainline_moves()` on a `Board` to ensure consistency.
- Populate internal history list from these moves and set result from PGN headers.
- Export (single game):
- Build a `python-chess.pgn.Game` from the move history and, optionally, header metadata.
- Set the result header based on the provided result or current board outcome.
- Use a `StringIO` and `pgn.Game().accept()` / `pgn.write_game()` to generate the PGN string.
- **Error handling**
- `IllegalMoveError(Exception)` raised by `apply_move()` when:
- The parsed move is not in `board.legal_moves`.
- Or the move input cannot be parsed.
- Invalid FEN/PGN:
- Wrap low-level errors in domain-specific exceptions (e.g., `InvalidFenError`, `InvalidPgnError`) or document using `ValueError` with clear messages.

### 6. System Components

- **New module: `chess_app/game.py` (or `chess_app/core/game.py`)**
- `class Game` – main game model API.
- `class IllegalMoveError(Exception)` – custom exception.
- `class InvalidFenError(Exception)` / `InvalidPgnError(Exception)` (optional, but recommended for clarity).
- `enum GameStatus(Enum)` – game status abstraction.
- `@dataclass Move` – domain move representation.
- **Existing integration points**
- `chess_app/__init__.py` can re-export `Game`, `GameStatus`, and error types for easier access.
- `chess_app/main.py` (or future UI layer) will construct and interact with `Game` exclusively, not `python-chess.Board` directly.
- **Dependencies**
- Ensure `python-chess` is added to `pyproject.toml` with an appropriate version constraint (e.g., `python-chess >=1.999,<2.0`).

### 7. Sequence Diagrams (Textual)

- **New game + move sequence**

1. UI creates `game = Game()`.
2. UI calls `moves = game.get_legal_moves()` to populate move list.
3. User selects a move; UI calls `game.apply_move(selected_move)`.
4. `Game` validates via underlying `Board`, updates state & history, and UI re-queries `get_status()` and `export_fen()` for display.

- **FEN-based scenario test**

1. Test constructs `game = Game.from_fen(fen_str)`.
2. Test calls `game.apply_move(uci_or_move)` inside a try/except.
3. Assert legality (no `IllegalMoveError`), new `export_fen()` value, updated `get_status()`, and history length.

- **Undo sequence**

1. After several `apply_move()` calls, UI invokes `game.undo()`.
2. `Game` pops from `Board` and move history.
3. UI refreshes board from `export_fen()` and status from `get_status()`.

### 8. Data Model Changes

- **New domain types**
- `Game` – encapsulates the current game state, move history, and rule interactions through `python-chess`.
- `Move` – immutable representation of a move for UI and tests (wrapping the underlying `python-chess.Move`).
- `GameStatus` – enum for game outcome / state abstraction.
- `IllegalMoveError`, `InvalidFenError`, `InvalidPgnError` – domain error types.
- **No persistence schema changes**
- The feature is in-memory only; there is no database or long-term storage at this stage.

### 9. Affected Services / Modules

- **Directly affected**
- `chess_app/game.py` (new): core game model implementation.
- `pyproject.toml`: add `python-chess` dependency.
- **Indirectly affected**
- `chess_app/main.py` or any CLI/UI bootstrap will be updated later to construct and use `Game` rather than touching `python-chess` directly.
- `tests/` package: new scenario tests validating this feature.

### 10. Risks and Alternatives

- **Risk: Over-coupling to `python-chess` types**
- Mitigation: Expose only domain-level `Game`, `Move`, and `GameStatus` in public API; keep direct `python-chess` usage internal.
- **Risk: Status mapping gaps**
- Some draw conditions (e.g., 3-fold repetition) may not map 1:1 to the initial enum set.
- Mitigation: Start with the requested subset and optionally add more enum values later, using a backward-compatible strategy.
- **Alternative design: Use `python-chess.Board` directly in UI**
- Rejected because it leaks low-level details and makes future changes (e.g., alternate engines, persistence, analysis) harder.
- **Alternative design: Immutable game objects**
- Rejected for now to keep integration with a stateful UI simple; can be added later as a separate projection API if needed.

### 11. Open Questions

- **Move input format**: Should `apply_move()` only accept UCI strings, or also SAN and/or coordinate objects? (Current design: UCI + `Move` DTO.)
- **Draw condition granularity**: Do we need to distinguish all draw types now (e.g., 3-fold, 75-move rule), or is the initial subset sufficient?
- **PGN headers**: Should we support a minimal fixed set of headers (e.g., Event, Site, Date, Round, White, Black, Result), or keep headers fully optional and caller-provided?

### To-dos

- [x] Add python-chess as a dependency in pyproject.toml and lock it via Poetry.
- [x] Implement the Game class, Move DTO, GameStatus enum, and custom exceptions around python-chess.Board.
- [x] Implement FEN and single-game PGN import/export methods on the Game model using python-chess APIs.
- [x] Create scenario-based unit tests that validate legal/illegal moves, check/checkmate, castling, en passant, and FEN/PGN round-trips.