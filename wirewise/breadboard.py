"""Breadboard geometry and internal connectivity.

A standard breadboard has terminal columns (1..N) split into two strips
(rows a-e and f-j) plus four power rails. Holes inside one strip of one
column are electrically common; each rail is common along its length.
"""
from dataclasses import dataclass

TOP_ROWS = "abcde"
BOTTOM_ROWS = "fghij"
RAILS = ("T+", "T-", "B+", "B-")


@dataclass(frozen=True)
class BreadboardSpec:
    columns: int = 30
    pitch_mm: float = 2.54


def hole_to_net(hole: str, spec: BreadboardSpec = BreadboardSpec()) -> str:
    """Map a hole name (e.g. 'a12', 'T+5') to its internal net id."""
    hole = hole.strip()
    for rail in RAILS:
        if hole.startswith(rail):
            col = int(hole[len(rail):])
            _check_col(col, spec)
            return f"RAIL_{rail}"
    row, col = hole[0].lower(), int(hole[1:])
    _check_col(col, spec)
    if row in TOP_ROWS:
        return f"COL{col}_TOP"
    if row in BOTTOM_ROWS:
        return f"COL{col}_BOT"
    raise ValueError(f"Unknown hole: {hole}")


def _check_col(col: int, spec: BreadboardSpec) -> None:
    if not 1 <= col <= spec.columns:
        raise ValueError(f"Column {col} outside 1..{spec.columns}")


def all_holes(spec: BreadboardSpec = BreadboardSpec()):
    """Canonical hole list with grid coordinates (col, row_index) for vision mapping."""
    rows = list(TOP_ROWS) + list(BOTTOM_ROWS)
    for c in range(1, spec.columns + 1):
        for r_idx, r in enumerate(rows):
            # 1-row gap (the centre channel) between e and f
            y = r_idx + (1 if r_idx >= 5 else 0)
            yield f"{r}{c}", (c - 1, y)
