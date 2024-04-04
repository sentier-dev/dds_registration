# @module dds_registration/views/membership.py
# @changed 2024.04.02, 15:05

import logging
import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.template.loader import render_to_string

from .helpers.check_for_available_membership import check_for_available_membership

from ..core.helpers.errors import errorToString
from ..core.helpers.create_invoice_pdf import create_invoice_pdf

from ..models import Membership

from .get_invoice_context import get_membership_invoice_context


LOG = logging.getLogger(__name__)


# TODO: Revoke membership feature?


def membership_start(request: HttpRequest):
    try:
        user = request.user
        # Go to the login page with a message if no logged user:
        if not user or not user.is_authenticated:
            messages.error(request, "You have to have an account before you can register for membership")
            return redirect("login")
        with check_for_available_membership(request) as checked:
            if checked.response:
                return checked.response
        # Display a membership options form...
        MEMBERSHIP_TYPES = Membership.get_available_membership_types()
        context = {
            "MEMBERSHIP_TYPES": MEMBERSHIP_TYPES,
            "membership_type": Membership.DEFAULT_MEMBERSHIP_TYPE,
        }
        LOG.debug("membership_start: %s", context)
        return render(request, "dds_registration/membership_start.html.django", context)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        sTraceback = str(traceback.format_exc())
        error_text = "Cannot start membership: {}".format(sError)
        messages.error(request, error_text)
        debug_data = {
            "err": err,
            "traceback": sTraceback,
            "sError": sError,
        }
        LOG.error("%s (re-raising): %s", error_text, debug_data)
        raise err


@login_required
def membership_proceed_success(request: HttpRequest):
    context = {
        "action": "membership_proceed_success",
    }
    return render(request, "dds_registration/membership_test.html.django", context)


def send_membership_registration_success_message(request: HttpRequest):
    """
    Send successful membership registration message to the user

    TODO: Send different messages depending on the `payment_method`?
    """

    email_body_template = "dds_registration/membership_registration_new_success_message_body.txt"
    email_subject_template = "dds_registration/membership_registration_new_success_message_subject.txt"

    user = request.user

    context = get_membership_invoice_context(request)

    invoice = context.get("invoice")

    try:
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

        if invoice.payment_method == "INVOICE" and invoice.status in ("ISSUED", "CREATED"):
            user.email_user(
                subject=subject,
                message=body,
                attachment_content=create_invoice_pdf(context),
                attachment_name="DdS Membership Invoice {}.pdf".format(user.get_full_name()),
            )
            invoice.status = "ISSUED"
            invoice.save()
        else:
            user.email_user(subject=subject, message=body)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("Caught error %s (re-raising): %s", sError, debug_data)
        raise err
