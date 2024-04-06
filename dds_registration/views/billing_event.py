from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from ..forms import PaymentForm
from ..models import Payment, Registration


@login_required
def event_payment_view(request: HttpRequest, payment_id: int) -> HttpResponse:
    payment = Payment.objects.get(id=payment_id)
    if payment.data["user"]["id"] != request.user.id:
        messages.error(request, "Can't pay for someone else's items")
        return redirect("profile")

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            if payment.data["method"] == "INVOICE":
                payment.email_invoice()
                messages.success(
                    request,
                    "An invoice has been sent to your email address; it can also be downloaded here. Please note your purchase is not complete until the invoice is paid.",
                )
                reg = Registration.objects.get(id=payment.data["registration"]["id"])
                reg.status = "PAYMENT_PENDING"
                reg.save()
                return redirect("profile")
            elif payment.data["method"] == "STRIPE":
                return redirect("event_payment_stripe", payment_id=payment.id)
    else:
        form = PaymentForm(
            data={
                "name": payment.data["user"]["name"],
                "address": payment.data["user"]["address"],
                "extra": payment.data["extra"],
            }
        )
        template = "dds_registration/billing/billing_event_form.html.django"
    return render(request=request, template_name=template, context={"form": form, "payment": payment})
