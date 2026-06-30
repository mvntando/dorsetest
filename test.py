import subprocess
import sys

'''
Simple Chess Engine Testing Script
Runs the python subprocess module for the engine and uses the UCI protocol.
Change the paths to the engine scripts if needed.
'''

V1 = "engines/v1/uci.py"
V2 = "engines/v2/uci.py"

def launch_engine(path):
    return subprocess.Popen(
        [sys.executable, path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True
    )

def send(proc, cmd):
    proc.stdin.write(cmd + "\n")
    proc.stdin.flush()

def read_move(proc):
    while True:
        line = proc.stdout.readline()
        if line.startswith("bestmove"):
            move = line.split()[1]
            if move == "0000":
                return None  # game over
            return move
        
def load_epd(path):
    positions = []
    with open(path) as f:
        for line in f:
            if line.strip():
                parts = line.strip().split()
                positions.append(" ".join(parts[:6]))  # keep only the FEN part
    return positions

def run_game(fen, movetime=100, swap=False):
    v1 = launch_engine(V1)
    v2 = launch_engine(V2)

    engines = [v2, v1] if swap else [v1, v2]
    names = ["v2", "v1"] if swap else ["v1", "v2"]

    moves = []
    current = 0  # 0 = white, 1 = black

    for _ in range(200):
        engine = engines[current]
        move_str = "moves " + " ".join(moves) if moves else ""
        send(engine, f"position fen {fen} {move_str}".strip())
        send(engine, f"go movetime {movetime}")
        move = read_move(engine)
        if move is None:
            winner = names[1 - current]
            break
        moves.append(move)
        current ^= 1
    else:
        winner = "draw"

    v1.terminate()
    v2.terminate()
    
    return winner

def main():
    positions = load_epd("noob5.epd")
    score = {"v1": 0, "v2": 0, "draw": 0}

    for fen in positions[:10]:  # Limit to first 10 positions for testing (engines can be too slow)
        for swap in (False, True):
            result = run_game(fen, movetime=100, swap=swap)  # movetime <100ms can cause engine to return 0000
            score[result] += 1
            print(f"\rv1 {score['v1']} - {score['v2']} v2 ({score['draw']} draws)", end="", flush=True)

    print("\n")

if __name__ == "__main__":
    main()
