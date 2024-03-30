# @module dds_registration/urls.py
# @changed 2024.03.26, 17:04

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.decorators.cache import cache_page

from . import views
from .views import membership as membership_views
from .views import event_registration as event_registration_views
from .views import billing as billing_views
from .views import registration as registration_views

from .forms import DdsRegistrationForm

cache_timeout = 0 if settings.DEV or settings.DEBUG else 15 * 60  # in seconds: {min}*60


urlpatterns = [
    path(
        # Overrided registration form using updated one
        "accounts/register/",
        registration_views.DdsRegistrationView.as_view(form_class=DdsRegistrationForm),
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
        event_registration_views.event_registration_new,
        name="event_registration_new",
    ),
    path(
        "event/<str:event_code>/registration/new/success",
        event_registration_views.event_registration_new_success,
        name="event_registration_new_success",
    ),
    path(
        "event/<str:event_code>/registration/cancel",
        event_registration_views.event_registration_cancel_confirm,
        name="event_registration_cancel",
    ),
    path(
        "event/<str:event_code>/registration/cancel/process",
        event_registration_views.event_registration_cancel_process,
        name="event_registration_cancel_process",
    ),
    path(
        "event/<str:event_code>/registration/edit",
        event_registration_views.event_registration_edit,
        name="event_registration_edit",
    ),
    path(
        "event/<str:event_code>/registration/edit/success",
        event_registration_views.event_registration_edit_success,
        name="event_registration_edit_success",
    ),
    # path(
    #     # Download invoice page (delete or move to billing?)
    #     "event/<str:event_code>/registration/invoice",
    #     event_registration_views.event_registration_invoice,
    #     name="event_registration_invoice",
    # ),
    #  path(
    #      # Download invoice pdf (delete or move to billing?)
    #      "event/<str:event_code>/registration/invoice/download",
    #      event_registration_views.event_registration_invoice_download,
    #      name="event_registration_invoice_download",
    #  ),
    path(
        "event/<str:event_code>/registration/payment",
        event_registration_views.event_registration_payment,
        name="event_registration_payment",
    ),
    # Billing...
    path(
        "billing/event/<str:event_code>",
        billing_views.billing_event,
        name="billing_event",
    ),
    path(
        # Invoice created: link to download a pdf
        "billing/event/<str:event_code>/invoice/proceed",
        billing_views.billing_event_proceed_invoice,
        name="billing_event_proceed_invoice",
    ),
    path(
        # Invoice pdf generate and download
        "billing/event/<str:event_code>/invoice/download",
        billing_views.billing_event_invoice_download,
        name="billing_event_invoice_download",
    ),
    path(
        # Create stripe session (TODO: Add params for currency and amout)
        "billing/event/<str:event_code>/payment/stripe/create_checkout_session",
        billing_views.billing_event_payment_stripe_create_checkout_session,
        name="billing_event_payment_stripe_create_checkout_session",
    ),
    path(
        # Proceed stripe payment
        "billing/event/<str:event_code>/payment/stripe/proceed",
        billing_views.billing_event_stripe_payment_proceed,
        name="billing_event_stripe_payment_proceed",
    ),
    path(
        # Stripe payment success
        "billing/event/<str:event_code>/payment/stripe/success/<str:session_id>",
        billing_views.billing_event_stripe_payment_success,
        name="billing_event_stripe_payment_success",
    ),
    path(
        # ???
        "billing/membership",
        billing_views.billing_membership,
        name="billing_membership",
    ),
    path(
        # Proceed membership payment (TODO: Update form in `membership-choose-list.django`
        "billing/membership/<str:membership_type>/payment/<str:payment_method>/proceed",
        billing_views.billing_event_stripe_payment_proceed,
        name="billing_membership_stripe_payment_proceed",
    ),
    # Membership (TODO: Some routes will be moved to `billing`)...
    path(
        "membership/start",
        membership_views.membership_start,
        name="membership_start",
    ),
    path(
        "membership/proceed/<str:membership_type>",
        membership_views.membership_proceed,
        name="membership_proceed",
    ),
    path(
        "membership/proceed/success",
        membership_views.membership_proceed_success,
        name="membership_proceed_success",
    ),
    path(
        "membership/proceed/test/<str:payment_id>",
        membership_views.membership_proceed_test,
        name="membership_proceed_test",
    ),
    # Stripe api
    path(
        # TODO: Use more specific url later
        "webhook",
        membership_views.membership_stripe_webhook,
        name="membership_stripe_webhook",
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
