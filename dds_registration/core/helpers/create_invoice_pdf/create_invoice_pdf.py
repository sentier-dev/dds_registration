# -*- coding: utf-8 -*-
from pathlib import Path
from fpdf import FPDF, Align
from typing import TypedDict
import posixpath

__all__ = [
    "TInvoicePdfParams",
    "create_invoice_pdf",
]

BASE_DIR = Path(__file__).resolve().parent


class TInvoicePdfParams(TypedDict):
    #  currency: str;
    optional_text: str
    client_name: str
    client_address: str
    dds_name: str
    dds_address: str
    invoice_no: str
    invoice_date: str
    payment_terms: str
    payment_details: str
    # Services table
    table_data: tuple[tuple[str, str, str, str]]


# Core constants/options

col_widths = (15, 45, 20, 20)  # Table column widths

logo_svg_file = "images/pdf-template-logo.svg"

margin_size = 20  # Default margin size

left_column_pos = margin_size  # Position of the left top column
right_column_pos = 132  # Postion of the right top column
left_column_width = 75  # Width of the left top column
right_column_width = 55  # Width of the right top column

logo_width = 60  # Set logo width
top_offset = 30  # Top offset should exceed the logo height

font_size = 12


def create_invoice_pdf(params: TInvoicePdfParams) -> FPDF:
    # Get params...
    #  currency = params["currency"]
    optional_text = params["optional_text"]
    client_name = params["client_name"]
    client_address = params["client_address"]
    dds_name = params["dds_name"]
    dds_address = params["dds_address"]
    invoice_no = params["invoice_no"]
    invoice_date = params["invoice_date"]
    payment_terms = params["payment_terms"]
    payment_details = params["payment_details"]
    table_data = params["table_data"]

    # Create pdf...
    pdf = FPDF(unit="mm", format="A4")

    pdf.set_title("Invoice {} ({})".format(invoice_no, client_name))

    # Set pdf margins...
    pdf.set_margins(left=margin_size, top=margin_size, right=margin_size)

    # Get full page width (mm)...
    page_width = pdf.epw

    # Create page...
    pdf.add_page()

    # Set font...
    pdf.set_font("times", size=font_size)

    # Get derived dimensions...
    pdf_font_size = pdf.font_size
    line_height = pdf_font_size * 1.3
    vertical_space = line_height / 2
    large_vertical_space = vertical_space * 2
    small_vertical_space = vertical_space / 2
    tiny_vertical_space = vertical_space / 4

    # Put logo
    logo_svg_path = posixpath.join(BASE_DIR, logo_svg_file)
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
    pdf.multi_cell(text=dds_name, w=right_column_width, align=Align.L, new_x="LEFT", new_y="NEXT", h=line_height)

    pdf.set_xy(right_column_pos, pdf.get_y() + small_vertical_space)
    pdf.multi_cell(
        text=dds_address.strip(), w=right_column_width, align=Align.L, new_x="LEFT", new_y="NEXT", h=line_height
    )

    right_stop_pos = pdf.get_y()

    # Choose the most bottom position of two top columns...
    max_right_top = max(left_stop_pos, right_stop_pos)

    # Put the title (invoice no), with an extra offset...
    pdf.set_xy(left_column_pos, max_right_top + large_vertical_space)
    pdf.multi_cell(
        text="Invoice " + invoice_no, w=left_column_width, align=Align.L, new_x="LEFT", new_y="NEXT", h=line_height
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
        for data_row in table_data:
            row = table.row()
            for data in data_row:
                row.cell(str(data))

    # Put bottom texts...

    pdf.set_y(pdf.get_y() + small_vertical_space)

    if invoice_date:
        pdf.set_y(pdf.get_y() + small_vertical_space)
        pdf.multi_cell(
            text="Invoice date: " + invoice_date, w=page_width, align=Align.L, new_x="LEFT", new_y="NEXT", h=line_height
        )

    if payment_terms:
        pdf.set_y(pdf.get_y() + small_vertical_space)
        pdf.multi_cell(
            text="Payment terms: " + payment_terms,
            markdown=True,
            w=page_width,
            align=Align.L,
            new_x="LEFT",
            new_y="NEXT",
            h=line_height,
        )

    if payment_details:
        pdf.set_y(pdf.get_y() + small_vertical_space)
        pdf.multi_cell(
            text="**Payment details:**",
            markdown=True,
            w=page_width,
            align=Align.L,
            new_x="LEFT",
            new_y="NEXT",
            h=line_height,
        )
        pdf.set_y(pdf.get_y() + tiny_vertical_space)
        pdf.multi_cell(
            text=payment_details.strip(),
            markdown=True,
            w=page_width,
            align=Align.L,
            new_x="LEFT",
            new_y="NEXT",
            h=line_height,
        )

    if optional_text:
        pdf.set_y(pdf.get_y() + large_vertical_space)
        pdf.multi_cell(
            text="__{}__".format(optional_text),
            markdown=True,
            w=page_width,
            align=Align.L,
            new_x="LEFT",
            new_y="NEXT",
            h=line_height,
        )

    return pdf
