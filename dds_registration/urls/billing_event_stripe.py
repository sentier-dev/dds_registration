# @module dds_registration/urls/billing_event_stripe.py
# @changed 2024.04.03, 15:50

from django.urls import path, register_converter

from ..views import billing_event_stripe as billing_event_stripe_views


from ..converters.FloatUrlParameterConverter import FloatUrlParameterConverter

register_converter(FloatUrlParameterConverter, "float")

urlpatterns = [
    path(
        # Proceed stripe payment
        "billing/event/<str:event_code>/payment/stripe/proceed",
        billing_event_stripe_views.billing_event_stripe_payment_proceed,
        name="billing_event_stripe_payment_proceed",
    ),
    path(
        # Stripe payment success
        "billing/event/<str:event_code>/payment/stripe/success",  # /<str:session_id>",
        billing_event_stripe_views.billing_event_stripe_payment_success,
        name="billing_event_stripe_payment_success",
    ),
]
