# @module XXX
# @changed 2024.04.02, 00:28

from django.urls import path, register_converter

from ..views import billing_event_stripe as billing_event_stripe_views


from ..converters.FloatUrlParameterConverter import FloatUrlParameterConverter

register_converter(FloatUrlParameterConverter, "float")

urlpatterns = [
    path(
        # Create stripe session (Link with event code, currency and amount)
        "billing/event/<str:event_code>/payment/stripe/create_checkout_session/<str:currency>/<float:amount>",
        billing_event_stripe_views.billing_event_payment_stripe_create_checkout_session,
        name="billing_event_payment_stripe_create_checkout_session",
    ),
    path(
        # Proceed stripe payment
        "billing/event/<str:event_code>/payment/stripe/proceed",
        billing_event_stripe_views.billing_event_stripe_payment_proceed,
        name="billing_event_stripe_payment_proceed",
    ),
    path(
        # Stripe payment success
        "billing/event/<str:event_code>/payment/stripe/success/<str:session_id>",
        billing_event_stripe_views.billing_event_stripe_payment_success,
        name="billing_event_stripe_payment_success",
    ),
]
