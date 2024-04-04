# @module dds_registration/urls/__init__.py
# @changed 2024.04.02, 00:32

from .billing_event_urls import urlpatterns as billing_event_urlpatterns
from .billing_event_invoice_urls import urlpatterns as billing_event_invoice_urlpatterns
from .billing_event_stripe_urls import urlpatterns as billing_event_stripe_urlpatterns
from .billing_membership_urls import urlpatterns as billing_membership_urlpatterns
from .billing_membership_invoice_urls import urlpatterns as billing_membership_invoice_urlpatterns
from .billing_membership_stripe_urls import urlpatterns as billing_membership_stripe_urlpatterns
from .event_urls import urlpatterns as event_urlpatterns
from .membership_urls import urlpatterns as membership_urlpatterns
from .accounts_urls import urlpatterns as accounts_urlpatterns
from .root_urls import urlpatterns as root_urlpatterns

urlpatterns = []

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
