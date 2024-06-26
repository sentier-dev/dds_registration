# @module dds_registration/urls/accounts.py
# @changed 2024.04.02, 00:28

from django.urls import include, path

from .. import views
from ..forms import DdsRegistrationForm
from ..views.user_registration import DdsRegistrationView

urlpatterns = [
    # Accounts...
    path(
        # Overrided registration form using updated one
        "accounts/register/",
        DdsRegistrationView.as_view(form_class=DdsRegistrationForm),
        name="django_registration_register",
    ),
    path("", views.index, name="index"),
    path("profile", views.profile, name="profile"),
    path(
        "profile/edit",
        views.edit_user_profile,
        name="profile_edit",
    ),
    # Stock accounts...
    path(
        "accounts/",
        include("django_registration.backends.activation.urls"),
    ),
    path("accounts/", include("django.contrib.auth.urls")),
]
