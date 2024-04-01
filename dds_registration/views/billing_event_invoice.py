# @module billing_event_invoice.py
# @changed 2024.04.01, 23:57

import logging
import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site

import stripe

from django.conf import settings
from django.http import HttpRequest, HttpResponse

from ..core.helpers.create_invoice_pdf import create_invoice_pdf
from ..core.helpers.errors import errorToString

from ..forms import BillingEventForm, BillingMembershipForm
from ..models import Invoice, Membership

from .helpers import send_event_registration_success_message

from .get_invoice_context import (
    get_basic_event_registration_context,
    get_event_invoice_context,
    get_basic_membership_registration_context,
    get_membership_invoice_context,
)


#  stripe.api_key = settings.STRIPE_SECRET_KEY  # 'sk_...'


LOG = logging.getLogger(__name__)


# Invoice pdf...


@login_required
def billing_event_invoice_payment_proceed(request: HttpRequest, event_code: str):
    """
    Show page with information about successfull invoice creation and a link to
    download it.
    """
    context = get_basic_event_registration_context(request, event_code)
    invoice: Invoice = context["invoice"]
    # Issue #72: If the user paid by credit card, then redirect to their user account page with a flash message "Registration is complete".
    if invoice.payment_method != "INVOICE":
        messages.success(request, "Registration is complete")
        return redirect("profile")
    template = "dds_registration/billing/billing_event_invoice_payment_proceed.html.django"
    return render(request, template, context)


@login_required
def billing_event_invoice_download(request: HttpRequest, event_code: str):
    """
    Show page with information about successfull invoice creation and a link to
    download it.
    """
    context = get_event_invoice_context(request, event_code)
    show_debug = False
    if show_debug:
        # DEBUG: Show test page with prepared invoice data
        template = "dds_registration/billing/billing_event_invoice_download_debug.html.django"
        return render(request, template, context)
    pdf = create_invoice_pdf(context)
    return HttpResponse(bytes(pdf.output()), content_type="application/pdf")
