"""Output data model for processed pallets."""

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
        The representation value displayed in the cell (the baby ZPPK).
    photo_lookup_key
        Key the caller uses to look up the design image for this cell.
    extras
        Open-ended metadata bag for caller-defined fields.
    """

    value: str
    photo_lookup_key: str
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Column:
    """A column on a pallet side, ordered top-to-bottom by size band."""

    number: int
    cells: list[Cell]


@dataclass(frozen=True, slots=True)
class Side:
    """A side of a pallet, ordered left-to-right by column number."""

    number: int
    columns: list[Column]


@dataclass(frozen=True, slots=True)
class Pallet:
    """A fully-resolved pallet build."""

    zppk: str
    team_key: str
    team_name: str
    callout: str
    dc_target: str
    pallet_type: PalletType
    required_count: int
    sides: list[Side]
