# Dorsetest

Simple testing program for comparing two versions of the dorse chess engine.

## Structure
- `engines/v1/`, `engines/v2/` - engine versions being compared
- `noob5.epd` - pool of balanced opening positions
- `test.py` - runs games between v1 and v2, prints running score
- `utils.py` - shared helpers (FEN parsing, etc.), not versioned per engine
- `results/` - saved results per run, timestamped JSON
- `test.html` - visualizer for results

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