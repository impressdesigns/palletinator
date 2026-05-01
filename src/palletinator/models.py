"""Output data model for built pallets."""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any


class PalletType(Enum):
    """Type of pallet build."""

    FULL = auto()
    HALF = auto()
    TOWER = auto()


@dataclass(frozen=True, slots=True)
class Cell:
    """A single cell within a pallet column.

    Attributes
    ----------
    value
        The value displayed in the cell.
    extras
        Open-ended metadata bag for caller-defined fields.
    """

    value: str
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Column:
    """A column on a pallet side, ordered top-to-bottom."""

    number: int
    cells: list[Cell]


@dataclass(frozen=True, slots=True)
class Side:
    """A side of a pallet, ordered left-to-right by column number."""

    number: int
    columns: list[Column]


@dataclass(frozen=True, slots=True)
class Pallet:
    """A fully-resolved pallet build.

    Attributes
    ----------
    pallet_type
        The build type (full, half, tower).
    sides
        Sides on the pallet, ordered by side number.
    extras
        Open-ended metadata bag for caller-defined fields.
    """

    pallet_type: PalletType
    sides: list[Side]
    extras: dict[str, Any] = field(default_factory=dict)
