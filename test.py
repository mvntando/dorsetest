import importlib
import time
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

V1 = {"path": "engines.v1", "name": "v1"}
V2 = {"path": "engines.v2", "name": "v2"}

Timestamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M%S")

def load_engine(pkg_name):
    # Import an engine's dorse/search modules by dotted package path
    dorse = importlib.import_module(f"{pkg_name}.dorse")
    search = importlib.import_module(f"{pkg_name}.search")
    return dorse.Position, search.Searcher


def load_epd(path):
    # Read an EPD file and return a list of FEN strings (first 6 fields only).
    positions = []
    with open(path) as f:
        for line in f:
            if line.strip():
                parts = line.strip().split()
                positions.append(" ".join(parts[:6]))
    return positions


def save_results(results):
    # Inject results as timestamped JSON into test.html between marker comments
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

Pos1, Searcher1 = load_engine(V1["path"])
Pos2, Searcher2 = load_engine(V2["path"])

def run_game(fen, movetime, swap, verbose):
    # Play a single game between v1 and v2 from a given FEN, swapping sides

    engines = [Searcher2(), Searcher1()] if swap else [Searcher1(), Searcher2()]
    positions = [Pos2, Pos1] if swap else [Pos1, Pos2]
    names = [V2["name"], V1["name"]] if swap else [V1["name"], V2["name"]]

    # Each engine may have its own Position class/board representation, thus tracking a separate position object per side
    pos = [P(*utils.parse_fen(fen)) for P in positions]

    moves = []
    move_stats = []
    current = 0 if fen.split()[1] == "w" else 1
    seen_positions = {}
    halfmove_clock = 0

    for _ in range(200):
        # Run the current engine's search for a move
        engine = engines[current]
        start = time.perf_counter()
        move = engine.search(pos[current], movetime=movetime / 1000.0, verbose=verbose)
        elapsed = time.perf_counter() - start

        pv_moves = engine.pv_moves
        pv_str = " ".join(utils.move_alg(m) for m in pv_moves if m)
        comment = f"({pv_str}) {engine.score / 100:.2f}/{engine.depth} {round(elapsed)}"

        move_stats.append({
            "engine": names[current], "depth": engine.depth, "nodes": engine.nodes, "qnodes": engine.qnodes, "elapsed": elapsed, "comment": comment,
        })

        if move is None:
            in_check_a = pos[current].in_check(pos[current].sd)
            in_check_b = pos[current^1].in_check(pos[current].sd)
            if in_check_a != in_check_b:
                print(f"warning: in_check mismatch between engines at move {len(moves)}")

            if in_check_a:
                winner = names[1 - current]  # checkmate
            else:
                winner = "draw"  # stalemate
            break

        move_uci = move.uci()
        moves.append(move_uci)
        for p in pos:
            p.make_uci_move(move_uci)

        # 3 fold repetition detection (check for hash mismatch between engines)
        h0, h1 = pos[0].hash, pos[1].hash
        if h0 != h1:
            print(f"warning: hash mismatch between engines at move {len(moves)} ({h0} vs {h1})")

        seen_positions[h0] = seen_positions.get(h0, 0) + 1
        if seen_positions[h0] >= 3:
            winner = "draw"
            break

        # 50-move rule detection
        if move.piece == utils.PAWN or move.captured != utils.EMPTY:
            halfmove_clock = 0
        else:
            halfmove_clock += 1

        if halfmove_clock >= 100:  # 50 full moves with no pawn push/capture
            winner = "draw"
            break

        current ^= 1
    else:
        winner = "draw"

    move_meta = [m["comment"] for m in move_stats[:len(moves)]]
    game = {
        "result": winner, "white": names[0], "black": names[1], "moves": len(moves), "moves_uci": " ".join(moves), "move_meta": move_meta,
    }

    return game, move_stats


def main():
    # Parse args, run all games across the selected positions
    parser = argparse.ArgumentParser()
    parser.add_argument("--positions", type=int, default=1)
    parser.add_argument("--movetime", type=int, default=5000)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    positions = load_epd("noob5.epd")
    score = {"v1": 0, "v2": 0, "draw": 0}
    stat_totals = {"v1": {"nodes": 0, "qnodes": 0, "elapsed": 0.0, "count": 0, "maxDepth": 0, "games": 0},
                   "v2": {"nodes": 0, "qnodes": 0, "elapsed": 0.0, "count": 0, "maxDepth": 0, "games": 0}}

    results = {
        "timestamp": Timestamp,
        "engines": {"v1": V1["name"], "v2": V2["name"]},
        "movetime": args.movetime,
        "summary": score,
        "stats": {},
        "games": [],
    }

    # Run games for the selected number of positions, swapping sides for each position
    for fen in positions[:args.positions]:
        for swap in (False, True):
            game, move_stats = run_game(fen, movetime=args.movetime, swap=swap, verbose=args.verbose)
            game["fen"] = fen
            results["games"].append(game)

            # per-game max depth per engine; only tracked for engines that actually moved this game
            game_max_depth = {}
            for m in move_stats:
                t = stat_totals[m["engine"]]
                t["nodes"] += m["nodes"]
                t["qnodes"] += m["qnodes"]
                t["elapsed"] += m["elapsed"]
                t["count"] += 1
                game_max_depth[m["engine"]] = max(game_max_depth.get(m["engine"], 0), m["depth"])

            for name, d in game_max_depth.items():
                stat_totals[name]["maxDepth"] += d
                stat_totals[name]["games"] += 1

            score[game["result"]] += 1
            print(f"\rv1 {score['v1']} - {score['v2']} v2 ({score['draw']} draws)", end="", flush=True)

    print("\n")

    results["stats"] = {
        name: {
            "avgNps": int(t["nodes"] / t["elapsed"]) if t["elapsed"] > 0 else 0,
            "avgMaxDepth": round(t["maxDepth"] / t["games"], 1) if t["games"] else 0,
            "avgNodes": int(t["nodes"] / t["count"]) if t["count"] else 0,
            "avgQNodes": int(t["qnodes"] / t["count"]) if t["count"] else 0,
        }
        for name, t in stat_totals.items()
    }

    save_results(results)
    return results

if __name__ == "__main__":
    main()