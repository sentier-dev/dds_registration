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
        # TODO: Populate template with existing choices instead of defaults
        if event.get_active_event_registration_for_user(request.user):
            messages.success(request, "You are editing an existing registration")
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
            method=payment_method,
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
                },
                "price": option.price,
                "currency": option.currency,
            },
        )
        payment.save()

        registration.payment = payment
        registration.save()

        return redirect("event_payment_details", payment_id=payment.id)


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
