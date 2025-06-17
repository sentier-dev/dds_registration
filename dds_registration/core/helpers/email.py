from typing import Any
import base64

from django.conf import settings
from email.message import EmailMessage
from fpdf import FPDF
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from loguru import logger

import base64
import mimetypes
import os
from email.message import EmailMessage
from email.mime.base import MIMEBase
from email.mime.text import MIMEText

import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


def get_creds() -> Any:  # Too lazy to look up proper type
    if not settings.GOOGLE_TOKEN_FILEPATH:
        return

    SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
    creds = Credentials.from_authorized_user_file(settings.GOOGLE_TOKEN_FILEPATH, SCOPES)

    if not creds.valid:
        creds.refresh(Request())

    return creds


def send_email(
    recipient_address: str,
    subject: str,
    message: str,
    is_html: bool = False,
    from_email: str = settings.DEFAULT_FROM_EMAIL,
    pdf: FPDF | None = None,
    pdf_name: str | None = None,
) -> None:
    logger.info("From email: {}".format(from_email))
    print("From email: {}".format(from_email))

    credentials = get_creds()
    if not credentials:
        logger.error("Can't find token file for email authorization")
        return

    service = build("gmail", "v1", credentials=get_creds())

    email_message = EmailMessage()
    email_message.set_content(message)

    email_message["To"] = recipient_address
    email_message["From"] = from_email
    email_message["Subject"] = subject

    if pdf:
        # Based on https://developers.google.com/workspace/gmail/api/guides/sending
        if not pdf_name:
            raise ValueError("Must specify `pdf_name`")
        email_message.add_attachment(
            pdf.output(),
            maintype="application",
            subtype="pdf",
            filename=pdf_name
        )

    encoded_message = base64.urlsafe_b64encode(email_message.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": encoded_message}).execute()
