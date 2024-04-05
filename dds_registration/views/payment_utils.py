from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import Http404, HttpRequest, HttpResponse

from ..models import Payment


@login_required
def invoice_download(request: HttpRequest, payment_id: int) -> HttpResponse:
    try:
        payment = Payment.objects.get(id=payment_id)
    except ObjectDoesNotExist:
        raise Http404

    if payment.data['user']['id'] != request.user.id:
        raise PermissionDenied()

    response = HttpResponse(content=bytes(payment.invoice_pdf().output()), content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="DdS invoice {payment.invoice_no}.pdf"'
    return response


@login_required
def receipt_download(request: HttpRequest, payment_id: int) -> HttpResponse:
    try:
        payment = Payment.objects.get(id=payment_id)
    except ObjectDoesNotExist:
        raise Http404

    if payment.data['user']['id'] != request.user.id:
        raise PermissionDenied()

    response = HttpResponse(content=bytes(payment.receipt_pdf().output()), content_type="application/pdf")
    response['Content-Disposition'] = f'attachment; filename="DdS receipt {payment.invoice_no}.pdf"'
    return response
