"""Pallet building engine.

Bucket caller-supplied cell placements into a structured `Pallet` of
sides, columns, and cells. The engine performs no I/O and applies no
business rules: callers decide where each cell goes and what extra
metadata it carries.
"""

from typing import TYPE_CHECKING, Any

from palletinator.models import Cell, Column, Pallet, Side

if TYPE_CHECKING:
    from palletinator.inputs import CellPlacement


def build_pallet(
    placements: list[CellPlacement],
    *,
    extras: dict[str, Any] | None = None,
) -> Pallet:
    """Build a pallet from a list of cell placements.

    Parameters
    ----------
    placements
        The cells to place. Each placement is materialised into one
        ``Cell`` per ``(side, column)`` coordinate it specifies.
    extras
        Open-ended metadata bag attached to the resulting ``Pallet``.

    Returns
    -------
    Pallet
        A pallet whose sides and columns are sorted by number.
    """
    buckets: dict[int, dict[int, list[CellPlacement]]] = {}
    for placement in placements:
        for side_num in placement.sides:
            for column_num in placement.columns:
                buckets.setdefault(side_num, {}).setdefault(column_num, []).append(placement)

    sides: list[Side] = []
    for side_num in sorted(buckets):
        columns: list[Column] = []
        for column_num in sorted(buckets[side_num]):
            cells = [
                Cell(value=placement.value, extras=dict(placement.extras))
                for placement in buckets[side_num][column_num]
            ]
            columns.append(Column(number=column_num, cells=cells))
        sides.append(Side(number=side_num, columns=columns))

    return Pallet(
        sides=sides,
        extras=dict(extras) if extras else {},
    )
