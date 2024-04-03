# @module billing_event_stripe.py
# @changed 2024.04.01, 23:57

import logging
import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

import stripe

from django.conf import settings
from django.http import HttpRequest

from .helpers.create_stripe_return_url import create_stripe_return_url

from ..core.helpers.errors import errorToString

from .get_invoice_context import get_event_invoice_context


LOG = logging.getLogger(__name__)


# Stripe payment for event...


def start_stripe_payment_intent(
    request: HttpRequest,
    currency: str,
    amount: float,
    payment_data: dict,
    #  return_url: str, # ???
):
    try:
        user = request.user
        extra_metadata = {
            "user_id": user.id,
            "user_email": user.email,
            #  "event_code": event_code,
            "currency": currency,
            "amount": amount,
        }
        # @see https://docs.stripe.com/api/metadata
        metadata = dict(payment_data, **extra_metadata)
        amount_in_cents = round(amount * 100)
        # @see https://docs.stripe.com/api/payment_intents/create
        session = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency=currency,
            #  automatic_payment_methods={"enabled": True},  # This is default
            metadata=metadata,
        )
        #  Reponse example (see https://docs.stripe.com/api/payment_intents/object):
        #  {
        #    "id": "pi_3MtwBwLkdIwHu7ix28a3tqPa",
        #    "object": "payment_intent",
        #    "amount": 2000,
        #    "amount_capturable": 0,
        #    "amount_details": {
        #      "tip": {}
        #    },
        #    "amount_received": 0,
        #    "application": null,
        #    "application_fee_amount": null,
        #    "automatic_payment_methods": {
        #      "enabled": true
        #    },
        #    "canceled_at": null,
        #    "cancellation_reason": null,
        #    "capture_method": "automatic",
        #    "client_secret": "pi_3MtwBwLkdIwHu7ix28a3tqPa_secret_YrKJUKribcBjcG8HVhfZluoGH",
        #    "confirmation_method": "automatic",
        #    "created": 1680800504,
        #    "currency": "usd",
        #    "customer": null,
        #    "description": null,
        #    "invoice": null,
        #    "last_payment_error": null,
        #    "latest_charge": null,
        #    "livemode": false,
        #    "metadata": {},
        #    "next_action": null,
        #    "on_behalf_of": null,
        #    "payment_method": null,
        #    "payment_method_options": {
        #      "card": {
        #        "installments": null,
        #        "mandate_options": null,
        #        "network": null,
        #        "request_three_d_secure": "automatic"
        #      },
        #      "link": {
        #        "persistent_token": null
        #      }
        #    },
        #    "payment_method_types": [
        #      "card",
        #      "link"
        #    ],
        #    "processing": null,
        #    "receipt_email": null,
        #    "review": null,
        #    "setup_future_usage": null,
        #    "shipping": null,
        #    "source": null,
        #    "statement_descriptor": null,
        #    "statement_descriptor_suffix": null,
        #    "status": "requires_payment_method",
        #    "transfer_data": null,
        #    "transfer_group": null
        #  }
        result = {
            #  "id": session.id,
            "client_secret": session.client_secret,
        }
        return result
        #  return JsonResponse(result)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = 'Cannot start stripe intent session for "{}": {}'.format(payment_data, sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (re-raising): %s", error_text, debug_data)
        raise Exception(error_text)


#  # OBSOLETE
#  @csrf_exempt
#  def billing_event_payment_stripe_create_checkout_session(
#      request: HttpRequest, event_code: str, currency: str, amount: float
#  ):
#      """
#      NOTE: We don't need this method for intent api: we can create session in the backend view of payment form.
#
#      Create stripe session.
#      Called from js code on checkout page.
#
#      TODO: To use `PaymentIntent` instead of `checkout.Session`?
#
#      @see: https://docs.stripe.com/payments/accept-a-payment?platform=web&ui=elements
#      """
#      try:
#          user = request.user
#          if not user.is_authenticated:
#              raise Exception('Expected authorized user')
#          #  product_data = {
#          #      # TODO: Set product name by event registration type?
#          #      "name": settings.STRIPE_PAYMENT_PRODUCT_NAME,
#          #  }
#          #  return_args = {
#          #      "event_code": event_code,
#          #      "session_id": "CHECKOUT_SESSION_ID_PLACEHOLDER",  # "{CHECKOUT_SESSION_ID}",  # To substitute by stripe
#          #  }
#          #  return_url = create_stripe_return_url(request, "billing_event_stripe_payment_success", return_args)
#          #  amount_in_cents = round(amount * 100)
#          #  # XXX: Issue #93: Old way
#          #  session = stripe.checkout.Session.create(
#          #      line_items=[
#          #          {
#          #              "price_data": {
#          #                  "currency": currency,
#          #                  "product_data": product_data,
#          #                  # NOTE: The amount value is an integer, and (sic!) in cents (must be multiplied by 100)
#          #                  "unit_amount": amount_in_cents,
#          #              },
#          #              "quantity": 1,
#          #          }
#          #      ],
#          #      mode="payment",
#          #      ui_mode="embedded",
#          #      return_url=return_url,
#          #  )
#          payment_data = {
#              "event_code": event_code,
#          }
#          intent_session = start_stripe_payment_intent(
#              request=request,
#              currency=currency,
#              amount=amount,
#              payment_data=payment_data,
#              #  return_url: str, # ???
#          )
#          return JsonResponse(intent_session)
#      except Exception as err:
#          sError = errorToString(err, show_stacktrace=False)
#          error_text = 'Cannot start checkout session for the event "{}": {}'.format(event_code, sError)
#          messages.error(request, error_text)
#          sTraceback = str(traceback.format_exc())
#          debug_data = {
#              "event_code": event_code,
#              "err": err,
#              "traceback": sTraceback,
#          }
#          LOG.error("%s (re-raising): %s", error_text, debug_data)
#          raise Exception(error_text)


@login_required
def billing_event_stripe_payment_proceed(request: HttpRequest, event_code: str):
    """
    Proceed stripe payment for event registration.
    """
    try:
        context = get_event_invoice_context(request, event_code)
        event = context["event"]
        registration = context["registration"]
        total_price = context["total_price"]
        currency = context["currency"]
        payment_data = {
            "event_code": event_code,
        }
        intent_session = start_stripe_payment_intent(
            request=request,
            currency=currency,
            amount=total_price,
            payment_data=payment_data,
            #  return_url: str, # ???
        )
        context.update(intent_session)
        debug_data = {
            "event": event,
            "registration": registration,
            "total_price": total_price,
            "currency": currency,
            "context": context,
        }
        LOG.debug("Start stripe payment: %s", debug_data)
        # Make a payment to stripe
        template = "dds_registration/billing/billing_event_stripe_payment_proceed.html.django"
        return render(request, template, context)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = 'Cannot start stripe intent session for "{}": {}'.format(payment_data, sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (re-raising): %s", error_text, debug_data)
        raise Exception(error_text)


@login_required
def billing_event_stripe_payment_success(request: HttpRequest, event_code: str):  # , session_id: str):
    """
    Proceed stripe payment.

    Show page with information about successfull payment creation and a link to
    proceed it.
    """
    context = get_event_invoice_context(request, event_code)
    event = context["event"]
    registration = context["registration"]
    total_price = context["total_price"]
    currency = context["currency"]
    invoice = context["invoice"]
    try:
        # XXX: Issue #93: Old way: session isn't used for intent api
        #  # Try to fetch stripe data...
        #  session = stripe.checkout.Session.retrieve(session_id)
        #  session_payment_status = session.get("payment_status")
        #  session_status = session.get("status")
        #  payment_success = session_payment_status == "paid" and session_status == "complete"
        # DEBUG...
        debug_data = {
            #  "payment_success": payment_success,
            #  "session": session,
            #  "session_payment_status": session_payment_status,
            #  "session_status": session_status,
            #  "session_id": session_id,
            "event_code": event_code,
            "event": event,
            "registration": registration,
            "invoice": invoice,
            "total_price": total_price,
            "currency": currency,
            "context": context,
        }
        LOG.debug("Start stripe payment: %s", debug_data)
        #  # XXX: Issue #93: Old way: session isn't used for intent api
        #  if not payment_success:
        #      messages.error(request, "Your payment was unsuccessfull")
        #      return redirect("billing_event", event_code=event_code)
        messages.success(request, "Your payment successfully proceed")
        # Update invoice status
        invoice.status = "PAID"
        # TODO: To save some payment details to invoice?
        invoice.save()
        # @see Issues #94, #96
        # TODO: Invoice should be saved earlier. Create and save invoice pdf and datastamp (into the `data` filed), add it as attachment to the email message
        # Check where we're sending emails?
        template = "dds_registration/billing/billing_event_stripe_payment_success.html.django"
        return render(request, template, context)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = 'Cannot start checkout session for the event "{}": {}'.format(event_code, sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "event_code": event_code,
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (re-raising): %s", error_text, debug_data)
        raise Exception(error_text)
