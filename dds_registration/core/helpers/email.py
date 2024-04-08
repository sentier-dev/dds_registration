import base64

from django.conf import settings
from fpdf import FPDF
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Attachment,
    Disposition,
    FileContent,
    FileName,
    FileType,
    Mail,
)


def send_email(
    recipient_address: str,
    subject: str,
    message: str,
    is_html: bool = False,
    from_email: str = settings.DEFAULT_FROM_EMAIL,
    pdf: FPDF | None = None,
    pdf_name: str | None = None,
) -> None:
    sg = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
    message = Mail(
        from_email=from_email,
        to_emails=recipient_address,
        subject=subject,
        plain_text_content=message,
    )
    if is_html:
        message.html_content = message
        # TODO: Create and replace plain text message copy?
    else:
        message.plain_text_content = message
    if pdf:
        if not pdf_name:
            raise ValueError("Must specify `pdf_name`")
        attachment = Attachment()
        attachment.file_content = FileContent(base64.b64encode(pdf.output()).decode())
        attachment.file_type = FileType("application/pdf")
        attachment.file_name = FileName(pdf_name)
        attachment.disposition = Disposition("attachment")
        message.attachment = attachment
    sg.send(message)
