"""Tests for the pallet builder engine."""

from palletinator import (
    Cell,
    CellPlacement,
    Pallet,
    build_pallet,
)


def test_build_pallet_returns_pallet_with_extras() -> None:
    pallet = build_pallet(
        [CellPlacement(value="X", sides=[1], columns=[1])],
        extras={"order_id": "PZ-1"},
    )

    assert isinstance(pallet, Pallet)
    assert pallet.extras == {"order_id": "PZ-1"}


def test_pallet_extras_default_to_empty_dict() -> None:
    pallet = build_pallet([CellPlacement(value="X", sides=[1], columns=[1])])
    assert pallet.extras == {}


def test_pallet_extras_dict_is_independent_per_pallet() -> None:
    p1 = build_pallet([CellPlacement(value="X", sides=[1], columns=[1])])
    p2 = build_pallet([CellPlacement(value="X", sides=[1], columns=[1])])

    p1.extras["k"] = "v"
    assert p2.extras == {}


def test_pallet_extras_are_copied_from_input() -> None:
    source = {"k": "v"}
    pallet = build_pallet([CellPlacement(value="X", sides=[1], columns=[1])], extras=source)

    pallet.extras["k"] = "other"
    assert source == {"k": "v"}


def test_cells_carry_value_and_extras() -> None:
    pallet = build_pallet(
        [
            CellPlacement(value="A", sides=[1], columns=[1], extras={"key": "K"}),
            CellPlacement(value="B", sides=[1], columns=[1], extras={"key": "K"}),
        ],
    )

    [side] = pallet.sides
    assert side.number == 1
    [column] = side.columns
    assert column.number == 1

    assert [cell.value for cell in column.cells] == ["A", "B"]
    for cell in column.cells:
        assert cell.extras == {"key": "K"}


def test_cell_extras_dict_is_independent_per_cell() -> None:
    pallet = build_pallet(
        [
            CellPlacement(value="A", sides=[1], columns=[1]),
            CellPlacement(value="B", sides=[1], columns=[1]),
        ],
    )
    [side] = pallet.sides
    [column] = side.columns

    column.cells[0].extras["image_b64"] = "abc"
    assert column.cells[1].extras == {}


def test_cell_extras_are_copied_from_placement() -> None:
    source = {"k": "v"}
    pallet = build_pallet([CellPlacement(value="A", sides=[1], columns=[1], extras=source)])

    pallet.sides[0].columns[0].cells[0].extras["k"] = "other"
    assert source == {"k": "v"}


def test_column_truncates_to_max_cells_per_column_default_four() -> None:
    placements = [CellPlacement(value=f"B{i}", sides=[1], columns=[1]) for i in range(1, 6)]
    pallet = build_pallet(placements)

    [side] = pallet.sides
    [column] = side.columns
    assert [cell.value for cell in column.cells] == ["B2", "B3", "B4", "B5"]


def test_max_cells_per_column_is_configurable() -> None:
    placements = [CellPlacement(value=f"B{i}", sides=[1], columns=[1]) for i in range(1, 5)]
    pallet = build_pallet(placements, max_cells_per_column=2)

    [side] = pallet.sides
    [column] = side.columns
    assert [cell.value for cell in column.cells] == ["B3", "B4"]


def test_placement_with_multiple_sides_and_columns_fans_out() -> None:
    pallet = build_pallet([CellPlacement(value="X", sides=[1, 2], columns=[1, 2])])

    sides = {side.number: side for side in pallet.sides}
    assert set(sides) == {1, 2}
    for side in sides.values():
        assert [column.number for column in side.columns] == [1, 2]
        for column in side.columns:
            assert [cell.value for cell in column.cells] == ["X"]


def test_sides_and_columns_are_sorted_by_number() -> None:
    pallet = build_pallet(
        [
            CellPlacement(value="A", sides=[3], columns=[2]),
            CellPlacement(value="B", sides=[1], columns=[3]),
            CellPlacement(value="C", sides=[1], columns=[1]),
        ],
    )

    assert [side.number for side in pallet.sides] == [1, 3]
    assert [column.number for column in pallet.sides[0].columns] == [1, 3]


def test_empty_placements_produces_empty_pallet() -> None:
    pallet = build_pallet([])
    assert pallet.sides == []


def test_placement_with_empty_sides_or_columns_is_skipped() -> None:
    pallet = build_pallet(
        [
            CellPlacement(value="A", sides=[], columns=[1]),
            CellPlacement(value="B", sides=[1], columns=[]),
        ],
    )
    assert pallet.sides == []


def test_cell_is_constructible_directly_with_extras() -> None:
    cell = Cell(value="X", extras={"size": "M"})
    assert cell.value == "X"
    assert cell.extras == {"size": "M"}


def test_cell_extras_default_to_empty_dict() -> None:
    cell = Cell(value="X")
    assert cell.extras == {}


def test_pallet_is_constructible_directly_with_extras() -> None:
    pallet = Pallet(sides=[], extras={"order_id": "1"})
    assert pallet.sides == []
    assert pallet.extras == {"order_id": "1"}
