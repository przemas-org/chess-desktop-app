# Stockfish Engine Integration - Technical Documentation

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Component Reference](#component-reference)
4. [Development Setup](#development-setup)
5. [Platform-Specific Notes](#platform-specific-notes)
6. [Engine Behavior and Configuration](#engine-behavior-and-configuration)
7. [Testing Strategy](#testing-strategy)
8. [Troubleshooting](#troubleshooting)
9. [Packaging Considerations](#packaging-considerations)

---

## Overview

The Chess Desktop App integrates the Stockfish chess engine to provide automated opponent play. The engine always plays Black while the human player controls White. The integration is designed to be:

- **Optional**: The app gracefully falls back to human-vs-human mode if Stockfish is unavailable
- **Robust**: Engine failures, timeouts, and crashes never corrupt game state or freeze the UI
- **Non-blocking**: All engine communication is asynchronous using Qt's event-driven architecture
- **Testable**: Clean abstractions allow testing without spawning real engine processes

### Key Design Principles

1. **Engine isolation**: The domain layer (`Game`) has no knowledge of the engine
2. **Clean abstraction**: `EngineAdapter` interface hides UCI protocol and process management
3. **Graceful degradation**: Missing or failing engines don't break the application
4. **Single source of truth**: `Game` domain model validates all moves, including engine replies

---

## Architecture

### Three-Layer Design

The Stockfish integration uses a three-layer architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                        MainWindow                           │
│  (GUI orchestration, user interaction, side locking)        │
└────────────┬────────────────────────────────┬───────────────┘
             │                                │
             │ owns                           │ owns
             ▼                                ▼
     ┌───────────────┐              ┌──────────────────┐
     │     Game      │◄─────────────│ EngineController │
     │  (domain)     │  validates   │   (coordinator)  │
     └───────────────┘    moves     └─────────┬────────┘
                                              │
                                              │ uses
                                              ▼
                                    ┌──────────────────────┐
                                    │   EngineAdapter      │
                                    │   (abstraction)      │
                                    └──────────┬───────────┘
                                              │
                                              │ implements
                                              ▼
                                ┌───────────────────────────────┐
                                │ StockfishProcessAdapter       │
                                │ (UCI protocol + QProcess)     │
                                └───────────────────────────────┘
```

### Component Responsibilities

1. **`engine_config.py`**: Platform-specific binary path resolution
2. **`gui/engine_integration.py`**: Engine abstraction and Stockfish adapter
3. **`gui/engine_controller.py`**: Coordination between Game and engine
4. **`main.py`**: Bootstrap sequence and engine initialization
5. **`gui/main_window.py`**: Side locking and move triggering

### Data Flow: Human Move → Engine Response

```
1. User clicks squares in MainWindow
   ↓
2. MainWindow validates and applies move to Game
   ↓
3. MainWindow calls EngineController.on_human_move_applied()
   ↓
4. EngineController checks: enabled? Black to move? not in-flight?
   ↓
5. EngineController exports FEN from Game
   ↓
6. EngineController requests move from EngineAdapter
   ↓
7. StockfishProcessAdapter sends UCI commands to process
   ↓
8. Stockfish computes and returns bestmove
   ↓
9. StockfishProcessAdapter emits move_ready signal
   ↓
10. EngineController receives UCI move
    ↓
11. EngineController validates by applying to Game
    ↓
12. EngineController emits engine_move_applied signal
    ↓
13. MainWindow refreshes board display
```

---

## Component Reference

### `engine_config.py` - Binary Path Resolution

**Purpose**: Centralized configuration for locating the Stockfish binary.

**Key Functions**:

```python
def get_stockfish_path() -> Optional[str]:
    """
    Returns absolute path to platform-specific Stockfish binary.
    Returns None if binary is missing or not executable.
    """

def is_stockfish_available() -> bool:
    """
    Convenience wrapper that returns True if engine is available.
    """
```

**Platform Detection**:
- Linux: `stockfish/stockfish-linux`
- Windows: `stockfish/stockfish-windows.exe`
- macOS: `stockfish/stockfish-macos`

Uses `sys.platform` for detection. Binary must be in `stockfish/` directory at project root.

**File Structure**:
```
project_root/
├── stockfish/
│   ├── stockfish-linux         (executable)
│   ├── stockfish-windows.exe   (executable)
│   └── stockfish-macos         (executable)
├── chess_app/
│   ├── engine_config.py        (← this file)
│   └── ...
```

---

### `gui/engine_integration.py` - Adapter Abstraction and Implementation

#### `EngineAdapter` (Abstract Base Class)

**Purpose**: Defines the contract for asynchronous engine communication.

**State Machine**:

```
DISABLED ──initialize()──→ INITIALIZING
                              │
                              ├──success──→ READY
                              │                │
                              │                ├──request_move()──→ BUSY
                              │                │                      │
                              │                │                      ├──success──→ READY
                              │                │                      │
                              │                │                      └──timeout/crash──→ ERROR
                              │
                              └──failure/timeout──→ ERROR (terminal)
```

**Signals**:
- `initialized()`: Engine ready to accept move requests
- `initialization_failed(error_code, message)`: Initialization failed
- `move_ready(uci_move)`: Engine returned a move (e.g., "e7e5")
- `move_failed(error_code, message)`: Request failed (timeout, crash, etc.)

**Error Codes** (`EngineErrorCode` enum):
- `INITIALIZATION_FAILED`: Process start or UCI handshake failed
- `TIMEOUT`: No response within configured timeout
- `ILLEGAL_MOVE`: Engine returned illegal move (reported by controller)
- `PROCESS_CRASHED`: Engine process terminated unexpectedly
- `INVALID_REQUEST`: API misuse (e.g., request while not READY)

**API Contract**:
- Single in-flight request: Only one `request_move()` at a time
- Engine plays Black (v1): All FEN positions must have Black to move
- State validation: `request_move()` only valid when state is READY
- No FEN validation: Assumes valid FEN from `Game.export_fen()`

#### `StockfishProcessAdapter` (Concrete Implementation)

**Purpose**: Manages long-lived Stockfish process via UCI protocol and Qt's `QProcess`.

**UCI Handshake Sequence** (on `initialize()`):
```
1. Start process: QProcess.start(stockfish_path, [])
2. Send: "uci\n"
3. Receive: "uciok" (+ ignore info lines)
4. Send: "isready\n"
5. Receive: "readyok"
6. Transition to READY state
7. Emit initialized() signal
```

**Handshake timeout**: 5000ms (terminal ERROR state if exceeded)

**Move Request Sequence** (on `request_move(fen, timeout_ms)`):
```
1. Validate state is READY
2. Send: "position fen <FEN>\n"
3. Send: "go movetime 100\n"
4. Start timeout timer (default 1000ms)
5. Parse output lines, looking for "bestmove <move>"
6. Extract UCI move from bestmove line
7. Cancel timeout timer
8. Emit move_ready(uci_move) signal
9. Transition to READY state
```

**Timeout Handling**:
- If timeout fires before bestmove received → ERROR state (terminal)
- Emit `move_failed(TIMEOUT, message)`

**Process Lifecycle**:
- Single process per session, kept alive for entire app lifetime
- Graceful shutdown: Send "quit\n", wait 1s, then kill if needed
- Unexpected exit → ERROR state, emit appropriate failure signal

**Output Parsing**:
- Buffers stdout line-by-line
- Ignores "info" lines (analysis output)
- Processes "bestmove <move> [ponder <move>]" lines
- First token after "bestmove" is the UCI move

---

### `gui/engine_controller.py` - Domain Bridge

**Purpose**: Coordinates between `Game` domain model and `EngineAdapter`.

**Responsibilities**:
1. Trigger engine queries after human moves (when Black to move)
2. Validate engine responses by applying to `Game`
3. Re-query once on illegal moves
4. Permanently disable on repeated failures
5. Enforce single in-flight request policy

**Signals**:
- `engine_move_applied()`: Move successfully applied to Game, refresh board
- `engine_disabled(reason)`: Engine permanently disabled due to errors

**Configuration** (v1):
- Engine side: `Side.BLACK` (hardcoded)
- Timeout: 1000ms (configurable per request)
- Illegal move retry: 1 attempt (2 illegal moves → permanent disable)

**State Tracking**:
- `_is_enabled`: Boolean, false after permanent disablement
- `_in_flight`: Boolean, true during pending request
- `_illegal_move_count`: Counter, reset per position

**Illegal Move Handling**:
```
First illegal move for position:
  - Increment counter
  - Immediately re-query with same FEN
  - Keep _in_flight = True

Second illegal move:
  - Clear _in_flight
  - Set _is_enabled = False
  - Emit engine_disabled(reason)
```

**Adapter Error Handling**:
- Any `move_failed` signal → permanent disablement
- Emit `engine_disabled` with error details

**Usage Pattern** (in `MainWindow`):
```python
# After human move applied:
self._game.apply_move(move)
self.update_board_from_game()
if self._engine_controller:
    self._engine_controller.on_human_move_applied()
```

---

### `main.py` - Bootstrap Sequence

**Engine Initialization Flow**:

```python
1. Create Qt application
2. Create Game instance
3. Create MainWindow
4. Call window.set_game(game)
5. Call window.update_board_from_game()

6. Get Stockfish path from engine_config
7. If path is None:
     - Log warning: binary not found
     - Continue without engine (human-vs-human mode)
   
8. If path exists:
     - Create StockfishProcessAdapter(path)
     - Connect initialized signal → window.set_engine_adapter(adapter)
     - Connect initialization_failed signal → log error
     - Call adapter.initialize() (asynchronous)

9. Show window
10. Start Qt event loop
```

**Logging**:
- Uses Python's `logging` module (stderr)
- Level: INFO
- Messages: Binary not found, initialization success/failure

**Graceful Fallback**:
- Missing binary → warning log, continue without engine
- Initialization failure → error log, continue without engine
- No crashes or exceptions propagated to user

---

### `gui/main_window.py` - Side Locking and Move Triggering

**Engine-Related Responsibilities**:

1. **Own engine components**:
   - `_engine_adapter: Optional[EngineAdapter]`
   - `_engine_controller: Optional[EngineController]`
   - `_engine_enabled: bool`

2. **Side locking** (when engine enabled):
   ```python
   # In _handle_source_selection():
   if self._engine_controller is not None and self._engine_controller.is_enabled():
       piece_side = self._game.get_piece_side(square)
       if piece_side != Side.WHITE:
           return  # Silently ignore non-White pieces
   ```

3. **Block input during engine thinking**:
   ```python
   if self._engine_controller is not None and self._engine_controller.is_in_flight():
       return  # Ignore user input while waiting for engine
   ```

4. **Trigger engine after human moves**:
   ```python
   # After successful move application:
   if self._engine_controller:
       self._engine_controller.on_human_move_applied()
   ```

5. **Respond to engine signals**:
   - `engine_move_applied` → `update_board_from_game()`
   - `engine_disabled` → update window title

**Window Title**:
- Engine enabled: "Chess Desktop App - Engine Enabled"
- No engine: "Chess Desktop App - Human vs Human"

---

## Development Setup

### 1. Obtain Stockfish Binary

Download from [stockfishchess.org](https://stockfishchess.org/download/) or build from source.

**Recommended versions**: Stockfish 15+ (tested with Stockfish 16)

### 2. Create Directory Structure

```bash
cd /home/przemas/proj/chess_desktop_app
mkdir -p stockfish
```

### 3. Place Binary

Copy/move the binary to `stockfish/` with the correct name:

**Linux**:
```bash
cp ~/Downloads/stockfish-ubuntu-x86-64-avx2 stockfish/stockfish-linux
chmod +x stockfish/stockfish-linux
```

**Windows**:
```cmd
copy Downloads\stockfish-windows-x86-64-avx2.exe stockfish\stockfish-windows.exe
```

**macOS**:
```bash
cp ~/Downloads/stockfish-macos-x86-64-avx2 stockfish/stockfish-macos
chmod +x stockfish/stockfish-macos
```

### 4. Verify Permissions

The binary must be executable. On Unix systems:

```bash
ls -l stockfish/
# Should show: -rwxr-xr-x ... stockfish-linux
```

If not executable:
```bash
chmod +x stockfish/stockfish-linux
```

### 5. Run the Application

```bash
poetry run chess-app
```

**Expected log output** (with engine):
```
INFO: Stockfish engine initialized successfully
```

**Expected log output** (without engine):
```
WARNING: Stockfish binary not found or not executable. Running in human-vs-human mode. To enable engine features, place the Stockfish binary in the 'stockfish/' directory at the project root.
```

### 6. Verify Engine is Working

- Window title should show "Chess Desktop App - Engine Enabled"
- Make a move as White (e.g., e2-e4)
- Black should respond automatically after ~100ms
- You cannot select or move Black pieces

---

## Platform-Specific Notes

### Linux

**Binary naming**: `stockfish-linux`

**Executable permission**: Required
```bash
chmod +x stockfish/stockfish-linux
```

**Common issues**:
- Missing shared libraries (rare with static builds)
- Check with: `ldd stockfish/stockfish-linux`

**Architecture**: Download appropriate build (AVX2, SSE4.2, etc.) for your CPU

### Windows

**Binary naming**: `stockfish-windows.exe` (`.exe` extension required)

**Executable permission**: Not needed (Windows doesn't use Unix permissions)

**Common issues**:
- Antivirus blocking execution
- Missing Visual C++ Redistributables (rare)

**Architecture**: Use 64-bit build unless on 32-bit Windows

### macOS

**Binary naming**: `stockfish-macos`

**Executable permission**: Required
```bash
chmod +x stockfish/stockfish-macos
```

**Gatekeeper issues**: macOS may block unsigned binaries

**Workaround**:
```bash
# Remove quarantine attribute
xattr -d com.apple.quarantine stockfish/stockfish-macos

# Or use System Preferences:
# System Preferences → Security & Privacy → Allow
```

**Architecture**:
- Intel Macs: Use x86-64 build
- Apple Silicon (M1/M2): Use ARM build or Rosetta-compatible x86-64

---

## Engine Behavior and Configuration

### v1 Constraints

- **Engine side**: Always Black (hardcoded in `EngineController`)
- **User side**: Always White
- **Side switching**: Not supported in v1
- **Hint mode**: Not supported in v1
- **Analysis mode**: Not supported in v1

### UCI Parameters

**Search time**: `go movetime 100`
- Engine searches for exactly 100 milliseconds
- Provides fast responses for interactive play
- Can be changed in `EngineController.on_human_move_applied()` (hardcoded)

**Response timeout**: 1000ms (1 second)
- Total time allowed for engine to respond
- Includes communication overhead + thinking time
- Can be changed in `EngineController.on_human_move_applied()` parameter
- Exceeding timeout → permanent engine disablement

**Handshake timeout**: 5000ms (5 seconds)
- Time allowed for UCI initialization
- Defined in `StockfishProcessAdapter.HANDSHAKE_TIMEOUT_MS`
- Exceeding timeout → initialization failure

### Configuration Constants

All located in source code (no user-facing config):

**Binary paths**: `engine_config.py`
```python
project_root / 'stockfish' / binary_name
```

**Timeouts**: `gui/engine_integration.py`
```python
HANDSHAKE_TIMEOUT_MS = 5000  # StockfishProcessAdapter
```

**Timeouts**: `gui/engine_controller.py`
```python
timeout_ms=1000  # request_move() parameter
```

**Search time**: `gui/engine_controller.py`
```python
"go movetime 100"  # UCI command (hardcoded)
```

**Engine side**: `gui/engine_controller.py`
```python
self._engine_side = Side.BLACK
```

**Illegal move retries**: `gui/engine_controller.py`
```python
if self._illegal_move_count < 2:  # 1 retry
```

---

## Testing Strategy

### Philosophy

- **No real processes in tests**: All tests use mock implementations
- **Fast execution**: No waiting for engine responses
- **Deterministic**: Tests control exactly what the "engine" returns
- **Coverage**: Success cases, failures, timeouts, edge cases

### Test Utilities

**`tests/engine_fakes.py`**:
- `FakeEngineAdapter`: Mock implementation of `EngineAdapter`
- Records all method calls for verification
- Allows simulation of any engine behavior
- Supports delayed responses for timing tests

**Example usage**:
```python
from tests.engine_fakes import FakeEngineAdapter

fake = FakeEngineAdapter()
fake.initialize()
fake.simulate_init_success()  # Manually trigger success

fake.request_move(fen, timeout_ms=1000)
fake.simulate_move_response("e7e5")  # Manually provide response

# Verify calls
calls = fake.get_call_log()
assert calls[0] == ("initialize", ())
```

### Test Coverage

**`test_engine_abstraction.py`**:
- `EngineAdapter` state machine transitions
- Signal emission on success/failure
- Timeout handling
- Process crash scenarios

**`test_engine_controller.py`**:
- Move validation logic
- Illegal move retry (1 attempt)
- Permanent disablement on repeated failures
- In-flight request enforcement

**`test_stockfish_adapter.py`**:
- UCI handshake sequence
- Move request/response parsing
- Timeout behavior
- Process lifecycle management

**`test_gui_integration.py`**:
- End-to-end flow: user move → engine response → board update
- Side locking when engine enabled
- Input blocking during engine thinking

**`test_startup_integration.py`**:
- Bootstrap sequence
- Graceful fallback when binary missing
- Initialization success/failure paths

### Running Tests

```bash
# All tests
poetry run pytest

# With coverage
poetry run pytest --cov=chess_app

# Specific test file
poetry run pytest tests/test_engine_controller.py

# Verbose output
poetry run pytest -v
```

**Note**: Tests skip GUI tests in headless environments (CI/CD).

---

## Troubleshooting

### Binary Not Found

**Symptom**: Log shows "Stockfish binary not found or not executable"

**Checks**:
1. Verify file exists: `ls -l stockfish/`
2. Check filename matches platform:
   - Linux: `stockfish-linux`
   - Windows: `stockfish-windows.exe`
   - macOS: `stockfish-macos`
3. Check project root (not inside `chess_app/`)

**Fix**: Place correctly named binary in `stockfish/` directory

### Binary Not Executable (Unix)

**Symptom**: Same as above, or initialization timeout

**Check**:
```bash
ls -l stockfish/stockfish-linux
# Look for 'x' permission: -rwxr-xr-x
```

**Fix**:
```bash
chmod +x stockfish/stockfish-linux
```

### Initialization Timeout

**Symptom**: Log shows "UCI handshake timed out after 5000ms"

**Possible causes**:
1. Binary is incompatible with system
2. Binary is corrupted
3. Missing shared libraries (Linux)
4. Gatekeeper blocking execution (macOS)

**Diagnosis**:
```bash
# Try running manually
cd stockfish
./stockfish-linux
# Should show: Stockfish 16 by the Stockfish developers

# Type: uci
# Should respond with engine info and "uciok"
```

**Linux shared library check**:
```bash
ldd stockfish/stockfish-linux
# Should show all dependencies resolved
```

**macOS Gatekeeper**:
```bash
xattr -d com.apple.quarantine stockfish/stockfish-macos
```

### Engine Response Timeout

**Symptom**: Move timeout after human move, engine disabled

**Log example**: "Engine error (timeout): Engine did not respond within 1000ms"

**Causes**:
1. Binary crashed during move calculation
2. Binary is unresponsive
3. Timeout too short for slow systems

**Diagnosis**: Increase timeout in `EngineController.on_human_move_applied()`:
```python
self._adapter.request_move(fen, timeout_ms=5000)  # Increase from 1000
```

### Illegal Move Returned

**Symptom**: Engine disabled with "Engine returned illegal move twice: <move>"

**Causes**:
1. Bug in Stockfish (very rare)
2. FEN/position mismatch (bug in our code)
3. Corrupted binary

**Diagnosis**:
1. Check the FEN that was sent (add logging)
2. Verify move is actually illegal in that position
3. Try different Stockfish version

### Process Crashes

**Symptom**: "Stockfish process crashed unexpectedly"

**Causes**:
1. Binary incompatible with system architecture
2. Corrupted download
3. System resource limits

**Fix**:
1. Re-download binary from official source
2. Verify SHA256 checksum if provided
3. Try different build variant (e.g., non-AVX2 if AVX2 crashes)

### Window Title Shows "Human vs Human"

**Not an error**: This is expected when:
- Stockfish binary not found
- Initialization failed
- Engine disabled due to errors

**To enable engine**:
1. Place binary correctly
2. Restart application
3. Check logs for specific error

---

## Packaging Considerations

### Open Questions (Out of Scope for v1)

The following packaging topics are **not yet implemented** and require future decisions:

#### 1. Binary Distribution Strategy

**Question**: How should Stockfish binaries be distributed?

**Options**:
- **Bundle in package**: Include binaries for all platforms in distribution
  - Pros: Works out-of-box, no user setup
  - Cons: Large package size, license implications
- **User-provided**: User downloads and installs Stockfish separately
  - Pros: Smaller package, no license concerns
  - Cons: Manual setup required, user confusion
- **Download on first run**: App downloads binary automatically
  - Pros: Balance of convenience and size
  - Cons: Network dependency, security verification needed

**Current state**: Developer must manually place binary

#### 2. Platform-Specific Packaging

**Question**: What packaging format for each platform?

**Options**:
- **PyInstaller**: Cross-platform, bundles Python + dependencies
- **AppImage** (Linux): Self-contained, no installation
- **MSI/Installer** (Windows): Standard Windows installer
- **DMG** (macOS): Standard macOS disk image
- **Platform stores**: Snap, Flatpak, Windows Store, Mac App Store

**Challenges**:
- Binary path resolution in frozen apps
- Executable permissions in packaged formats
- Code signing for macOS/Windows

**Current state**: Runs from Poetry environment only

#### 3. Binary Path Resolution in Packaged Apps

**Question**: How to locate binary when app is frozen/packaged?

**Consideration**: `__file__` and relative paths behave differently when packaged

**Potential solutions**:
- Use `sys._MEIPASS` (PyInstaller)
- Use `importlib.resources` for data files
- Environment variable override for binary path

**Current state**: Relative path from `engine_config.py` location

#### 4. Code Signing and Notarization

**Question**: How to handle unsigned binaries?

**Platforms affected**:
- **macOS**: Gatekeeper blocks unsigned binaries
- **Windows**: SmartScreen warnings for unsigned executables

**Options**:
- Sign Stockfish binary ourselves (requires certificate)
- Bundle pre-signed official binary
- Document workaround for users (xattr, bypass warnings)

**Current state**: Developer must manually bypass security warnings

#### 5. License Compliance

**Question**: Can we legally distribute Stockfish?

**Stockfish license**: GPL v3

**Implications**:
- Can distribute, but our app may need compatible license
- Must provide source code and build instructions
- Attribute Stockfish authors appropriately

**Current state**: Binary not included in repository

#### 6. Multi-Architecture Support

**Question**: Which CPU architectures to support?

**Stockfish variants**:
- AVX2, SSE4.2, SSE3, generic (x86-64)
- ARM builds for Apple Silicon, Raspberry Pi

**Approaches**:
- Bundle multiple binaries, detect at runtime
- Bundle single "best compatibility" build
- Let user choose variant

**Current state**: Developer chooses appropriate binary for their system

#### 7. Updates and Versioning

**Question**: How to handle Stockfish updates?

**Considerations**:
- New Stockfish versions release regularly
- Performance improvements and bug fixes
- Breaking changes (rare but possible)

**Current state**: Manual binary replacement

---

### Recommendations for Future Implementation

When ready to tackle packaging:

1. **Start with PyInstaller**: Cross-platform, well-documented
2. **Bundle generic builds**: Lower performance but maximum compatibility
3. **Document manual setup**: Clear instructions for user-provided binaries
4. **Implement path override**: Environment variable for custom binary location
5. **Add binary verification**: SHA256 checksums for bundled binaries
6. **Consult legal**: Confirm GPL compliance for distribution method

---

## Summary

The Stockfish integration provides robust, optional engine play through a clean three-layer architecture:

1. **`EngineAdapter`**: Abstract interface for asynchronous engine communication
2. **`StockfishProcessAdapter`**: UCI protocol + QProcess implementation
3. **`EngineController`**: Domain bridge with validation and error handling

**For development**:
- Place platform-named binary in `stockfish/` directory
- Make executable on Unix systems
- Run normally with `poetry run chess-app`

**For testing**:
- Use `FakeEngineAdapter` from `tests/engine_fakes.py`
- No real processes in automated tests
- Run with `poetry run pytest`

**For production packaging**:
- Multiple open questions remain (see Packaging Considerations)
- Current implementation supports development workflow only

---

## Further Reading

- [Stockfish Official Site](https://stockfishchess.org/)
- [UCI Protocol Specification](https://www.shredderchess.com/download/div/uci.zip)
- [Python-Chess Documentation](https://python-chess.readthedocs.io/)
- [Qt for Python (PySide6) Documentation](https://doc.qt.io/qtforpython/)

## Related Files

- `chess_app/engine_config.py` - Binary path resolution
- `chess_app/gui/engine_integration.py` - Adapter abstraction and implementation
- `chess_app/gui/engine_controller.py` - Domain coordination
- `chess_app/main.py` - Bootstrap sequence
- `chess_app/gui/main_window.py` - GUI integration
- `tests/engine_fakes.py` - Test utilities


