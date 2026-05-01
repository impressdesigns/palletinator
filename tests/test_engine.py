"""Tests for the pallet processing engine."""

from textwrap import dedent

from palletinator import (
    Cell,
    ColumnNames,
    PalletType,
    Request,
    process,
)

_COLUMN_NAMES = ColumnNames(
    parent_zppk="parent",
    baby_zppk="baby",
    team_key="team_key",
    team_name="team_name",
    requested_pallet_count="count",
    color_description="color",
    logo_description="logo",
    column="column",
    side="side",
    callout="callout",
    date_column="dc",
)


def _request(csv_data: str) -> Request:
    return Request(csv_data=dedent(csv_data).lstrip(), column_names=_COLUMN_NAMES)


def test_process_returns_one_pallet_with_expected_top_level_fields() -> None:
    csv_data = """\
        parent,baby,team_key,team_name,count,color,logo,column,side,callout,dc
        PZ-1,BZ-A,TK,Team Name,0,Red,LogoText,1,1,No,
        PZ-1,BZ-B,TK,Team Name,0,Red,LogoText,1,1,No,
        PZ-1,BZ-C,TK,Team Name,0,Red,LogoText,1,1,No,
        PZ-1,BZ-D,TK,Team Name,0,Red,LogoText,1,1,No,
        ,,,,5,,,,,Yes,2026-06-15
    """
    [pallet] = process(_request(csv_data))

    assert pallet.zppk == "PZ-1"
    assert pallet.team_key == "TK"
    assert pallet.team_name == "Team Name"
    assert pallet.required_count == 5
    assert pallet.pallet_type is PalletType.TOWER
    assert pallet.callout == "CLC CREATIVE CORRUGATE"
    assert pallet.dc_target == "2026-06-15"


def test_cells_carry_value_and_photo_lookup_key() -> None:
    csv_data = """\
        parent,baby,team_key,team_name,count,color,logo,column,side,callout,dc
        PZ-1,BZ-A,TK,Team Name,0,"Red, Bold",LogoTextLong,1,1,No,
        PZ-1,BZ-B,TK,Team Name,0,"Red, Bold",LogoTextLong,1,1,No,
        ,,,,1,,,,,No,
    """
    [pallet] = process(_request(csv_data))

    [side] = pallet.sides
    assert side.number == 1
    [column] = side.columns
    assert column.number == 1

    assert [cell.value for cell in column.cells] == ["BZ-A", "BZ-B"]
    expected_key = "LogoTex Red Bold TK"
    for cell in column.cells:
        assert cell.photo_lookup_key == expected_key
        assert cell.extras == {}


def test_column_truncates_to_last_four_cells() -> None:
    csv_data = """\
        parent,baby,team_key,team_name,count,color,logo,column,side,callout,dc
        PZ,B1,TK,Team,0,Red,Logo,1,1,No,
        PZ,B2,TK,Team,0,Red,Logo,1,1,No,
        PZ,B3,TK,Team,0,Red,Logo,1,1,No,
        PZ,B4,TK,Team,0,Red,Logo,1,1,No,
        PZ,B5,TK,Team,0,Red,Logo,1,1,No,
        ,,,,1,,,,,No,
    """
    [pallet] = process(_request(csv_data))
    [side] = pallet.sides
    [column] = side.columns

    assert [cell.value for cell in column.cells] == ["B2", "B3", "B4", "B5"]


def test_extras_dict_is_independent_per_cell() -> None:
    csv_data = """\
        parent,baby,team_key,team_name,count,color,logo,column,side,callout,dc
        PZ,B1,TK,Team,0,Red,Logo,1,1,No,
        PZ,B2,TK,Team,0,Red,Logo,1,1,No,
        ,,,,1,,,,,No,
    """
    [pallet] = process(_request(csv_data))
    [side] = pallet.sides
    [column] = side.columns

    column.cells[0].extras["image_b64"] = "abc"
    assert column.cells[1].extras == {}


def test_column_five_alternates_per_side() -> None:
    csv_data = """\
        parent,baby,team_key,team_name,count,color,logo,column,side,callout,dc
        PZ,B1,TK,Team,0,Red,Logo,5,12,No,
        ,,,,1,,,,,No,
    """
    [pallet] = process(_request(csv_data))

    sides = {side.number: side for side in pallet.sides}
    assert set(sides) == {1, 2}

    assert [column.number for column in sides[1].columns] == [1, 2, 3]
    assert [column.number for column in sides[2].columns] == [1, 2]


def test_multiple_pallets_split_on_nonzero_count() -> None:
    csv_data = """\
        parent,baby,team_key,team_name,count,color,logo,column,side,callout,dc
        PZ-A,BA1,TKA,Team A,0,Red,Logo,1,1,No,
        ,,,,3,,,,,No,
        PZ-B,BB1,TKB,Team B,0,Blue,Logo,1,1,Yes,
        ,,,,7,,,,,Yes,
    """
    pallets = process(_request(csv_data))

    assert len(pallets) == 2
    assert pallets[0].zppk == "PZ-A"
    assert pallets[0].team_key == "TKA"
    assert pallets[0].required_count == 3
    assert pallets[0].callout == ""
    assert pallets[1].zppk == "PZ-B"
    assert pallets[1].team_key == "TKB"
    assert pallets[1].required_count == 7
    assert pallets[1].callout == "CLC CREATIVE CORRUGATE"


def test_cell_is_constructible_directly_with_extras() -> None:
    cell = Cell(value="X", photo_lookup_key="K", extras={"size": "M"})
    assert cell.value == "X"
    assert cell.photo_lookup_key == "K"
    assert cell.extras == {"size": "M"}
