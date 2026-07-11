import sys
import importlib
import datetime
import json
import os
import re
import argparse

import utils  # shared, root-level, not versioned per engine

"""
Simple chess engine testing script.
Runs two engines by importing their Searcher/Position classes directly,
plays games from EPD positions (sides swapped), and tracks a running score.
Update the engine paths if needed.
"""

V1 = {"path": "engines/v1", "name": "v1"}
V2 = {"path": "engines/v2", "name": "v2"}

Timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")

def load_engine(engine_dir):
    """Load an engine's dorse/search modules by temporarily putting engine_dir
    at the front of sys.path, so the engine's own internal imports (e.g.
    dorse.py's `from evaluate import ...`) resolve to files in that same dir.
    Clears any cached modules of the same name first so v1/v2 don't collide."""
    modnames = [f[:-3] for f in os.listdir(engine_dir) if f.endswith(".py")]

    sys.path.insert(0, engine_dir)
    try:
        for m in modnames:
            sys.modules.pop(m, None)  # force fresh import from this engine_dir
        dorse = importlib.import_module("dorse")
        search = importlib.import_module("search")
    finally:
        sys.path.remove(engine_dir)

    return dorse.Position, search.Searcher


def load_epd(path):
    positions = []
    with open(path) as f:
        for line in f:
            if line.strip():
                parts = line.strip().split()
                positions.append(" ".join(parts[:6]))
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


def run_game(fen, movetime, swap):
    Pos1, Searcher1 = load_engine(V1["path"])
    Pos2, Searcher2 = load_engine(V2["path"])

    engines = [Searcher2(), Searcher1()] if swap else [Searcher1(), Searcher2()]
    positions = [Pos2, Pos1] if swap else [Pos1, Pos2]
    names = [V2["name"], V1["name"]] if swap else [V1["name"], V2["name"]]

    # Each engine may have its own Position class/board representation, thus tracking a separate position object per side
    pos = [P(*utils.parse_fen(fen)) for P in positions]

    moves = []
    current = 0  # 0 = white, 1 = black

    for _ in range(200):
        engine = engines[current]
        move = engine.search(pos[current], movetime=movetime / 1000.0)
        if move is None:
            winner = names[1 - current]
            break

        move_uci = move.uci()
        moves.append(move_uci)
        for p in pos:
            p.make_uci_move(move_uci)
        current ^= 1
    else:
        winner = "draw"

    return {
        "result": winner, "moves": len(moves), "white": names[0], "black": names[1],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--positions", type=int, default=1)
    parser.add_argument("--movetime", type=int, default=5000)
    args = parser.parse_args()

    positions = load_epd("noob5.epd")
    score = {"v1": 0, "v2": 0, "draw": 0}

    results = {
        "timestamp": Timestamp,
        "engines": {"v1": V1["name"], "v2": V2["name"]},
        "movetime": args.movetime,
        "games": [],
        "summary": score,
    }

    for fen in positions[:args.positions]:
        for swap in (False, True):
            game = run_game(fen, movetime=args.movetime, swap=swap)
            game["fen"] = fen
            results["games"].append(game)

            score[game["result"]] += 1
            print(f"\rv1 {score['v1']} - {score['v2']} v2 ({score['draw']} draws)", end="", flush=True)

    print("\n")

    save_results(results)
    return results

if __name__ == "__main__":
    main()