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
    # SSO gateway for the gated static dashboards on dashboard.d-d-s.ch.
    # `login/` overrides the stock auth view so the dashboard host is honoured
    # as a `?next=` target; must precede the auth.urls include below to win.
    # `dashboards/<key>/auth/` is the per-route nginx `auth_request` target.
    path("accounts/login/", views.SubdomainLoginView.as_view(), name="login"),
    path("dashboards/<slug:key>/auth/", views.dashboard_auth, name="dashboard_auth"),
    # Stock accounts...
    path(
        "accounts/",
        include("django_registration.backends.activation.urls"),
    ),
    path("accounts/", include("django.contrib.auth.urls")),
]
