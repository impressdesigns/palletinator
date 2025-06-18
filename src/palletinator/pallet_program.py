"""Pallet Program."""

import base64
import csv
from dataclasses import asdict, dataclass
from enum import Enum, auto
from io import BytesIO, StringIO
from typing import Self

import httpx
from jinja2 import Environment, PackageLoader
from msgraph.generated.models.file_attachment import FileAttachment
from PIL import Image
from sqlalchemy import select
from weasyprint import CSS, HTML

from core.external.local_api import local_api_client
from core.mailer import send_mail
from core.models.redacted.pallet_program import ColumnNames, PDFsRequest
from core.orm import OnSiteDesign, Session


def get_image_for_design(design_number: int, size: tuple[int, int] | None = None) -> str:
    """Find and load to base64."""
    image_bytes = local_api_client.get_design_image(design_number)

    image = Image.open(BytesIO(image_bytes))
    if size:
        image.thumbnail(size)

    buffered = BytesIO()
    image.save(buffered, format="PNG")
    buffered.seek(0)

    return base64.b64encode(buffered.getvalue()).decode()


def _find_numbers_in_text(text: float | str) -> list[int]:
    if isinstance(text, float | int):
        return [int(text)]
    return [int(char) for char in text if char.isdigit()]


class PalletType(Enum):
    """Type of pallet."""

    FULL = auto()
    HALF = auto()
    TOWER = auto()


@dataclass(frozen=True, slots=True)
class Row:
    """A sheet row."""

    callout: str
    parent_zppk: str
    baby_zppk: str
    team_key: str
    team_name: str
    requested_pallet_count: int
    dc_target: str
    color_description: str
    logo_description: str
    sides: list[int]
    columns: list[int]
    rows: list[int]

    @classmethod
    def build_from(cls: type[Self], data: dict, column_names: ColumnNames) -> Self:  # type: ignore[type-arg]
        """Build `cls` from `dict`."""
        if column_names.callout is not None:
            callout = "CLC CREATIVE CORRUGATE" if data.get(column_names.callout) == "Yes" else ""
        else:
            callout = ""

        dc_target = data.get(column_names.date_column) if column_names.date_column is not None else ""

        return cls(
            parent_zppk=data.get(column_names.parent_zppk),  # type: ignore[arg-type]
            baby_zppk=data.get(column_names.baby_zppk),  # type: ignore[arg-type]
            team_key=data.get(column_names.team_key),  # type: ignore[arg-type]
            team_name=data.get(column_names.team_name),  # type: ignore[arg-type]
            requested_pallet_count=int(data.get(column_names.requested_pallet_count) or 0),
            dc_target=dc_target,  # type: ignore[arg-type]
            color_description=data.get(column_names.color_description),  # type: ignore[arg-type]
            logo_description=data.get(column_names.logo_description),  # type: ignore[arg-type]
            callout=callout,
            sides=_find_numbers_in_text(data.get(column_names.side, "1")),
            columns=_find_numbers_in_text(data.get(column_names.column)),  # type: ignore[arg-type]
            rows=_find_numbers_in_text(data.get(column_names.row)),  # type: ignore[arg-type]
        )


@dataclass(frozen=True, slots=True)
class PalletConfig:
    """Configuration of a pallet build."""

    zppk: str
    team_key: str
    team_name: str
    callout: str
    dc_target: str
    pallet_type: PalletType
    required_count: int
    sides: list[list[str]]

    @classmethod
    def build_from(cls: type[Self], rows: list[Row]) -> Self:
        """Build `cls` from `dict`."""
        last = rows.pop()

        return cls(
            callout=last.callout,
            dc_target=last.dc_target,
            zppk=rows[-1].parent_zppk,
            team_name=rows[-1].team_name,
            team_key=rows[-1].team_key,
            pallet_type=PalletType.TOWER,
            required_count=last.requested_pallet_count,
            sides=flip_pallet_sides(parse_sides(rows, repeat_columns=False)),
        )


def parse_sides(  # noqa: C901,PLR0912 -- split this up
    rows: list[Row],
    *,
    repeat_columns: bool = False,
) -> list[list[str]]:
    """Parse sides for half pallet."""
    column_designs_cache = {}
    sides = {}  # type: ignore[var-annotated]
    for row in rows:
        for side in row.sides:
            if row.columns[0] == 5:  # noqa: PLR2004 -- confirm what this does
                repeat_columns = True
                columns = [2] if side % 2 == 0 else [3]
            else:
                columns = row.columns
            columns = list(range(1, columns[0] + 1)) if repeat_columns else columns
            for column in columns:
                if side not in sides:
                    sides[side] = {}
                if column not in sides[side]:
                    sides[side][column] = []
                    column_designs_cache[side, column] = " ".join(
                        (
                            row.logo_description[:7],
                            row.color_description.replace(",", ""),
                            row.team_key,
                        ),
                    )
                sides[side][column].append(row.baby_zppk)

    last_used_design_number = None
    last_used_design_image = None
    output = []
    for side_key in sorted(sides.keys()):
        current_side = sides[side_key]
        for column_key in sorted(current_side.keys()):
            row = current_side[column_key]
            if len(row) > 4:  # noqa: PLR2004 -- temp
                row = row[-4:]
            with Session() as session:
                key_ = column_designs_cache[side_key, column_key]
                design_number = session.scalars(
                    select(OnSiteDesign.number).where(OnSiteDesign.title.ilike(f"{key_}%")),
                ).first()
            if design_number and design_number == last_used_design_number:
                image = last_used_design_image
            else:
                last_used_design_number = design_number
                if design_number is not None:
                    try:
                        image = get_image_for_design(design_number, (70, 70))
                    except Exception:  # noqa: BLE001
                        image = f"{key_=} {design_number=}"
                else:
                    image = f"{key_=} {design_number=}"
                last_used_design_image = image
            row.append(str(image))
            output.append(row)
    return output


def flip_pallet_sides(data: list[list[str]]) -> list[list[str]]:
    """Flip the sides on a pallet."""
    heads = ["XS (13) / S (13)", "M (30)", "L (32)", "XL (20)", "IMAGE"]
    output = []
    for index, head in enumerate(heads):
        output.append([head] + [lst[index] for lst in data])
    return output


async def generate_pallet_detail_sheets(
    pdfs_request: PDFsRequest,
) -> None:
    """Build and send a report."""
    raw_rows = list(csv.DictReader(StringIO(pdfs_request.file_data)))

    rows = [Row.build_from(raw_row, pdfs_request.column_names) for raw_row in raw_rows]
    row_groups = []
    group = []
    for row in rows:
        group.append(row)
        if row.requested_pallet_count != 0:
            row_groups.append(group)
            group = []

    pallet_configs = [PalletConfig.build_from(row_group) for row_group in row_groups]

    html_template = Environment(loader=PackageLoader("core"), autoescape=True).get_template("pallet.html")
    async with httpx.AsyncClient() as client:
        response = await client.get("https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css")
    cached_css = CSS(string=response.text)

    documents = []
    for pallet_config in pallet_configs:
        html = HTML(string=html_template.render(asdict(pallet_config)))
        documents.append(html.render(stylesheets=[cached_css]))
    all_pages = [page for document in documents for page in document.pages]
    bytes_ = documents[0].copy(all_pages).write_pdf()

    attachment = FileAttachment(
        name="details.pdf",
        content_type="application/pdf",
        content_bytes=bytes_,
    )

    await send_mail(
        recipient_addresses=[pdfs_request.email_address],
        subject="Details PDFs",
        content="<p>Please see your PDFs attached.</p>",
        attachments=[attachment],
    )