# Dorsetest

Simple testing program for comparing two versions of the dorse chess engine.

## Structure
- `engines/v1/`, `engines/v2/` - engine versions being compared
- `noob5.epd` - pool of balanced opening positions
- `test.py` - runs games between v1 and v2, tracks score (checkmate/stalemate/repetition/move-limit), and per-engine stats (avg NPS, avg nodes/qnodes per move, avg max depth per game)
- `utils.py` - shared helpers (FEN parsing, etc.), not versioned per engine
- `results/` - saved results per run, timestamped JSON
- `test.html` - visualizer for results; copy button on each game exports PGN
- `chess.js` - required alongside `test.html` for PGN export (use `chess.js@0.12.1`, not newer versions - see note below)

## Engine requirements
Each engine dir (`engines/v1`, `engines/v2`) must be a proper Python package:
- needs an `__init__.py` (can be empty)
- internal sibling imports must be relative, e.g. `from .evaluate import piece_eval`
  (bare imports like `from evaluate import piece_eval` will break or collide across versions)

## Usage
```
python test.py --positions 5 --movetime 500
```
- `--positions` - number of opening positions to test (each played twice, sides swapped). Default: 1
- `--movetime` - time per move in ms. Default: 5000.
- Note: movetime values under 100ms may cause engines to return no move, especially on slower systems.
- in the games table you can click the "Copy PGN" button to copy the game's PGN to your clipboard.

## chess.js version note
`test.html` uses `chess.js` to convert a game's FEN + move list into PGN for the copy button.
Versions `0.13.0` and newer are ES modules (`export const ...`) and will throw a syntax error
when loaded via a plain `<script src="chess.js">` tag. Use `0.12.1`, which exposes a plain
global `Chess` and works with no build step:

```
curl -o chess.js https://unpkg.com/chess.js@0.12.1/chess.js
```