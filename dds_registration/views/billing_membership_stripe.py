# @module billing_membership_stripe.py
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


# Stripe payment for membership...


@csrf_exempt
def billing_membership_payment_stripe_create_checkout_session(
    request: HttpRequest, membership_type: str, currency: str, amount: float
):
    """
    Create stripe session for the membership.
    Called from js code on checkout page.
    """
    try:
        product_data = {
            # TODO: Get product name by membership type (or future membership option)
            "name": settings.STRIPE_PAYMENT_PRODUCT_NAME,
        }
        return_args = {
            "membership_type": membership_type,
            "session_id": "CHECKOUT_SESSION_ID_PLACEHOLDER",  # "{CHECKOUT_SESSION_ID}",  # To substitute by stripe
        }
        return_url = create_stripe_return_url(request, "billing_membership_stripe_payment_success", return_args)
        session = stripe.checkout.Session.create(
            line_items=[
                {
                    "price_data": {
                        "currency": currency,
                        "product_data": product_data,
                        # NOTE: The amount value is an integer, and (sic!) in cents (must be multiplied by 100)
                        "unit_amount": round(amount * 100),
                    },
                    "quantity": 1,
                }
            ],
            mode="payment",
            ui_mode="embedded",
            return_url=return_url,
        )
        result = {
            "clientSecret": session.client_secret,
        }
        return JsonResponse(result)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = "Cannot start checkout session for the membership: {}".format(sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (re-raising): %s", error_text, debug_data)
        raise Exception(error_text)


@login_required
def billing_membership_stripe_payment_success(request: HttpRequest, membership_type: str, session_id: str):
    """
    Proceed stripe payment.

    Show page with information about successfull payment creation and a link to
    proceed it.
    """
    context = get_membership_invoice_context(request)
    membership = context["membership"]
    total_price = context["total_price"]
    currency = context["currency"]
    invoice = context["invoice"]
    try:
        # Try to fetch stripe data...
        session = stripe.checkout.Session.retrieve(session_id)
        session_payment_status = session.get("payment_status")
        session_status = session.get("status")
        payment_success = session_payment_status == "paid" and session_status == "complete"
        # DEBUG...
        debug_data = {
            "payment_success": payment_success,
            "session": session,
            "session_payment_status": session_payment_status,
            "session_status": session_status,
            "membership_type": membership.membership_type,
            "session_id": session_id,
            "membership": membership,
            "invoice": invoice,
            "total_price": total_price,
            "currency": currency,
            "context": context,
        }
        LOG.debug("Start stripe payment: %s", debug_data)
        if not payment_success:
            messages.error(request, "Your payment was unsuccessfull")
            return redirect("billing_membership", membership_type=membership.membership_type)
        messages.success(request, "Your payment successfully proceed")
        # Update invoice status
        invoice.status = "PAID"
        # TODO: To save some payment details to invoice?
        invoice.save()
        # TODO:
        # Send email message?
        # Smth else?
        template = "dds_registration/billing/billing_membership_stripe_payment_success.html.django"
        return render(request, template, context)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = "Cannot start checkout session for the membership: {}".format(sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (re-raising): %s", error_text, debug_data)
        raise Exception(error_text)


@login_required
def billing_membership_stripe_payment_proceed(request: HttpRequest):
    """
    Proceed stripe payment for a membership: show embedded stripe form.
    """
    user = request.user
    if not user.is_authenticated:
        return redirect("index")
    # Find membership and invoice...
    membership: Membership = None
    #  invoice: Invoice = None
    try:
        membership = Membership.objects.get(user=user)
    except Membership.DoesNotExist:
        raise Exception("Membership does not exist")
    membership_type = membership.membership_type
    try:
        context = get_membership_invoice_context(request)
        total_price = context["total_price"]
        currency = context["currency"]
        debug_data = {
            "membership": membership,
            "total_price": total_price,
            "currency": currency,
            "context": context,
        }
        LOG.debug("Start stripe payment: %s", debug_data)
        # TODO: Create a view
        template = "dds_registration/billing/billing_membership_stripe_payment_proceed.html.django"
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
