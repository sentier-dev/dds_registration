# @module billing_membership_invoice.py
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


# Invoice payment for the membership...


@login_required
def billing_membership_invoice_payment_proceed(request: HttpRequest):
    """
    Proceed invoice payment for a membership.
    """
    user = request.user
    if not user.is_authenticated:
        return redirect("index")
    # Find membership and invoice...
    membership: Membership = None
    invoice: Invoice = None
    try:
        membership = Membership.objects.get(user=user)
    except Membership.DoesNotExist:
        raise Exception("Membership does not exist")
    invoice = membership.invoice
    if not invoice:
        raise Exception("Invoice does not exist")
    try:
        #  total_price = context["total_price"]
        currency = invoice.currency
        context = {
            "membership": membership,
            "invoice": invoice,
        }
        debug_data = {
            "membership": membership,
            "invoice": invoice,
            "context": context,
        }
        LOG.debug("Start invoice payment: %s", debug_data)
        template = "dds_registration/billing/billing_membership_invoice_payment_proceed.html.django"
        return render(request, template, context)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = "Cannot create invoice page for the membership: {}".format(sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (re-raising): %s", error_text, debug_data)
        raise Exception(error_text)


@login_required
def billing_membership_invoice_download(request: HttpRequest):
    """
    Show page with information about successfull invoice creation and a link to
    download it.
    """
    user = request.user
    context = get_membership_invoice_context(request)
    try:
        show_debug = False
        if show_debug:
            # DEBUG: Show test page with prepared invoice data
            template = "dds_registration/billing/billing_membership_invoice_download_debug.html.django"
            return render(request, template, context)
        pdf = create_invoice_pdf(context)
        return HttpResponse(bytes(pdf.output()), content_type="application/pdf")
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = "Error: {}".format(sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (re-raising): %s", error_text, debug_data)
        raise Exception(error_text)
