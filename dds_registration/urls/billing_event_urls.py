# @module XXX
# @changed 2024.04.02, 00:28

from django.conf import settings
from django.contrib import admin
from django.views.decorators.cache import cache_page
from django.urls import include, path
from django.urls import path, register_converter

from .. import views
from ..views import membership as membership_views
from ..views import event_registration as event_registration_views
from ..views import registration as registration_views
from ..views import billing_event as billing_event_views
from ..views import billing_event_invoice as billing_event_invoice_views
from ..views import billing_event_stripe as billing_event_stripe_views
from ..views import billing_membership as billing_membership_views
from ..views import billing_membership_invoice as billing_membership_invoice_views
from ..views import billing_membership_stripe as billing_membership_stripe_views

from ..forms import DdsRegistrationForm

from ..converters.FloatUrlParameterConverter import FloatUrlParameterConverter

urlpatterns = [
    # Billing for events...
    path(
        "billing/event/<str:event_code>",
        billing_event_views.billing_event,
        name="billing_event",
    ),
]
