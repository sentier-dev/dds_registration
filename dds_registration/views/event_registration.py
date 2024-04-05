# @module dds_registration/views/event_registration.py
# @changed 2024.03.19, 01:40

import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpRequest
from django.shortcuts import redirect, render

from ..models import Event, Payment, Registration, RegistrationOption
# from .event_registration_cancel import (
#     event_registration_cancel_confirm_form,
#     event_registration_cancel_process_action,
# )
# from .helpers.events import (
#     event_registration_form,
#     get_event_registration_context,
#     show_registration_form_success,
# )

LOG = logging.getLogger(__name__)


@login_required
def event_registration(request: HttpRequest, event_code: str):
    try:
        event = Event.objects.get(code=event_code)
    except ObjectDoesNotExist:
        raise Http404

    if not event.can_register:
        messages.error(request, f"Registration for {event.title} isn't open")
        return redirect("index")

    if request.method == "GET":
        if event.get_active_event_registration_for_user(request.user):
            messages.error(request, f"You are already registered for {event.title}")
            return redirect("index")
        else:
            return render(
                request=request,
                template_name="dds_registration/event_registration_new.html.django",
                context={
                    "event": event,
                    "options": event.options.all(),
                    "error_message": None,
                    "payment_methods": Payment.METHODS,
                    "default_payment_method": Payment.DEFAULT_METHOD,
                },
            )
    else:
        registration = event.get_active_event_registration_for_user(request.user)
        if registration:
            # Can only change if not yet paid
            if registration.payment and registration.payment.status == "PAID":
                messages.error(
                    request,
                    f"Changing a paid registration isn't currently possible. You need to cancel and register again for {event.title}. Sorry for the inconvenience.",
                )
                return redirect("profile")
            # Set up new payment and registration option
            if registration.payment:
                registration.payment.status = "OBSOLETE"
                registration.payment.save()
        else:
            registration = Registration(event=event, status="SUBMITTED", user=request.user)
        try:
            option = RegistrationOption.objects.get(id=int(request.POST["checked_option_ids"]))
        except ObjectDoesNotExist:
            raise Http404

        registration.option = option
        registration.save()

        if not option.price:
            messages.success(request, f"You have successfully registered for {event.title}.")
            registration.complete_registration()
            return redirect("profile")

        payment_method = request.POST["payment_method"]
        payment = Payment(
            status="CREATED",
            data={
                "user": {
                    "id": request.user.id,
                    "name": request.user.get_full_name(),
                    "address": request.user.address,
                },
                "extra": "",
                "kind": "event",
                "method": payment_method,
                "event": {
                    "id": event.id,
                    "title": event.title,
                },
                "registration": {
                    "id": registration.id,
                },
                "option": {
                    "id": option.id,
                    "item": option.item,
                    "price": option.stripe_price if payment_method == "STRIPE" else option.price,
                    "stripe-converted": payment_method == "STRIPE",
                    "currency": option.currency,
                },
            },
        )
        payment.save()

        registration.payment = payment
        registration.save()

        return redirect("payment_details", payment_id=payment.id)


# @login_required
# def event_registration_cancel_confirm(request: HttpRequest, event_code: str):
#     return event_registration_cancel_confirm_form(
#         request,
#         event_code=event_code,
#         form_template="dds_registration/event_registration_cancel_confirm.html.django",
#         success_redirect="profile",
#     )


# @login_required
# def event_registration_cancel_process(request: HttpRequest, event_code: str):
#     return event_registration_cancel_process_action(
#         request,
#         event_code=event_code,
#         #  form_template=None,
#         success_redirect="profile",
#     )


# @login_required
# def event_registration_payment(request: HttpRequest, event_code: str):
#     # XXX: OBSOLETE: Should be moved to `billing`
#     try:
#         # TODO: Place payment link/info here
#         template = "dds_registration/event_registration_payment.html.django"
#         context = get_event_registration_context(request, event_code)
#         return render(request, template, context)
#     except Exception as err:
#         sError = errorToString(err, show_stacktrace=False)
#         error_text = 'Can not get payment information the for event "{}": {}'.format(event_code, sError)
#         messages.error(request, error_text)
#         sTraceback = str(traceback.format_exc())
#         debug_data = {
#             "event_code": event_code,
#             "err": err,
#             "traceback": sTraceback,
#         }
#         LOG.error("%s (redirecting to profile): %s", error_text, debug_data)
#         raise Exception(error_text)
