<!-- 7291d785-dac1-4dcd-ac2f-51a2df7a325d 3add7eec-e6a9-4e2c-b49d-1f8021dd6da6 -->
# Basic GUI & Board Rendering – JIRA Task Breakdown

## CHESS-1: Add PySide6 dependency and project configuration

**Description**

- Add `PySide6` as a runtime dependency in `pyproject.toml` and ensure it is compatible with the existing Python and dependency stack.
- Verify that the packaging and execution model (e.g., `poetry run`) correctly installs and resolves Qt for Python.
- Decide whether GUI modules will opt into `snake_case` / `true_property` via `from __feature__ import ...` and document the convention for the GUI layer.

**Tests**

- **Unit tests**: Not applicable.
- **Functional tests**:
- `poetry install` succeeds on supported platforms.
- A minimal `PySide6` smoke script (e.g., a trivial `QApplication` + empty `QMainWindow`) runs without import or runtime errors.

**Dependencies**

- None.

---

## CHESS-2: Introduce GUI module structure

**Description**

- Create a dedicated GUI package under `chess_app` (for example `chess_app/gui/`).
- Define initial module stubs for:
- `main_window` (Qt main window class).
- `board_widget` (custom widget responsible for board rendering).
- Optional helper modules (e.g., `fen_view_model` or `board_model`) to keep FEN parsing separate from painting.
- Ensure these modules import cleanly and do not reference the domain `Game` model directly (GUI remains FEN-based).

**Tests**

- **Unit tests**:
- Simple import tests to ensure `from chess_app.gui import ...` (or equivalent) succeeds.
- **Functional tests**:
- Manual developer verification that a placeholder main window + board widget can be instantiated from a temporary harness without errors.

**Dependencies**

- Depends on: **CHESS-1** (PySide6 available for GUI imports).

---

## CHESS-3: Implement FEN-to-8×8 board representation logic

**Description**

- Implement a pure-Python function or small class (e.g., in `fen_view_model`) that:
- Accepts a FEN string.
- Extracts and validates the piece-placement field.
- Expands each rank from FEN notation into 8 files, enforcing exactly 8 ranks and 8 files per rank.
- Produces an 8×8 structure representing either an empty square or a piece (type + color), with rank 8 mapped to the top row and rank 1 to the bottom row.
- Define clear error handling/validation strategy for malformed FENs (e.g., raise a domain-specific exception or return a sentinel error).
- Ensure the logic is independent of Qt so it can be unit-tested easily.

**Tests**

- **Unit tests** (new test module, e.g., `tests/test_gui_fen_view_model.py`):
- Verify correct expansion of the standard starting position FEN (matches expected 8×8 layout, white at the bottom).
- Verify expansion of several non-trivial FENs (irregular piece distributions, promoted pieces) with correct rank/file mapping.
- Verify that digits correctly represent consecutive empty squares and that total squares per rank equal 8.
- Verify that invalid FEN strings (wrong rank count, too many squares in a rank, illegal characters) are rejected according to the chosen error strategy.
- **Functional tests**:
- None beyond unit-level for this logic; full functional behaviour covered in later GUI integration tasks.

**Dependencies**

- Depends on: **CHESS-2** (GUI helper module location agreed and created).

---

## CHESS-4: Implement Unicode piece mapping utilities

**Description**

- Implement a deterministic mapping from FEN piece symbols (e.g., `K`, `k`, `Q`, `q`, etc.) or internal piece descriptors (color + type) to Unicode chess glyphs.
- Encapsulate mapping in a small utility (e.g., `piece_glyphs.py`) to keep painting code simple.
- Decide on and document a default font family/strategy that reliably supports these glyphs across platforms; keep the font choice overridable from the widget.

**Tests**

- **Unit tests** (e.g., `tests/test_gui_piece_glyphs.py`):
- Assert that each standard piece type/color combination maps to the correct Unicode code point.
- Assert that invalid piece identifiers are handled gracefully (e.g., raise or return `None`).
- **Functional tests**:
- Manual verification that glyphs render correctly on at least one reference platform using a small test harness (e.g., show each glyph in a grid widget).

**Dependencies**

- Depends on: **CHESS-2** (utility module location agreed and created).

---

## CHESS-5: Implement BoardWidget painting and resize behaviour

**Description**

- Implement the custom `BoardWidget` as a Qt widget (e.g., subclassing `QWidget` or `QFrame`) that:
- Maintains the current FEN string and corresponding 8×8 board model.
- Exposes a public API `set_fen(fen: str)` which:
- Uses the FEN parsing logic from **CHESS-3**.
- Updates internal state and triggers a repaint via `update()`.
- Implements `paintEvent` to:
- Compute square size as `min(width, height) // 8`.
- Center the 8×8 grid within the widget with equal margins.
- Draw alternating light/dark squares.
- Draw Unicode piece glyphs centered in occupied squares using the mapping from **CHESS-4**.
- Ensure the widget reports a square-ish `sizeHint` to encourage reasonable layouts.

**Tests**

- **Unit tests** (where feasible without a full GUI):
- Tests for the internal helper methods that compute square size, offsets, and square rectangles given a widget size.
- Tests asserting that board indices (rank/file) map to the correct screen coordinates.
- **Functional tests**:
- Manual test plan:
- Open a test harness window with the `BoardWidget` set to the starting position FEN and verify visual correctness (orientation, colors, piece placement).
- Resize the window in extreme aspect ratios and verify squares remain square and the board stays centered.
- Change FEN at runtime and verify the board redraws correctly.

**Dependencies**

- Depends on: **CHESS-3** (FEN parsing), **CHESS-4** (glyph mapping), **CHESS-2** (widget skeleton).

---

## CHESS-6: Implement MainWindow shell and board integration

**Description**

- Implement a `MainWindow` Qt class (subclassing `QMainWindow`) that:
- Sets a reasonable window title (e.g., "Chess" or project branding) and an initial size large enough for a clear board.
- Creates a `BoardWidget` instance and sets it as the central widget.
- Provides a simple interface (e.g., a method or signal/slot) for updating the board from external FEN strings.
- Keep this class focused on composition, not on game rules or move logic.

**Tests**

- **Unit tests** (lightweight):
- Instantiate `MainWindow` in a non-interactive test environment and assert that its central widget is a `BoardWidget` instance.
- **Functional tests**:
- Manual verification that starting the application shows the main window with a centered board and that resizing the window behaves as expected.

**Dependencies**

- Depends on: **CHESS-5** (BoardWidget implemented), **CHESS-2** (module structure).

---

## CHESS-7: Update application entry point to bootstrap Qt GUI

**Description**

- Refactor `chess_app/main.py` to:
- Create a `QApplication` instance as the primary event loop.
- Instantiate the existing `Game` model in its default starting position.
- Obtain the FEN string from the `Game` model via its export API.
- Instantiate `MainWindow`, pass the FEN into the contained `BoardWidget` (via its FEN setter), and show the window.
- Start the Qt event loop instead of the previous console-only behaviour.
- Ensure that the entry-point behaviour remains correct when invoked via the existing CLI or script entry points (no additional side effects).

**Tests**

- **Unit tests**:
- Minimal test to ensure the main module can be imported without side effects (actual GUI startup guarded by `if __name__ == "__main__"`).
- **Functional tests**:
- Manual smoke test: running the application via the documented command shows the starting-position board with white at the bottom.

**Dependencies**

- Depends on: **CHESS-1** (PySide6 available), **CHESS-6** (MainWindow implemented), existing **Game** model.

---

## CHESS-8: Add automated tests for GUI-related core logic and wire into CI

**Description**

- Finalize and organize all non-Qt unit tests created in earlier tasks (FEN parsing, glyph mapping, geometry helpers) under the `tests/` package.
- Ensure they run as part of the standard test suite (e.g., `pytest`) alongside existing core game tests.
- Optionally add a very small number of Qt-aware tests if the environment and CI support a headless Qt backend; otherwise, document the manual GUI test plan.

**Tests**

- **Unit tests**:
- All tests from **CHESS-3**, **CHESS-4**, and parts of **CHESS-5** integrated and passing under CI.
- **Functional tests**:
- Document a short manual regression checklist for GUI behaviour (board rendering, resize, FEN update) to accompany releases.

**Dependencies**

- Depends on: **CHESS-3**, **CHESS-4**, **CHESS-5**, existing CI/test runner configuration.

---

## CHESS-9: Update documentation and developer onboarding for GUI

**Description**

- Update `README.md` (or create a dedicated docs section) to:
- Describe the new GUI capabilities and how to start the application.
- Clarify that the GUI layer is FEN-driven and decoupled from python-chess types, with the `Game` model acting as the bridge.
- Document any use of `__feature__` imports (`snake_case`, `true_property`) in GUI modules and the rationale.
- Capture the manual GUI test checklist at a high level.

**Tests**

- **Unit tests**: Not applicable.
- **Functional tests**:
- Manual verification that a new developer can follow the README to install dependencies, run tests, and launch the GUI successfully.

**Dependencies**

- Depends on: **CHESS-7** (entry point behaviour stable), **CHESS-8** (test commands finalized).

### To-dos

- [ ] Add PySide6 dependency and verify basic Qt smoke test (CHESS-1).
- [ ] Create GUI package and module skeletons for main window, board widget, and helpers (CHESS-2).
- [ ] Implement and test FEN-to-8x8 board model utilities (CHESS-3).
- [ ] Implement and test Unicode glyph mapping utilities (CHESS-4).
- [ ] Implement BoardWidget, set_fen API, and painting/resize behaviour (CHESS-5).
- [ ] Implement MainWindow and integrate BoardWidget (CHESS-6).
- [ ] Refactor main.py to bootstrap Qt application and wire Game to GUI via FEN (CHESS-7).
- [ ] Integrate GUI-related core logic tests into CI (CHESS-8).
- [ ] Update README and docs for GUI usage and testing (CHESS-9).