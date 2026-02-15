### Stockfish Engine Integration

The application includes optional Stockfish chess engine integration. When enabled, the engine plays as Black while the human player controls White.

**Quick Start:**
1. Download Stockfish for your platform from [stockfishchess.org](https://stockfishchess.org/download/)
2. Create a `stockfish/` directory at the project root
3. Place the binary in the directory with the correct name:
   - Linux: `stockfish-linux`
   - Windows: `stockfish-windows.exe`
   - macOS: `stockfish-macos`
4. Make it executable (Unix systems):
   ```bash
   chmod +x stockfish/stockfish-linux  # or stockfish-macos
   ```
5. Run normally: `poetry run chess-app`

**Without Engine:**

The app automatically falls back to human-vs-human mode if the Stockfish binary is not found or fails to initialize. You'll see a log message indicating the mode.

**For detailed technical documentation**, including architecture, development setup, testing, troubleshooting, and packaging considerations, see **[docs/stockfish_integration.md](docs/stockfish_integration.md)**.
