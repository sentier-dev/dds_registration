from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpRequest
from django.contrib.sites.shortcuts import get_current_site

from ..models import Payment, Registration
from ..money import get_stripe_amount_for_currency, convert_from_stripe_units

from .helpers.stripe_payments import get_stripe_client_secret


@login_required
def event_payment_stripe(request: HttpRequest, payment_id: int):
    try:
        payment = Payment.objects.get(id=payment_id)
    except ObjectDoesNotExist:
        raise Http404

    if payment.status != "CREATED":
        messages.error("This payment has already been paid or refunded")
        redirect("profile")

    if payment.data['user']['id'] != request.user.id:
        messages.error(request, "Can't pay for someone else's items")
        return redirect("profile")

    # Stripe is in cents or centimes
    stripe_amount = get_stripe_amount_for_currency(
        amount=payment.data['price'],
        currency=payment.data['currency'],
    )
    actual_amount = convert_from_stripe_units(
        amount=stripe_amount,
        currency=payment.data['currency'],
    )

    payment.data['stripe_charge_in_progress'] = actual_amount
    payment.save()

    stripe_intent = get_stripe_client_secret(
        payment.data['currency'],
        stripe_amount,
        request.user.email,
        {'payment_id': payment.id}
    )

    template = "dds_registration/billing/billing_event_stripe_payment_proceed.html.django"
    return render(
        request=request,
        template_name=template,
        context={
            'client_secret': stripe_intent.client_secret,
            'payment': payment,
            'site': get_current_site(request),
            'scheme': "https" if request.is_secure() else "http",
        }
    )


@login_required
def event_payment_stripe_success(request: HttpRequest, payment_id: int):
    try:
        payment = Payment.objects.get(id=payment_id)
    except ObjectDoesNotExist:
        raise Http404

    if payment.status != "CREATED":
        messages.error("This payment has already been paid or refunded")
        redirect("profile")

    if payment.data['user']['id'] != request.user.id:
        messages.error(request, "Can't pay for someone else's items")
        return redirect("profile")

    messages.success(request, f"Awesome, your registration for {payment.data['event']['title']} is paid, and you are good to go!")

    payment.data['price'] = payment.data.pop('stripe_charge_in_progress')
    payment.mark_paid()

    reg = Registration.objects.get(id=payment.data['registration']['id'])
    reg.status = "REGISTERED"
    reg.save()
    return redirect("profile")
