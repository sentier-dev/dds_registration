from django.urls import path

from ..views.membership import membership_application

urlpatterns = [
    path(
        "membership/apply",
        membership_application,
        name="membership_application",
    ),
]
