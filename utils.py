# Colour constants
WHITE = 1
BLACK = -1

# Board integer representation (white = +ve, black = -ve)
EMPTY  = 0
PAWN   = 1
KNIGHT = 2
BISHOP = 3
ROOK   = 4
QUEEN  = 5
KING   = 6

PIECES = {PAWN: "P", KNIGHT: "N", BISHOP: "B", ROOK: "R", QUEEN: "Q", KING: "K"}

# Initial chess board setup
START_POS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# Parse FEN string into board representation and game state
def parse_fen(fen: str) -> tuple[list[list[int]], tuple[int, int], tuple[int, int], tuple[int, int] | None, int]:
    parts = fen.split()
    if len(parts) < 4:
        raise ValueError("Invalid FEN")
    board_part, side, castling, ep = parts[:4]
    board: list[list[int]] = []

    fen_map = {
        'P': PAWN,  'N': KNIGHT,  'B': BISHOP,  'R': ROOK,  'Q': QUEEN,  'K': KING,
        'p': -PAWN, 'n': -KNIGHT, 'b': -BISHOP, 'r': -ROOK, 'q': -QUEEN, 'k': -KING,
    }

    # FEN ranks: 8 to 1
    for fen_rank, row in enumerate(board_part.split('/')):
        board.append([EMPTY] * 8)  # create the row first
        file = 0
        for ch in row:
            if ch.isdigit():
                file += int(ch)
            else:
                board[fen_rank][file] = fen_map[ch]
                file += 1
        # optional safety check (can remove for zero overhead)
        if file != 8:
            raise ValueError("Invalid FEN rank")
    # Flip so board[0][0] == a1 (white side) (cartesian coordinates)
    board = board[::-1]
    # Side to move
    sd = WHITE if side == 'w' else BLACK
    # Castling rights
    wc = (1 if 'Q' in castling else 0, 1 if 'K' in castling else 0)
    bc = (1 if 'q' in castling else 0, 1 if 'k' in castling else 0)
    # En passant
    if ep == '-':
        ep = None
    else:
        file = ord(ep[0]) - ord('a')
        rank = int(ep[1]) - 1  # rank 1 -> index 0
        ep = (rank, file)
    return board, wc, bc, ep, sd

def move_alg(move):
    # Long algebraic notation (e.g. "Ng8-f6", "e7-e6", "Nb1xc3")
    uci_str = move.uci()
    src_sq, dst_sq = uci_str[:2], uci_str[2:4]
    piece = PIECES.get(move.piece, "")
    letter = piece if piece != "P" else ""
    sep = "x" if move.captured != EMPTY else "-"
    return f"{letter}{src_sq}{sep}{dst_sq}"
