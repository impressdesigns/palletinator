"""Pallet-inator."""

from dataclasses import dataclass

from .pallet import Pallet, PalletCell, PalletColumn, PalletSide


@dataclass(frozen=True, slots=True)
class Row:
    """A sheet row."""

    baby_zppk: str
    sides: list[int]
    columns: list[int]


class Palletinator:
    """Pallet-inator."""

    def parse_pallet(
        self,
        rows: list[Row],
        *,
        repeat_columns: bool = False,
    ) -> Pallet:
        """Parse a pallet."""
        pallet = Pallet()
        for row in rows:
            for side in row.sides:
                while len(pallet.sides) < side:
                    pallet.sides.append(PalletSide())

                if repeat_columns or row.columns[0] == 5:  # noqa: PLR2004
                    columns = [2] if side % 2 == 0 else [3]
                    columns = list(range(1, columns[0] + 1))
                else:
                    columns = row.columns

                pallet_side = pallet.sides[side - 1]
                for column in columns:
                    while len(pallet_side.columns) < column:
                        pallet_side.columns.append(PalletColumn())

                    design_key = "[FIXME]"

                    pallet_side.columns[column - 1].cells.append(
                        PalletCell(
                            metadata={"design_key": design_key},
                            display_text=row.baby_zppk,
                        ),
                    )
        return pallet
