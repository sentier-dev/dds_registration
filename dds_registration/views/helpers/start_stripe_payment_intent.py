# @module start_stripe_payment_intent.py
# @changed 2024.04.04, 00:25

import logging
import traceback

from django.contrib import messages
from django.http import HttpRequest

import stripe

from django.http import HttpRequest

from ...core.helpers.errors import errorToString


LOG = logging.getLogger(__name__)


def initiate_stripe_payment(
    request: HttpRequest,
    amount_in_cents: int,
    currency: str,
    metadata: dict,
) -> stripe.PaymentIntent:
    user = request.user
    try:
        # TODO: Probably it'd be better to use old approach: to start payment and to fetch the secret via async ajax request: this operation requires a noticeable time (up to 1-2 seconds required to open the page)
        # @see https://docs.stripe.com/api/metadata
        # @see https://docs.stripe.com/api/payment_intents/create
        intent = stripe.PaymentIntent.create(
            amount=amount_in_cents,
            currency=currency,
            #  automatic_payment_methods={"enabled": True},  # This is default
            metadata=metadata,
            # NOTE: Issue #103: Send automatic email receipt
            # @see: https://docs.stripe.com/api/payment_intents/confirm#confirm_payment_intent-receipt_email
            receipt_email=user.email,
        )
        #  The `PaymentIntent` result example (see https://docs.stripe.com/api/payment_intents/object):
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
        return intent
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = "Cannot initiate stripe payment intent: {}".format(sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (re-raising): %s", error_text, debug_data)
        raise Exception(error_text)


def start_stripe_payment_intent(
    request: HttpRequest,
    currency: str,
    amount: float,
    payment_data: dict = {},
):
    user = request.user
    extra_metadata = {
        "user_id": user.id,
        "user_email": user.email,
        "currency": currency,
        "amount": amount,
    }
    # @see https://docs.stripe.com/api/metadata
    metadata = dict(payment_data, **extra_metadata)
    amount_in_cents = round(amount * 100)
    try:
        intent = initiate_stripe_payment(
            request,
            amount_in_cents,
            currency,
            metadata,
        )
        result = {
            "client_secret": intent.client_secret,
        }
        return result
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
