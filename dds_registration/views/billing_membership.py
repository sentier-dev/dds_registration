from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.http import HttpRequest, HttpResponse


from ..forms import PaymentForm
from ..models import Payment


@login_required
def membership_payment_view(request: HttpRequest, payment_id: int) -> HttpResponse:
    payment = Payment.objects.get(id=payment_id)
    if payment.data['user']['id'] != request.user.id:
        messages.error(request, "Can't pay for someone else's membership")
        return redirect("profile")

    if request.method == "POST":
        form = PaymentForm(request.POST)
        if form.is_valid():
            if payment.data['method'] == 'INVOICE':
                payment.email_invoice()
                messages.success(request, "An invoice has been sent to your email address; it can also be downloaded here. Please note your membership is not complete until the invoice is paid.")
                return redirect("profile")
            elif payment.data['method'] == 'STRIPE':
                return redirect("membership_payment_stripe", payment_id=payment.id)
    else:
        form = PaymentForm(data={'name': payment.data['user']['name'], 'address': payment.data['user']['address'], 'extra': payment.data['extra']})
        template = "dds_registration/billing/billing_membership_form.html.django"
    return render(request=request, template_name=template, context={'form': form, 'payment': payment})
