"""Input types for the pallet builder."""

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class CellPlacement:
    """Specification for where a cell goes on a pallet build.

    Attributes
    ----------
    value
        The value displayed in the resulting cell.
    sides
        Side numbers the cell appears on.
    columns
        Column numbers (within each side) the cell appears in.
    extras
        Open-ended metadata bag for caller-defined fields. A copy is
        attached to every emitted ``Cell`` so callers can mutate per-cell
        state without cross-talk.
    """

    value: str
    sides: list[int]
    columns: list[int]
    extras: dict[str, Any] = field(default_factory=dict)
