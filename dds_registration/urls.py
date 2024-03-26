from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.decorators.cache import cache_page

#  from django_registration.views import RegistrationView as OriginalRegistrationView

from . import views
from .forms import DdsRegistrationForm

cache_timeout = 0 if settings.DEV or settings.DEBUG else 15 * 60  # in seconds: {min}*60


urlpatterns = [
    path(
        # Overrided registration form using updated form
        "accounts/register/",
        views.DdsRegistrationView.as_view(form_class=DdsRegistrationForm),
        name="django_registration_register",
    ),
    path("", views.index, name="index"),
    path("profile", views.profile, name="profile"),
    path(
        "profile/edit",
        views.edit_user_profile,
        name="profile_edit",
    ),
    path(
        "event/<str:event_code>/registration/new",
        views.event_registration_new,
        name="event_registration_new",
    ),
    path(
        "event/<str:event_code>/registration/new/success",
        views.event_registration_new_success,
        name="event_registration_new_success",
    ),
    path(
        "event/<str:event_code>/registration/cancel",
        views.event_registration_cancel_confirm,
        name="event_registration_cancel",
    ),
    path(
        "event/<str:event_code>/registration/cancel/process",
        views.event_registration_cancel_process,
        name="event_registration_cancel_process",
    ),
    path("event/<str:event_code>/registration/edit", views.event_registration_edit, name="event_registration_edit"),
    path(
        "event/<str:event_code>/registration/edit/success",
        views.event_registration_edit_success,
        name="event_registration_edit_success",
    ),
    path(
        "event/<str:event_code>/registration/invoice",
        views.event_registration_invoice,
        name="event_registration_invoice",
    ),
    path(
        "event/<str:event_code>/registration/payment",
        views.event_registration_payment,
        name="event_registration_payment",
    ),
    # App-provided paths...
    path("admin/", admin.site.urls, name="admin"),
    path(
        "accounts/",
        include("django_registration.backends.activation.urls"),
    ),
    path("accounts/", include("django.contrib.auth.urls")),
    # Service pages...
    path(
        "robots.txt",
        cache_page(cache_timeout)(views.RobotsView.as_view()),
        name="robots",
    ),
    #  url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemap.sitemaps_dict}, name='sitemap'),
]

if settings.DEV:
    # Demo pages (for debug/dev purposes only)...
    urlpatterns.append(
        path("components-demo", views.components_demo, name="components_demo"),
    )
