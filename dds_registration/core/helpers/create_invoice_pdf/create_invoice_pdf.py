# -*- coding: utf-8 -*-
from datetime import date
from pathlib import Path

from fpdf import FPDF, Align

from ...constants.payments import (
    default_payment_deadline_days,
    payment_recipient_address,
    payment_recipient_name,
)

__all__ = [
    "create_invoice_pdf",
]

BASE_DIR = Path(__file__).resolve().parent
DDS_LOGO = BASE_DIR / "images" / "pdf-template-logo.svg"

# Core constants/options

col_widths = (15, 45, 20, 20)  # Table column widths
margin_size = 20  # Default margin size
left_column_pos = margin_size  # Position of the left top column
right_column_pos = 132  # Postion of the right top column
left_column_width = 75  # Width of the left top column
right_column_width = 55  # Width of the right top column
logo_width = 60  # Set logo width
top_offset = 30  # Top offset should exceed the logo height
font_size = 12


def create_invoice_pdf(
    client_name: str,
    client_address: str,
    invoice_number: int,
    items: list,
    recipient_account: str,
    invoice_date: date | None = None,
    extra: str = "",
    recipient_name: str = payment_recipient_name,
    recipient_address: str = payment_recipient_address,
    payment_days: int = default_payment_deadline_days,
    logo_svg_path: Path = DDS_LOGO,
) -> FPDF:

    if invoice_date is None:
        invoice_date = date.today()

    # Get params...
    #  currency = params["currency"]
    # optional_text = params["optional_text"]
    # client_name = params["client_name"]
    # client_address = params["client_address"]
    # dds_name = params["dds_name"]
    # dds_address = params["dds_address"]
    # invoice_no = params["invoice_no"]
    # invoice_date = params["invoice_date"]
    # payment_terms = params["payment_terms"]
    # payment_details = params["payment_details"]
    # table_data = params["table_data"]

    # Create pdf...
    pdf = FPDF(unit="mm", format="A4")
    pdf.set_title("Invoice {} ({})".format(invoice_number, client_name))
    pdf.set_margins(left=margin_size, top=margin_size, right=margin_size)

    # Get full page width (mm)...
    page_width = pdf.epw

    pdf.add_page()
    pdf.set_font("times", size=font_size)

    # Get derived dimensions...
    pdf_font_size = pdf.font_size
    line_height = pdf_font_size * 1.3
    vertical_space = line_height / 2
    large_vertical_space = vertical_space * 2
    small_vertical_space = vertical_space / 2
    tiny_vertical_space = vertical_space / 4

    # Put logo
    pdf.image(logo_svg_path, x=right_column_pos + 1, y=margin_size, w=logo_width, keep_aspect_ratio=True)
    # @see https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image
    # @see https://py-pdf.github.io/fpdf2/SVG.html

    # Left (client) address column...
    pdf.set_xy(left_column_pos, margin_size + top_offset)
    pdf.multi_cell(text=client_name, w=left_column_width, align=Align.L, new_x="LEFT", new_y="NEXT", h=line_height)

    pdf.set_y(pdf.get_y() + small_vertical_space)
    pdf.multi_cell(
        text=client_address.strip(), w=left_column_width, align=Align.L, new_x="LEFT", new_y="NEXT", h=line_height
    )

    left_stop_pos = pdf.get_y()

    # Right (client) address column...
    pdf.set_xy(right_column_pos, margin_size + top_offset)
    pdf.multi_cell(text=recipient_name, w=right_column_width, align=Align.L, new_x="LEFT", new_y="NEXT", h=line_height)

    pdf.set_xy(right_column_pos, pdf.get_y() + small_vertical_space)
    pdf.multi_cell(
        text=recipient_address.strip(), w=right_column_width, align=Align.L, new_x="LEFT", new_y="NEXT", h=line_height
    )

    right_stop_pos = pdf.get_y()

    # Choose the most bottom position of two top columns...
    max_right_top = max(left_stop_pos, right_stop_pos)

    # Put the title (invoice no), with an extra offset...
    pdf.set_xy(left_column_pos, max_right_top + large_vertical_space)
    pdf.multi_cell(
        text="Invoice " + invoice_number, w=left_column_width, align=Align.L, new_x="LEFT", new_y="NEXT", h=line_height
    )

    pdf.set_y(pdf.get_y() + vertical_space)

    # Set gray color for table border
    pdf.set_draw_color(200)

    # @see https://py-pdf.github.io/fpdf2/Tables.html
    with pdf.table(
        col_widths=col_widths,
        text_align="LEFT",
        line_height=line_height,
        padding=2,
        markdown=True,
        v_align="T",
        # Stripped background
        cell_fill_color=240,
        cell_fill_mode="ROWS",
    ) as table:
        for data_row in items:
            row = table.row()
            for data in data_row:
                row.cell(str(data))

    # Put bottom texts...

    pdf.set_y(pdf.get_y() + small_vertical_space)

    pdf.set_y(pdf.get_y() + small_vertical_space)
    pdf.multi_cell(
        text="Invoice date: " + invoice_date.strftime("%Y-%m-%d"), w=page_width, align=Align.L, new_x="LEFT", new_y="NEXT", h=line_height
    )

    if payment_days:
        pdf.set_y(pdf.get_y() + small_vertical_space)
        pdf.multi_cell(
            text=f"Payment terms: {payment_days} calendar days",
            markdown=True,
            w=page_width,
            align=Align.L,
            new_x="LEFT",
            new_y="NEXT",
            h=line_height,
        )

    pdf.set_y(pdf.get_y() + small_vertical_space)
    pdf.multi_cell(
        text="**Bank account details:**",
        markdown=True,
        w=page_width,
        align=Align.L,
        new_x="LEFT",
        new_y="NEXT",
        h=line_height,
    )
    pdf.set_y(pdf.get_y() + tiny_vertical_space)
    pdf.multi_cell(
        text=recipient_account.strip(),
        markdown=True,
        w=page_width,
        align=Align.L,
        new_x="LEFT",
        new_y="NEXT",
        h=line_height,
    )

    if extra:
        pdf.set_y(pdf.get_y() + large_vertical_space)
        pdf.multi_cell(
            text="__{}__".format(extra),
            markdown=True,
            w=page_width,
            align=Align.L,
            new_x="LEFT",
            new_y="NEXT",
            h=line_height,
        )

    return pdf
