from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, Http404
from django.core.exceptions import ObjectDoesNotExist
from ..models import Payment


@login_required
def invoice_download(request: HttpRequest, payment_id: int) -> HttpResponse:
    try:
        payment = Payment.objects.get(id=payment_id)
    except ObjectDoesNotExist:
        raise Http404

    if payment.data['user']['id'] != request.user.id:
        raise PermissionDenied()

    return HttpResponse(bytes(payment.invoice_pdf().output()), content_type="application/pdf")


@login_required
def receipt_download(request: HttpRequest, payment_id: int) -> HttpResponse:
    try:
        payment = Payment.objects.get(id=payment_id)
    except ObjectDoesNotExist:
        raise Http404

    if payment.data['user']['id'] != request.user.id:
        raise PermissionDenied()

    return HttpResponse(bytes(payment.receipt_pdf().output()), content_type="application/pdf")
