# @module XXX
# @changed 2024.04.02, 00:28

from django.urls import path

from ..views import billing_membership as billing_membership_views


urlpatterns = [
    # Billing for memberships...
    path(
        "billing/membership/<str:membership_type>",
        billing_membership_views.billing_membership,
        name="billing_membership",
    ),
]
