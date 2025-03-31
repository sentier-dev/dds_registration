from datetime import date
from pathlib import Path
import tempfile
from fpdf import FPDF, Align
import qrcode
import qrcode.image.svg

from dds_registration.core.constants.people import certificate_signature, organization

BASE_DIR = Path(__file__).parent
DDS_LOGO = BASE_DIR / "images" / "pdf-template-logo.svg"

margin_size = 20  # Default margin size
left_column_pos = margin_size  # Position of the left top column
right_column_pos = 132  # Postion of the right top column
left_column_width = 75  # Width of the left top column
right_column_width = 55  # Width of the right top column
logo_width = 60  # Set logo width
top_offset = 30  # Top offset should exceed the logo height
font_size = 12


def normalize_text(text: str) -> str:
    return text.encode("utf-8", "ignore").decode("utf-8").strip()


def create_certificate_pdf(
    attendee_name: str,
    certificate_text: str,
    event_title: str,
    url: str,
    signature: str = certificate_signature,
    signature_file: Path = BASE_DIR / "images" / "hancock.png",
    logo_svg_path: Path = DDS_LOGO,
    issue_date: date | None = None,
    issuing_org: str = organization
) -> FPDF:
    if issue_date is None:
        issue_date = date.today()

    # Create pdf...
    pdf = FPDF(unit="mm", format="A4")

    pdf.add_font("NotoSans", style="", fname=BASE_DIR / "fonts" / "NotoSans-Regular.ttf")
    pdf.add_font("NotoSans", style="B", fname=BASE_DIR / "fonts" / "NotoSans-Bold.ttf")
    pdf.add_font("NotoSans", style="I", fname=BASE_DIR / "fonts" / "NotoSans-Italic.ttf")
    pdf.add_font("NotoSans", style="BI", fname=BASE_DIR / "fonts" / "NotoSans-BoldItalic.ttf")

    pdf.set_title("Certificate of Completion")
    pdf.set_margins(left=margin_size, top=margin_size, right=margin_size)

    # Get full page width (mm)...
    page_width = pdf.epw

    pdf.add_page()
    pdf.set_font("NotoSans", size=font_size)

    # Get derived dimensions...
    pdf_font_size = pdf.font_size
    line_height = pdf_font_size * 1.3
    vertical_space = line_height / 2
    large_vertical_space = vertical_space * 2
    small_vertical_space = vertical_space / 2

    # Put logo
    pdf.image(logo_svg_path, x=margin_size, y=margin_size, w=logo_width, keep_aspect_ratio=True)
    # @see https://py-pdf.github.io/fpdf2/fpdf/fpdf.html#fpdf.fpdf.FPDF.image
    # @see https://py-pdf.github.io/fpdf2/SVG.html

    pdf.set_xy(right_column_pos + 1, margin_size)
    pdf.multi_cell(
        text=normalize_text(issuing_org) + "\n" + issue_date.isoformat(),
        w=left_column_width,
        align=Align.L,
        new_x="LEFT",
        new_y="NEXT",
        h=line_height
    )

    pdf.set_font("NotoSans", "B", size=16)
    pdf.set_xy(20, pdf.get_y() + vertical_space * 2.5)
    pdf.multi_cell(
        text=normalize_text(event_title),
        w=page_width,
        align=Align.C,
        new_x="LEFT",
        new_y="NEXT",
        h=line_height,
    )

    pdf.set_font("NotoSans", size=font_size)
    pdf.set_y(pdf.get_y() + large_vertical_space)
    pdf.multi_cell(
        text=normalize_text(certificate_text.format(attendee_name=attendee_name)),
        markdown=True,
        w=page_width,
        align=Align.L,
        new_x="LEFT",
        new_y="NEXT",
        h=line_height,
    )

    signature_y = pdf.get_y() + large_vertical_space

    pdf.set_xy(left_column_pos + 8, signature_y + 8)
    pdf.cell(
        w=left_column_width,
        h=line_height,
        align=Align.L,
        text="Validation link",
        new_y="NEXT",
    )
    with tempfile.NamedTemporaryFile(suffix=".svg") as f:
        img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage)
        img.save(f.name)
        pdf.image(f.name, x=left_column_pos + 8, y=pdf.get_y(), w=30, keep_aspect_ratio=True)

    pdf.image(signature_file, x=right_column_pos + 1, y=signature_y + 8, h=12, keep_aspect_ratio=True)
    pdf.set_xy(right_column_pos + 1, signature_y + 8 + 12 + small_vertical_space)
    pdf.multi_cell(
        text=normalize_text(signature),
        w=left_column_width,
        align=Align.L,
        h=line_height,
    )

    return pdf
