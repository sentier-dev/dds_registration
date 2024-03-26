# @module dds_registration/views/membership.py
# @changed 2024.03.26, 17:04

import logging
import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import redirect, render

from ..core.helpers.errors import errorToString

from ..core.constants.stripe_payments import (
    academic_membership_stripe_payment_link,
    regular_membership_stripe_payment_link,
)

#  from ..core.helpers.create_invoice_pdf import create_invoice_pdf
#  from ..core.helpers.errors import errorToString

#  from .get_invoice_context import get_invoice_context

from ..models import Membership


LOG = logging.getLogger(__name__)


# TODO: Revoke membership?


class check_for_available_membership:
    """
    Check if it's possible to apply for a membership
    """

    response: None | HttpResponsePermanentRedirect | HttpResponseRedirect = None
    success: bool = False

    def __init__(self, request: HttpRequest):
        self.success = True  # Assume success by default
        user = request.user
        # Check for the existing membership...
        if user.is_authenticated:
            memberships = Membership.objects.filter(user=user)
            # Are there memberships for this user?
            if memberships and len(memberships):
                messages.success(request, "You're already a member or have been registered as a future member!")
                # TODO: Display the membership data on the profile page?
                self.response = redirect("profile")
                self.success = False

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass


def check_if_it_possible_to_become_a_member(request: HttpRequest):
    user = request.user
    # Check for the existing membership...
    if user.is_authenticated:
        memberships = Membership.objects.filter(user=user)
        # Has member user(s)?
        if memberships and len(memberships):
            messages.success(request, "You're already a member or have been registered as a future member!")
            # TODO: Display the membership data on the profile page?
            return redirect("profile")
    return None


def membership_start(request: HttpRequest):
    with check_for_available_membership(request) as checked:
        if checked.response:
            return checked.response
    # Display a membership options form...
    context = {
        "MEMBERSHIP_TYPES": Membership.MEMBERSHIP_TYPES,
        "membership_type": Membership.DEFAULT_MEMBERSHIP_TYPE,
    }
    return render(request, "dds_registration/membership_start.html.django", context)


@login_required
def membership_proceed(request: HttpRequest):
    try:
        user = request.user
        if not user.is_authenticated:
            messages.error(request, "Authorization is required in order to create a membership")
            return redirect("index")
        with check_for_available_membership(request) as checked:
            if checked.response:
                return checked.response
        # Proceed...
        membership_type = request.GET.get("membership_type")
        if not membership_type:
            messages.error(request, "You have to choose membership type")
            return redirect("membership_start")
        is_invoice = "INVLICE" in membership_type
        is_academic = "INVLICE" in membership_type
        debug_data = {
            "is_invoice": is_invoice,
            "is_academic": is_academic,
            "membership_type": membership_type,
            "request": request,
        }
        LOG.debug("membership_proceed: %s", debug_data)
        membership = Membership()
        membership.membership_type = membership_type
        membership.user = user
        membership.save()
        # Invoice option: show invoice result...
        if is_invoice:
            return redirect("membership_proceed_invoice")
        # Go to stripe site...
        stripe_link = academic_membership_stripe_payment_link if is_academic else regular_membership_stripe_payment_link
        return redirect(stripe_link)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        sTraceback = str(traceback.format_exc())
        error_text = "Can not proceed membership: {}".format(sError)
        messages.error(request, error_text)
        debug_data = {
            "err": err,
            "traceback": sTraceback,
            "sError": sError,
        }
        LOG.error("%s (redirecting to profile): %s", error_text, debug_data)
        # Redirect to profile page with error messages (see above)
        return redirect("profile")


@login_required
def membership_proceed_success(request: HttpRequest):
    context = {
        "action": "membership_proceed_success",
    }
    return render(request, "dds_registration/membership_proceed.html.django", context)


#  @login_required
#  def membership_proceed_invoice(request: HttpRequest):
#      # TODO: Generate invoice pdf
#      template = "dds_registration/membership_invoice.html.django"
#      context = get_invoice_context(request, event_code)
#      show_debug = False
#      if show_debug:
#          return render(request, template, context)
#      pdf = create_invoice_pdf(context)
#      return HttpResponse(bytes(pdf.output()), content_type="application/pdf")


__all__ = [
    membership_start,
    membership_proceed,
    membership_proceed_success,
]
