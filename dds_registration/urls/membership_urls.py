# @module XXX
# @changed 2024.04.02, 00:28

from django.urls import path

from ..views import membership as membership_views


urlpatterns = [
    # Membership (TODO: Some routes will be moved to `billing`)...
    path(
        "membership/start",
        membership_views.membership_start,
        name="membership_start",
    ),
    path(
        "membership/proceed/success",
        membership_views.membership_proceed_success,
        name="membership_proceed_success",
    ),
]
