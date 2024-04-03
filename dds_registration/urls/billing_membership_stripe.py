# @module XXX
# @changed 2024.04.02, 00:28

from django.urls import path, register_converter


from ..views import billing_membership_stripe as billing_membership_stripe_views

from ..converters.FloatUrlParameterConverter import FloatUrlParameterConverter

register_converter(FloatUrlParameterConverter, "float")

urlpatterns = [
    # Stripe...
    path(
        # Proceed membership payment by stripe
        "billing/membership/payment/stripe/proceed",
        billing_membership_stripe_views.billing_membership_stripe_payment_proceed,
        name="billing_membership_stripe_payment_proceed",
    ),
    path(
        # Stripe payment success
        "billing/membership/payment/stripe/success",
        billing_membership_stripe_views.billing_membership_stripe_payment_success,
        name="billing_membership_stripe_payment_success",
    ),
]
