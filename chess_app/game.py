"""
Core domain types for the chess game model.

This module defines domain-level abstractions for the chess game,
including game status, move representation, and custom exceptions.
The python-chess library types remain internal to this module and
are not exposed to the rest of the application.
"""

import chess
import chess.pgn
import io
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Union


class GameStatus(Enum):
    """Represents the current state of a chess game.
    
    Attributes:
        ONGOING: The game is in progress with no special conditions.
        CHECK: The current player's king is under attack.
        CHECKMATE: The current player's king is in checkmate (game over).
        STALEMATE: The current player has no legal moves but is not in check (draw).
        DRAW_50_MOVE: Game is drawn due to the fifty-move rule.
        DRAW_INSUFFICIENT_MATERIAL: Game is drawn due to insufficient mating material.
        DRAW_OTHER: Game is drawn for other reasons (e.g., threefold repetition, agreement).
    """
    ONGOING = "ongoing"
    CHECK = "check"
    CHECKMATE = "checkmate"
    STALEMATE = "stalemate"
    DRAW_50_MOVE = "draw_50_move"
    DRAW_INSUFFICIENT_MATERIAL = "draw_insufficient_material"
    DRAW_OTHER = "draw_other"


class Side(Enum):
    """Represents which side (color) is to move.
    
    Attributes:
        WHITE: White pieces.
        BLACK: Black pieces.
    """
    WHITE = "white"
    BLACK = "black"


@dataclass
class Move:
    """
    Data transfer object representing a chess move.
    
    This class wraps move information from the python-chess library,
    providing a clean domain-level interface for move representation.
    
    Attributes:
        uci: The move in UCI (Universal Chess Interface) notation (e.g., "e2e4").
        san: The move in SAN (Standard Algebraic Notation), if available (e.g., "e4").
        from_square: The starting square in algebraic notation (e.g., "e2").
        to_square: The destination square in algebraic notation (e.g., "e4").
        promotion: The piece to promote to, if this is a pawn promotion move
                  (e.g., "q" for queen, "r" for rook, etc.). None otherwise.
    """
    uci: str
    san: Optional[str]
    from_square: str
    to_square: str
    promotion: Optional[str] = None


class IllegalMoveError(Exception):
    """
    Exception raised when an illegal chess move is attempted.
    
    This is raised when a move violates chess rules or is not valid
    in the current game position.
    """
    pass


class InvalidFenError(Exception):
    """
    Exception raised when an invalid FEN (Forsyth-Edwards Notation) string is provided.
    
    This is raised when attempting to initialize or set a game position
    from a malformed or invalid FEN string.
    """
    pass


class InvalidPgnError(Exception):
    """
    Exception raised when an invalid PGN (Portable Game Notation) string is provided.
    
    This is raised when attempting to parse or import a game from
    a malformed or invalid PGN string.
    """
    pass


class Game:
    """
    Core game state manager and entry point for UI interaction with chess logic.
    
    This class serves as a thin wrapper around python-chess.Board, providing a clean
    domain-level interface for the UI layer. It encapsulates the chess board state
    and maintains a history of moves using domain Move objects.
    
    The Game class is the primary interface for the UI to interact with game state.
    Internal python-chess types (chess.Board, chess.Move, etc.) are NOT exposed
    directly to other parts of the application - all interactions should go through
    this Game class and its domain types.
    
    Attributes:
        _board: The internal python-chess Board instance that manages chess rules
                and position state. This is kept private and not exposed to callers.
        _move_history: A list of domain Move objects representing all moves made
                      in this game. Starts empty and will be populated as moves
                      are applied (in future implementations).
    
    Example:
        # Create a new game with standard starting position
        game = Game()
        
        # Create a game from a specific position
        game = Game.from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
    """
    
    def __init__(self) -> None:
        """
        Initialize a new chess game with the standard starting position.
        
        Creates a new game with pieces arranged in the traditional chess
        opening position (all pieces on their starting squares, white to move).
        The move history starts empty.
        """
        self._board: chess.Board = chess.Board()
        self._move_history: list[Move] = []
        self._result: Optional[str] = None
    
    @classmethod
    def from_fen(cls, fen: str) -> "Game":
        """
        Create a Game instance from a FEN (Forsyth-Edwards Notation) string.
        
        FEN is a standard notation for describing a chess position. This method
        constructs a Game with the board position specified by the FEN string.
        The move history starts empty regardless of the position.
        
        Args:
            fen: A valid FEN string representing the chess position. This should
                 include all six FEN fields: piece placement, active color,
                 castling rights, en passant square, halfmove clock, and
                 fullmove number.
        
        Returns:
            A new Game instance with the board position set according to the
            provided FEN string.
        
        Raises:
            InvalidFenError: If the provided FEN string is malformed or invalid.
                            The exception message will include details about
                            what was wrong with the FEN string.
        
        Example:
            # Standard starting position
            game = Game.from_fen("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
            
            # Position after 1.e4
            game = Game.from_fen("rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1")
        """
        try:
            board = chess.Board(fen=fen)
        except ValueError as e:
            raise InvalidFenError(
                f"Invalid FEN string provided: '{fen}'. "
                f"Error details: {str(e)}"
            ) from e
        
        # Create a new Game instance and set its internal state
        game = cls.__new__(cls)
        game._board = board
        game._move_history = []
        game._result = None
        return game
    
    @classmethod
    def from_pgn(cls, pgn_str: str) -> "Game":
        """
        Create a Game instance from a PGN (Portable Game Notation) string.
        
        PGN is a standard notation for recording chess games. This method parses
        a PGN string containing a single game and constructs a Game instance by
        replaying all moves from the initial position.
        
        Args:
            pgn_str: A valid PGN string representing a single chess game. This should
                    include move text and may include headers (Event, Site, Date, etc.).
        
        Returns:
            A new Game instance with the board position after all moves have been
            replayed and the move history populated with all moves from the PGN.
        
        Raises:
            InvalidPgnError: If the provided PGN string is malformed, invalid, or
                           empty. The exception message will include details about
                           what was wrong with the PGN string.
        
        Example:
            # Simple game
            pgn = '''
            [Event "Example Game"]
            [Result "1-0"]
            
            1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 1-0
            '''
            game = Game.from_pgn(pgn)
            
            # Access game state
            history = game.get_history()
            print(f"Moves played: {len(history)}")  # Prints: Moves played: 6
        """
        try:
            # Parse the PGN string using StringIO as a file-like object
            pgn_io = io.StringIO(pgn_str)
            parsed_game = chess.pgn.read_game(pgn_io)
            
            # Validate that a game was successfully parsed
            if parsed_game is None:
                raise InvalidPgnError(
                    "Failed to parse PGN: no valid game found in the provided string"
                )
            
            # Extract the result from headers for later use in export
            result = parsed_game.headers.get("Result", "*")
            
            # Create a new Game instance starting from initial position
            game = cls.__new__(cls)
            game._board = chess.Board()
            game._move_history = []
            game._result = result
            
            # Replay all moves to build move history and reach final position
            temp_board = chess.Board()
            for chess_move in parsed_game.mainline_moves():
                # Generate SAN before pushing (board state will change)
                san = temp_board.san(chess_move)
                
                # Get move details
                uci = chess_move.uci()
                from_square = chess.square_name(chess_move.from_square)
                to_square = chess.square_name(chess_move.to_square)
                
                # Handle promotion
                promotion = None
                if chess_move.promotion is not None:
                    promotion = chess.piece_symbol(chess_move.promotion)
                
                # Create domain Move and add to history
                domain_move = Move(
                    uci=uci,
                    san=san,
                    from_square=from_square,
                    to_square=to_square,
                    promotion=promotion
                )
                game._move_history.append(domain_move)
                
                # Push move to temporary board
                temp_board.push(chess_move)
            
            # Set the final board position
            game._board = temp_board
            
            return game
            
        except InvalidPgnError:
            # Re-raise our custom exception as-is
            raise
        except Exception as e:
            # Catch any other parsing errors and convert to InvalidPgnError
            raise InvalidPgnError(
                f"Failed to parse PGN: {str(e)}"
            ) from e
    
    def get_legal_moves(self) -> list[Move]:
        """
        Get all legal moves in the current position.
        
        Queries the underlying python-chess Board for all legal moves and converts
        them into domain Move objects suitable for UI consumption.
        
        Returns:
            A list of Move instances representing all legal moves in the current
            position. Each Move includes UCI notation, SAN notation, from/to squares,
            and promotion information where applicable.
        
        Example:
            game = Game()
            legal_moves = game.get_legal_moves()
            for move in legal_moves:
                print(f"{move.san}: {move.uci}")
        """
        moves = []
        for chess_move in self._board.legal_moves:
            # Convert python-chess move to domain Move
            uci = chess_move.uci()
            san = self._board.san(chess_move)
            from_square = chess.square_name(chess_move.from_square)
            to_square = chess.square_name(chess_move.to_square)
            
            # Handle promotion
            promotion = None
            if chess_move.promotion is not None:
                promotion = chess.piece_symbol(chess_move.promotion)
            
            moves.append(Move(
                uci=uci,
                san=san,
                from_square=from_square,
                to_square=to_square,
                promotion=promotion
            ))
        
        return moves
    
    def apply_move(self, move: Union[Move, str]) -> None:
        """
        Apply a move to the game.
        
        Accepts either a domain Move object or a UCI string, validates the move
        is legal in the current position, and applies it to the board. The move
        is added to the internal move history.
        
        Args:
            move: Either a domain Move object or a UCI string (e.g., "e2e4" or "e7e8q"
                 for promotion moves).
        
        Raises:
            IllegalMoveError: If the move is not legal in the current position or
                            cannot be parsed as a valid UCI move.
        
        Example:
            game = Game()
            # Apply using UCI string
            game.apply_move("e2e4")
            # Apply using Move object
            moves = game.get_legal_moves()
            game.apply_move(moves[0])
        """
        # Extract UCI string from Move object or use string directly
        if isinstance(move, Move):
            uci_str = move.uci
        else:
            uci_str = move
        
        # Parse UCI string to python-chess move
        try:
            chess_move = chess.Move.from_uci(uci_str)
        except ValueError as e:
            raise IllegalMoveError(
                f"Invalid UCI move string: '{uci_str}'. "
                f"Error details: {str(e)}"
            ) from e
        
        # Validate the move is legal
        if chess_move not in self._board.legal_moves:
            raise IllegalMoveError(
                f"Move '{uci_str}' is not legal in the current position. "
                f"Current FEN: {self._board.fen()}"
            )
        
        # Generate SAN before pushing the move (board state will change)
        san = self._board.san(chess_move)
        
        # Apply the move to the board
        self._board.push(chess_move)
        
        # Create domain Move and add to history
        from_square = chess.square_name(chess_move.from_square)
        to_square = chess.square_name(chess_move.to_square)
        promotion = None
        if chess_move.promotion is not None:
            promotion = chess.piece_symbol(chess_move.promotion)
        
        domain_move = Move(
            uci=uci_str,
            san=san,
            from_square=from_square,
            to_square=to_square,
            promotion=promotion
        )
        self._move_history.append(domain_move)
    
    def undo(self) -> None:
        """
        Undo the last move.
        
        Reverts the board state to before the last move was applied and removes
        that move from the move history. Safe to call repeatedly until reaching
        the initial position.
        
        If there are no moves to undo (history is empty), this method does nothing
        (no-op behavior).
        
        Example:
            game = Game()
            game.apply_move("e2e4")
            game.apply_move("e7e5")
            game.undo()  # Reverts e7e5
            game.undo()  # Reverts e2e4
            game.undo()  # Safe no-op, already at starting position
        """
        # Check if there are moves to undo
        if len(self._move_history) > 0:
            # Revert the board state
            self._board.pop()
            # Remove the last move from history
            self._move_history.pop()
    
    def get_history(self) -> tuple[Move, ...]:
        """
        Get a read-only view of the move history.
        
        Returns an immutable tuple containing all moves that have been applied
        in this game, in chronological order.
        
        Returns:
            A tuple of Move objects representing the complete move history.
            The tuple is immutable to prevent external modification of the
            game's internal state.
        
        Example:
            game = Game()
            game.apply_move("e2e4")
            game.apply_move("e7e5")
            history = game.get_history()
            print(f"Moves played: {len(history)}")  # Prints: Moves played: 2
            for move in history:
                print(move.san)  # Prints: e4, e5
        """
        return tuple(self._move_history)
    
    def get_status(self) -> GameStatus:
        """
        Get the current game status.
        
        Inspects the underlying chess board to determine the current state of the game,
        checking for terminal conditions (checkmate, stalemate, draws) and non-terminal
        conditions (check, ongoing).
        
        The method checks conditions in priority order:
        1. Terminal conditions that end the game (checkmate, stalemate, draws)
        2. Non-terminal special conditions (check)
        3. Normal ongoing play
        
        Returns:
            A GameStatus enum value representing the current state:
            - CHECKMATE: The current player is in checkmate (game over, opponent wins)
            - STALEMATE: The current player has no legal moves but is not in check (draw)
            - DRAW_INSUFFICIENT_MATERIAL: Neither side has enough material to checkmate (draw)
            - DRAW_50_MOVE: The fifty-move rule applies or can be claimed (draw)
            - DRAW_OTHER: Another draw condition applies (e.g., threefold repetition)
            - CHECK: The current player's king is under attack but the game continues
            - ONGOING: Normal play with no special conditions
        
        Note:
            This method is read-only and does not mutate the game state.
            It is cheap to call repeatedly as it only queries board properties.
        
        Example:
            game = Game()
            game.apply_move("f2f3")
            game.apply_move("e7e6")
            game.apply_move("g2g4")
            game.apply_move("d8h4")  # Fool's mate
            status = game.get_status()
            assert status == GameStatus.CHECKMATE
        """
        # Check terminal conditions first (game over states)
        if self._board.is_checkmate():
            return GameStatus.CHECKMATE
        
        if self._board.is_stalemate():
            return GameStatus.STALEMATE
        
        if self._board.is_insufficient_material():
            return GameStatus.DRAW_INSUFFICIENT_MATERIAL
        
        # Check fifty-move rule (both actual trigger and claimable)
        if self._board.is_fifty_moves() or self._board.can_claim_fifty_moves():
            return GameStatus.DRAW_50_MOVE
        
        # Check threefold repetition
        if self._board.can_claim_threefold_repetition():
            return GameStatus.DRAW_OTHER
        
        # Check non-terminal conditions
        if self._board.is_check():
            return GameStatus.CHECK
        
        # Normal ongoing play
        return GameStatus.ONGOING
    
    def get_side_to_move(self) -> Side:
        """
        Get which side (color) is to move next.
        
        Returns the color of the side whose turn it is to make a move.
        This is derived from the board's turn indicator.
        
        Returns:
            Side.WHITE if it is White's turn to move, Side.BLACK if it is Black's turn.
        
        Note:
            This method is read-only and does not mutate the game state.
            It is cheap to call repeatedly as it only queries a board property.
        
        Example:
            game = Game()
            assert game.get_side_to_move() == Side.WHITE
            game.apply_move("e2e4")
            assert game.get_side_to_move() == Side.BLACK
        """
        return Side.WHITE if self._board.turn else Side.BLACK
    
    def get_piece_side(self, square: str) -> Optional[Side]:
        """
        Get which side (color) occupies a given square.
        
        Queries the board to determine if a square contains a piece and, if so,
        which side that piece belongs to. This helper allows the GUI layer to
        enforce side locking and make engine decisions without parsing FEN or
        duplicating chess logic.
        
        Args:
            square: Algebraic square notation (e.g., "e4", "a1", "h8").
                   Case-insensitive.
        
        Returns:
            Side.WHITE if a white piece occupies the square.
            Side.BLACK if a black piece occupies the square.
            None if the square is empty or if the square notation is invalid.
        
        Note:
            This method is read-only and does not mutate the game state.
            It is cheap to call repeatedly as it only queries board state.
            Invalid square strings (e.g., "z9", "invalid") return None gracefully
            rather than raising an exception.
        
        Example:
            game = Game()
            # Starting position
            assert game.get_piece_side("e2") == Side.WHITE  # White pawn
            assert game.get_piece_side("e7") == Side.BLACK  # Black pawn
            assert game.get_piece_side("e4") is None        # Empty square
            
            # After moving white pawn
            game.apply_move("e2e4")
            assert game.get_piece_side("e2") is None        # Now empty
            assert game.get_piece_side("e4") == Side.WHITE  # Pawn moved here
            
            # Invalid squares return None
            assert game.get_piece_side("z9") is None
            assert game.get_piece_side("invalid") is None
        """
        try:
            # Normalize to lowercase (chess.parse_square expects lowercase)
            square_lower = square.lower()
            
            # Convert algebraic notation to python-chess square index
            square_idx = chess.parse_square(square_lower)
            
            # Query the piece at this square
            piece = self._board.piece_at(square_idx)
            
            # If no piece, return None
            if piece is None:
                return None
            
            # Return the side based on piece color
            # python-chess uses True for White, False for Black
            return Side.WHITE if piece.color else Side.BLACK
            
        except (ValueError, AttributeError):
            # ValueError: invalid square string (e.g., "z9", "invalid")
            # AttributeError: malformed input that can't be processed
            return None
    
    def get_fullmove_number(self) -> int:
        """
        Get the current full-move number.
        
        Returns the full-move number from the FEN position. This counter starts at 1
        and increments after Black's move. In other words, after both White and Black
        have each made one move, the full-move number becomes 2.
        
        Returns:
            The current full-move number (starts at 1).
        
        Note:
            This method is read-only and does not mutate the game state.
            It is cheap to call repeatedly as it only queries a board property.
        
        Example:
            game = Game()
            assert game.get_fullmove_number() == 1
            game.apply_move("e2e4")
            assert game.get_fullmove_number() == 1  # Still move 1 (Black hasn't moved)
            game.apply_move("e7e5")
            assert game.get_fullmove_number() == 2  # Now move 2
        """
        return self._board.fullmove_number
    
    def get_halfmove_clock(self) -> int:
        """
        Get the current half-move clock.
        
        Returns the half-move clock (also known as the fifty-move counter) from the
        FEN position. This counter tracks the number of half-moves (plies) since the
        last pawn move or capture. It is used to enforce the fifty-move rule: if this
        counter reaches 100 (meaning 50 full moves), either player can claim a draw.
        
        The counter resets to 0 after any pawn move or capture.
        
        Returns:
            The current half-move clock value (0 or higher).
        
        Note:
            This method is read-only and does not mutate the game state.
            It is cheap to call repeatedly as it only queries a board property.
        
        Example:
            game = Game()
            assert game.get_halfmove_clock() == 0
            game.apply_move("g1f3")  # Knight move, no pawn move or capture
            assert game.get_halfmove_clock() == 1
            game.apply_move("g8f6")
            assert game.get_halfmove_clock() == 2
            game.apply_move("e2e4")  # Pawn move, resets counter
            assert game.get_halfmove_clock() == 0
        """
        return self._board.halfmove_clock
    
    def export_fen(self) -> str:
        """
        Export the current position as a FEN string.
        
        Returns the complete FEN (Forsyth-Edwards Notation) representation of the
        current board position, including all six FEN fields: piece placement,
        active color, castling rights, en passant square, halfmove clock, and
        fullmove number.
        
        This method can be used to save the current game state or to create
        snapshots at specific points during gameplay. The exported FEN can later
        be used with Game.from_fen() to recreate the exact position.
        
        Returns:
            A FEN string representing the current position.
        
        Note:
            This method is read-only and does not mutate the game state.
            The exported FEN will always represent a valid chess position that
            can be re-imported using Game.from_fen().
        
        Example:
            game = Game()
            fen = game.export_fen()
            # Starting position FEN:
            # "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
            
            game.apply_move("e2e4")
            fen = game.export_fen()
            # After 1.e4:
            # "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
            
            # Round-trip: export and re-import produces equivalent position
            game2 = Game.from_fen(fen)
            assert game2.export_fen() == fen
        """
        return self._board.fen()
    
    def export_pgn(self, headers: Optional[dict[str, str]] = None) -> str:
        """
        Export the game as a PGN (Portable Game Notation) string.
        
        Constructs a PGN string from the internal move history and optional header
        metadata. The Result header is automatically determined from the current
        game state unless explicitly provided in the headers parameter.
        
        Args:
            headers: Optional dictionary of PGN headers to include in the exported
                    game. Common headers include Event, Site, Date, Round, White,
                    Black, and Result. If not provided or if certain standard headers
                    are missing, default values will be used.
        
        Returns:
            A PGN string representing the complete game with headers and moves.
        
        Note:
            This method is read-only and does not mutate the game state.
            The PGN will include all moves from the move history, and the Result
            header will be automatically determined if not explicitly provided.
        
        Example:
            game = Game()
            game.apply_move("e2e4")
            game.apply_move("e7e5")
            
            # Export with default headers
            pgn = game.export_pgn()
            
            # Export with custom headers
            pgn = game.export_pgn({
                "Event": "World Championship",
                "Site": "London",
                "Date": "2024.01.15",
                "White": "Player 1",
                "Black": "Player 2"
            })
            
            # Round-trip: export and re-import preserves game state
            pgn = game.export_pgn()
            game2 = Game.from_pgn(pgn)
            assert game2.export_fen() == game.export_fen()
        """
        # Create a new PGN game
        pgn_game = chess.pgn.Game()
        
        # Set default headers
        pgn_game.headers["Event"] = "?"
        pgn_game.headers["Site"] = "?"
        pgn_game.headers["Date"] = "????.??.??"
        pgn_game.headers["Round"] = "?"
        pgn_game.headers["White"] = "?"
        pgn_game.headers["Black"] = "?"
        
        # Merge user-provided headers
        if headers:
            for key, value in headers.items():
                pgn_game.headers[key] = value
        
        # Determine the result if not explicitly provided by user
        if not headers or "Result" not in headers:
            if self._result is not None:
                # Use result from imported PGN
                pgn_game.headers["Result"] = self._result
            else:
                # Derive result from current board state
                status = self.get_status()
                if status == GameStatus.CHECKMATE:
                    # Determine winner based on whose turn it is (they lost)
                    if self._board.turn:  # White to move means White is in checkmate
                        pgn_game.headers["Result"] = "0-1"
                    else:  # Black to move means Black is in checkmate
                        pgn_game.headers["Result"] = "1-0"
                elif status in (GameStatus.STALEMATE, GameStatus.DRAW_50_MOVE,
                              GameStatus.DRAW_INSUFFICIENT_MATERIAL, GameStatus.DRAW_OTHER):
                    pgn_game.headers["Result"] = "1/2-1/2"
                else:
                    # Game is ongoing or in check
                    pgn_game.headers["Result"] = "*"
        
        # Add moves to the PGN game
        node = pgn_game
        for domain_move in self._move_history:
            # Convert domain Move back to chess.Move using UCI
            chess_move = chess.Move.from_uci(domain_move.uci)
            node = node.add_variation(chess_move)
        
        # Export to string using StringIO
        exporter = chess.pgn.StringExporter(headers=True, variations=True, comments=True)
        pgn_string = pgn_game.accept(exporter)
        
        return pgn_string
