from django.urls import path

from ..views.payment_utils import invoice_download, receipt_download
from ..views.billing_event import payment_view

urlpatterns = [
    path(
        "payments/<int:payment_id>/download/invoice",
        invoice_download,
        name="invoice_download",
    ),
    path(
        "payments/<int:payment_id>/download/receipt",
        receipt_download,
        name="receipt_download",
    ),
    path(
        "payments/<int:payment_id>/",
        payment_view,
        name="payment_details",
    ),
]
