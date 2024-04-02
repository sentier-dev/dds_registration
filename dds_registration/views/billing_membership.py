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

from ..forms import BillingMembershipForm
from ..models import Invoice, Membership

from .membership import send_membership_registration_success_message


LOG = logging.getLogger(__name__)


# Membership...


@login_required
def billing_membership(request: HttpRequest, membership_type: str):
    """
    Basic form to create invoice and/or payment for membership.
    """
    try:
        user = request.user
        if not user.is_authenticated:
            return redirect("index")

        # Find or create membership immediatelly
        is_new_membership = False
        membership: Membership | None = None
        memberships = Membership.objects.filter(user=user)
        if len(memberships):
            membership = memberships[0]
        if not membership:
            is_new_membership = True
            membership = Membership()
            membership.user = user
        membership.membership_type = membership_type
        membership.save()

        # Find or create invoice
        is_new_invoice = False
        invoice: Invoice = membership.invoice
        if not invoice:
            is_new_invoice = True
            # Create default invoice and initialize default values...
            invoice = Invoice()
            invoice.name = user.get_full_name()
            invoice.address = user.address

        # If user posted his data...
        if request.method == "POST":
            # Create a form instance and populate it with data from the request:
            form = BillingMembershipForm(request.POST, instance=invoice)
            # Check whether it's valid:
            if form.is_valid():
                cleaned_data = form.cleaned_data
                invoice = form.save()
                debug_data = {
                    "cleaned_data": cleaned_data,
                    "invoice": invoice,
                }
                LOG.debug("Get form data: %s", debug_data)
                new_verb = "created" if is_new_invoice else "updated"
                messages.success(request, "Invoice has been successfully " + new_verb)
                # TODO: What if changing an existing invoice and the `payment_method` parameter has changed? Should we provide for actions in such a case?
                invoice.save()
                # Update membership...
                membership.invoice = invoice  # Link the invoice
                #  membership.status = "PAYMENT_PENDING"  # Change the status -- now we're expecting the payment
                membership.save()
                # Send an e-mail message...
                send_membership_registration_success_message(request)
                # Redirect to invoice downloading or to payment page?
                if invoice.payment_method == "INVOICE":
                    return redirect("billing_membership_invoice_payment_proceed")
                else:
                    return redirect("billing_membership_stripe_payment_proceed")
        else:
            form = BillingMembershipForm(instance=invoice)
        context = {
            "membership": membership,
            "invoice": invoice,
            "form": form,
        }
        template = "dds_registration/billing/billing_membership_form.html.django"
        return render(request, template, context)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = 'Cannot process billing for the membership "{}": {}'.format(membership_type, sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "membership_type": membership_type,
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (re-raising): %s", error_text, debug_data)
        raise Exception(error_text)
