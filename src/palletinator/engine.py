"""Pallet processing engine.

Turns a pallet-program CSV export into a structured list of `Pallet`
objects. The engine performs no I/O: it does not contact a database,
fetch images, render PDFs, or send mail. Callers are responsible for
enriching cells (using each cell's ``photo_lookup_key``) and for any
downstream presentation.
"""

import csv
from dataclasses import dataclass
from io import StringIO
from typing import TYPE_CHECKING, Self

from palletinator.models import Cell, Column, Pallet, PalletType, Side

if TYPE_CHECKING:
    from palletinator.inputs import ColumnNames, Request

_FIVE_COLUMN_TRIGGER = 5
_MAX_CELLS_PER_COLUMN = 4


def process(request: Request) -> list[Pallet]:
    """Process a pallet-program CSV export into structured pallet data.

    Parameters
    ----------
    request
        The CSV payload and the column-name mapping describing where
        each logical field lives in the export.

    Returns
    -------
    list[Pallet]
        One `Pallet` per row group in the export.
    """
    raw_rows = list(csv.DictReader(StringIO(request.csv_data)))
    rows = [_Row.from_dict(raw, request.column_names) for raw in raw_rows]
    return [_build_pallet(group) for group in _group_rows(rows)]


@dataclass(frozen=True, slots=True)
class _Row:
    """An internal parsed CSV row."""

    parent_zppk: str
    baby_zppk: str
    team_key: str
    team_name: str
    requested_pallet_count: int
    callout: str
    dc_target: str
    color_description: str
    logo_description: str
    sides: list[int]
    columns: list[int]

    @classmethod
    def from_dict(cls: type[Self], data: dict[str, str], names: ColumnNames) -> Self:
        """Build a row from a `csv.DictReader` record."""
        callout = ""
        if names.callout is not None and data.get(names.callout) == "Yes":
            callout = "CLC CREATIVE CORRUGATE"

        dc_target = ""
        if names.date_column is not None:
            dc_target = data.get(names.date_column) or ""

        return cls(
            parent_zppk=data.get(names.parent_zppk) or "",
            baby_zppk=data.get(names.baby_zppk) or "",
            team_key=data.get(names.team_key) or "",
            team_name=data.get(names.team_name) or "",
            requested_pallet_count=int(data.get(names.requested_pallet_count) or 0),
            callout=callout,
            dc_target=dc_target,
            color_description=data.get(names.color_description) or "",
            logo_description=data.get(names.logo_description) or "",
            sides=_extract_numbers(data.get(names.side) or "1"),
            columns=_extract_numbers(data.get(names.column) or ""),
        )


def _extract_numbers(text: str) -> list[int]:
    """Pull the digit characters out of `text` as a list of single-digit ints."""
    return [int(char) for char in text if char.isdigit()]


def _group_rows(rows: list[_Row]) -> list[list[_Row]]:
    """Split rows into groups, terminating on a non-zero `requested_pallet_count`."""
    groups: list[list[_Row]] = []
    current: list[_Row] = []
    for row in rows:
        current.append(row)
        if row.requested_pallet_count != 0:
            groups.append(current)
            current = []
    return groups


def _build_pallet(group: list[_Row]) -> Pallet:
    """Build a `Pallet` from a single row group."""
    last = group[-1]
    header = group[-2] if len(group) > 1 else last
    body = group[:-1] if len(group) > 1 else group

    return Pallet(
        zppk=header.parent_zppk,
        team_key=header.team_key,
        team_name=header.team_name,
        callout=last.callout,
        dc_target=last.dc_target,
        pallet_type=PalletType.TOWER,
        required_count=last.requested_pallet_count,
        sides=_build_sides(body),
    )


def _build_sides(rows: list[_Row]) -> list[Side]:
    """Bucket rows by `(side, column)` and emit `Side` objects in order."""
    buckets: dict[int, dict[int, list[_Row]]] = {}
    keys: dict[tuple[int, int], str] = {}
    repeat_columns = False
    for row in rows:
        for side_num in row.sides:
            if row.columns and row.columns[0] == _FIVE_COLUMN_TRIGGER:
                repeat_columns = True
                column_set = [2] if side_num % 2 == 0 else [3]
            else:
                column_set = row.columns
            if not column_set:
                continue
            if repeat_columns:
                column_set = list(range(1, column_set[0] + 1))
            for column_num in column_set:
                side_bucket = buckets.setdefault(side_num, {})
                cell_rows = side_bucket.setdefault(column_num, [])
                keys.setdefault((side_num, column_num), _photo_lookup_key(row))
                cell_rows.append(row)

    sides: list[Side] = []
    for side_num in sorted(buckets):
        columns: list[Column] = []
        for column_num in sorted(buckets[side_num]):
            cell_rows = buckets[side_num][column_num][-_MAX_CELLS_PER_COLUMN:]
            key = keys[side_num, column_num]
            cells = [Cell(value=row.baby_zppk, photo_lookup_key=key) for row in cell_rows]
            columns.append(Column(number=column_num, cells=cells))
        sides.append(Side(number=side_num, columns=columns))
    return sides


def _photo_lookup_key(row: _Row) -> str:
    """Build the design-image lookup key for a row."""
    return " ".join(
        (
            row.logo_description[:7],
            row.color_description.replace(",", ""),
            row.team_key,
        ),
    )
