"""Testing the client."""

from palletinator import Palletinator, Row

ROW = Row(
    baby_zppk="ZPPK-1234",
    sides=[1],
    columns=[1, 2],
)


def test_parse_pallet() -> None:
    """Test parsing a pallet."""
    engine = Palletinator()
    pallet = engine.parse_pallet([ROW])

    assert len(pallet.sides) == 1
    assert len(pallet.sides[0].columns) == 2  # noqa: PLR2004
    assert len(pallet.sides[0].columns[0].cells) == 1
    assert pallet.sides[0].columns[0].cells[0].display_text == "ZPPK-1234"
    assert pallet.sides[0].columns[0].cells[0].metadata["design_key"] == "[FIXME]"
