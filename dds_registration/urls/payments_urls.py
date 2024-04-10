from django.urls import path

from ..views.payment_stripe import payment_stripe, payment_stripe_success
from ..views.payment_utils import invoice_download, receipt_download

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
        "payments/<int:payment_id>/stripe",
        payment_stripe,
        name="payment_stripe",
    ),
    path(
        "payments/<int:payment_id>/stripe/success",
        payment_stripe_success,
        name="payment_stripe_success",
    ),
]
