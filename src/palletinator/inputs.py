"""Input types for the pallet processor."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ColumnNames:
    """Spreadsheet column headers the engine should read each field from.

    A ``None`` entry means the field is not present in the export and a
    sensible default will be used.
    """

    parent_zppk: str
    baby_zppk: str
    team_key: str
    team_name: str
    requested_pallet_count: str
    color_description: str
    logo_description: str
    column: str
    side: str
    callout: str | None = None
    date_column: str | None = None


@dataclass(frozen=True, slots=True)
class Request:
    """A request to process a pallet program export."""

    csv_data: str
    column_names: ColumnNames
