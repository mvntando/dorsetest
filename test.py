import subprocess
import sys
import datetime
import json
import os
import re

"""
Simple chess engine testing script.
Runs two engines via the UCI protocol using subprocess, plays games from
EPD positions (sides swapped), and tracks a running score.
Update the engine paths if needed.
"""

# Engine paths
V1 = {"path": "engines/v1/uci.py", "name": "v1"}
V2 = {"path": "engines/v2/uci.py", "name": "v2"}

Timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")

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

def save_results(results):
    os.makedirs("results", exist_ok=True)
    timestamp = Timestamp
    with open(f"results/{timestamp}.json", "w") as f:
        json.dump(results, f, indent=2)

    with open("test.html") as f:
        html = f.read()

    new_block = f"<!-- DORSE_RESULTS_START -->\n<script>\nconst results = {json.dumps(results)};\n</script>\n<!-- DORSE_RESULTS_END -->"
    html = re.sub(
        r"<!-- DORSE_RESULTS_START -->.*?<!-- DORSE_RESULTS_END -->",
        new_block,
        html,
        flags=re.DOTALL,
    )

    with open("test.html", "w") as f:
        f.write(html)

def run_game(fen, movetime=100, swap=False):
    v1 = launch_engine(V1["path"])
    v2 = launch_engine(V2["path"])

    engines = [v2, v1] if swap else [v1, v2]
    names = [V2["name"], V1["name"]] if swap else [V1["name"], V2["name"]]

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

    return {
        "result": winner, "moves": len(moves), "white": names[0], "black": names[1],
    }

def main():
    positions = load_epd("noob5.epd")
    score = {"v1": 0, "v2": 0, "draw": 0}

    results = {
        "timestamp": Timestamp,
        "engines": {"v1": V1["name"], "v2": V2["name"]},
        "movetime": 100,
        "games": [],
        "summary": score,  # same dict object, updates live as score updates
    }

    for fen in positions[:10]:  # Limit to first 10 positions for testing (engines can be too slow)
        for swap in (False, True):
            game = run_game(fen, movetime=5000, swap=swap)  # movetime <100ms can cause engine to return 0000
            game["fen"] = fen
            results["games"].append(game)

            score[game["result"]] += 1
            print(f"\rv1 {score['v1']} - {score['v2']} v2 ({score['draw']} draws)", end="", flush=True)

    print("\n")

    save_results(results)
    return results

if __name__ == "__main__":
    main()
