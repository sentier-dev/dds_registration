from django.urls import path

from ..views.membership import membership_application, membership_details

urlpatterns = [
    path("membership/apply", membership_application, name="membership_application"),
    path("membership/details", membership_details, name="membership_details"),
]
