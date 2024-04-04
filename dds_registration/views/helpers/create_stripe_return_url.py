# @module billing_event_stripe.py
# @changed 2024.04.01, 23:57
# NOTE: UNUSED: It was used for stripe checkout payment method.


from django.http import HttpRequest
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site


from django.http import HttpRequest


def create_stripe_return_url(request: HttpRequest, route: str, return_args: dict) -> str:
    # route billing_membership_stripe_payment_success:
    # "billing/membership/<str:membership_type>/payment/stripe/success/<str:session_id>"
    # Example from stripe docs:
    # return_url="https://example.com/checkout/return?session_id={CHECKOUT_SESSION_ID}",
    return_url_path = reverse(route, kwargs=return_args)
    return_url_path = return_url_path.replace("CHECKOUT_SESSION_ID_PLACEHOLDER", "{CHECKOUT_SESSION_ID}")
    scheme = "https" if request.is_secure() else "http"
    site = get_current_site(request)
    return_url = scheme + "://" + site.domain + return_url_path
    return return_url
