"""Pallet data structures."""

from dataclasses import dataclass, field


@dataclass
class PalletCell:
    """A cell of a pallet."""

    display_text: str
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class PalletColumn:
    """A column of a pallet."""

    cells: list[PalletCell] = field(default_factory=list)


@dataclass
class PalletSide:
    """A side of a pallet."""

    columns: list[PalletColumn] = field(default_factory=list)


@dataclass
class Pallet:
    """A pallet."""

    metadata: dict[str, str] = field(default_factory=dict)
    sides: list[PalletSide] = field(default_factory=list)
