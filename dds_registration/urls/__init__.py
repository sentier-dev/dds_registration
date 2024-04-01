# @module dds_registration/urls/__init__.py
# @changed 2024.04.02, 00:32

from django.conf import settings
from django.urls import path

from .. import views

from .billing_event import urlpatterns as billing_event_urlpatterns
from .billing_event_invoice import urlpatterns as billing_event_invoice_urlpatterns
from .billing_event_stripe import urlpatterns as billing_event_stripe_urlpatterns
from .billing_membership import urlpatterns as billing_membership_urlpatterns
from .billing_membership_invoice import urlpatterns as billing_membership_invoice_urlpatterns
from .billing_membership_stripe import urlpatterns as billing_membership_stripe_urlpatterns
from .event import urlpatterns as event_urlpatterns
from .membership import urlpatterns as membership_urlpatterns
from .accounts import urlpatterns as accounts_urlpatterns
from .root import urlpatterns as root_urlpatterns

urlpatterns = []

if settings.DEV:
    # Demo pages (for debug/dev purposes only)...
    urlpatterns.append(
        path("components-demo", views.components_demo, name="components_demo"),
    )

urlpatterns += event_urlpatterns
urlpatterns += membership_urlpatterns

urlpatterns += billing_event_urlpatterns
urlpatterns += billing_event_invoice_urlpatterns
urlpatterns += billing_event_stripe_urlpatterns
urlpatterns += billing_membership_urlpatterns
urlpatterns += billing_membership_invoice_urlpatterns
urlpatterns += billing_membership_stripe_urlpatterns

urlpatterns += accounts_urlpatterns
urlpatterns += root_urlpatterns
