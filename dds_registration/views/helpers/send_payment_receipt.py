# @module send_payment_receipt.py
# @changed 2024.04.04, 20:00

import logging
import traceback

from django.conf import settings
from django.contrib import messages
from django.http import HttpRequest
from django.template.loader import render_to_string

from django.http import HttpRequest

from ...core.helpers.create_invoice_pdf import create_invoice_pdf
from ...core.helpers.errors import errorToString


LOG = logging.getLogger(__name__)


def send_payment_receipt(
    request: HttpRequest,
    email_body_template: str,
    email_subject_template: str,
    context: dict,
):
    user = request.user
    invoice = context.get("invoice")
    from_email = settings.DEFAULT_FROM_EMAIL
    try:
        debug_data = {
            "email_body_template": email_body_template,
            "email_subject_template": email_subject_template,
            "context": context,
        }
        LOG.debug("Data: %s", debug_data)
        # Create message subject and body...
        subject = render_to_string(
            template_name=email_subject_template,
            context=context,
            request=request,
        )
        subject = " ".join(subject.splitlines()).strip()
        body = render_to_string(
            template_name=email_body_template,
            context=context,
            request=request,
        )
        # Create pdf invoice to attach...
        pdf = create_invoice_pdf(context)
        debug_data = {
            "pdf": pdf,
            "invoice": invoice,
            "subject": subject,
            "body": body,
            "context": context,
        }
        LOG.debug("Mail user: %s", debug_data)
        user.email_user(subject, body, attachment_content=pdf, attachment_name="invoice.pdf")
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = "Cannot send pyment receipt: {}".format(sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (re-raising): %s", error_text, debug_data)
        raise Exception(error_text)
