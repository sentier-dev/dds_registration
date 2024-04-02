# @module dds_registration/views/billing.py
# @changed 2024.03.29, 18:16

import logging
import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import redirect, render


from django.http import HttpRequest

from ..core.helpers.errors import errorToString

from ..forms import BillingEventForm
from ..models import Invoice

from .helpers.events import send_event_registration_success_message

from .get_invoice_context import (
    get_basic_event_registration_context,
)


LOG = logging.getLogger(__name__)


# Basic billing form...


@login_required
def billing_event(request: HttpRequest, event_code: str):
    """
    Basic form to create invoice and/or payment.

    Show the form to select payment options:
    - RegistrationOption (from available ones for this event)
    - `payment_method`: Payment method (either Credit Card or Invoice)
    - `extra_invoice_text`: Extra information they might want to add to the
      Invoice (help text is "Any additional text for the invoice, such as a
      reference or purchase order number").

    Form should display the name and address that we have for that user account.

    Users must be logged in, and registered for the event - otherwise they get
    redirected to the homepage.

    If they are registered, then they have chosen a RegistrationOption, so we
    can use that to look up the price and currency.

    """
    try:
        user = request.user
        if not user.is_authenticated:
            return redirect("index")
        # TODO: Check if invoice has been already created?
        context = get_basic_event_registration_context(request, event_code)
        # TODO: Catch registration doesn't exist
        # event = context["event"]
        registration = context["registration"]
        invoice = context["invoice"]
        is_new = False
        if not invoice:
            is_new = True
            # Create default invoice and initialize default values...
            invoice = Invoice()
            invoice.name = user.get_full_name()
            invoice.address = user.address
        # Set currency from registration option (Issue #86)
        invoice.currency = registration.option.currency
        # Check redirects...
        context_redirect = context.get("redirect")
        if context_redirect:
            return context_redirect
        if request.method == "POST":
            # Create a form instance and populate it with data from the request:
            form = BillingEventForm(request.POST, instance=invoice)
            # Check whether it's valid:
            if form.is_valid():
                cleaned_data = form.cleaned_data
                invoice = form.save()
                #  debug_data = {
                #      "cleaned_data": cleaned_data,
                #      "invoice": invoice,
                #  }
                #  LOG.debug("Get form data: %s", debug_data)
                new_verb = "created" if is_new else "updated"
                messages.success(request, "Invoice has been successfully " + new_verb)
                # TODO: What if changing an existing invoice and the `payment_method` parameter has changed? Should we provide for actions in such a case?
                invoice.save()
                # Update registration...
                registration.invoice = invoice  # Link the invoice
                registration.status = "PAYMENT_PENDING"  # Change the status -- now we're expecting the payment
                registration.save()
                # Send an e-mail message (if registration has been created/updated)...
                send_event_registration_success_message(request, event_code)
                # Redirect to invoice downloading or to payment page?
                if invoice.payment_method == "INVOICE":
                    return redirect("billing_event_invoice_payment_proceed", event_code=event_code)
                else:
                    return redirect("billing_event_stripe_payment_proceed", event_code=event_code)
        else:
            form = BillingEventForm(instance=invoice)
        context["form"] = form
        template = "dds_registration/billing/billing_event_form.html.django"
        return render(request, template, context)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = 'Cannot process billing for the event "{}": {}'.format(event_code, sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "event_code": event_code,
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (re-raising): %s", error_text, debug_data)
        raise Exception(error_text)
