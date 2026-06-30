# Dorsetest

Simple testing program for comparing two versions of the dorse chess engine.

## Structure
- `v1/`, `v2/` — engine versions being compared
- `noob5.epd` — pool of balanced opening positions
- `test.py` — runs games between v1 and v2, prints running score
- `results/` — saved results per run (planned)
- `test.html` — visualizer for results (planned)

## Usage
```
python test.py
```