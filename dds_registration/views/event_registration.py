# @module dds_registration/views/event_registration.py
# @changed 2024.03.19, 01:40

import logging
import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpRequest
from django.shortcuts import redirect, render

from ..core.helpers.errors import errorToString
from ..models import Event, Payment, Registration, RegistrationOption
from .event_registration_cancel import (
    event_registration_cancel_confirm_form,
    event_registration_cancel_process_action,
)
from .helpers.events import (
    event_registration_form,
    get_event_registration_context,
    show_registration_form_success,
)

LOG = logging.getLogger(__name__)


@login_required
def event_registration(request: HttpRequest, event_code: str):
    try:
        event = Event.objects.get(code=event_code)
    except ObjectDoesNotExist:
        raise Http404

    if not event.can_register():
        messages.error(request, f"Registration for {event.title} isn't open")
        return redirect("index")

    if request.method == "GET":
        if event.get_active_registration_for_user(request.user):
            messages.error(request, f"You are already registered for {event.title}")
            return redirect("index")
        else:
            return render(
                request=request,
                template_name="dds_registration/event_registration_new.html.django",
                context={
                    "event": event,
                    "error_message": None,
                    "payment_methods": Payment.PAYMENT_METHODS,
                    "default_payment_method": "INVOICE",
                },
            )
    else:
        registration = event.get_active_registration_for_user(request.user)
        if registration:
            # Can only change if not yet paid
            if registration.payment.status == "PAID":
                messages.error(
                    request,
                    f"Changing a paid registration isn't currently possible. You need to cancel and register again for {event.title}. Sorry for the inconvenience.",
                )
                return redirect("profile")
            # Set up new payment and registration option
            registration.option.delete()
            registration.payment.status = "OBSOLETE"
            registration.payment.save()
        else:
            registration = Registration(event=event, status="SUBMITTED", user=request.user)
        try:
            option = RegistrationOption.objects.get(id=int(request.POST["registration_option_radio"]))
        except ObjectDoesNotExist:
            raise Http404

        registration.option = option
        registration.save()

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
                    "currency": option.currency,
                },
            },
        )
        payment.save()

        registration.payment = payment
        registration.save()

        # TODO: Render payment form

    # return event_registration_form(
    #     request,
    #     event_code=event_code,
    #     form_template="dds_registration/event_registration_new.html.django",
    #     success_redirect="billing_event",
    #     create_new=True,
    # )


@login_required
def event_registration_edit(request: HttpRequest, event_code: str):
    return event_registration_form(
        request,
        event_code=event_code,
        form_template="dds_registration/event_registration_edit.html.django",
        success_redirect="event_registration_edit_success",
    )


@login_required
def event_registration_cancel_confirm(request: HttpRequest, event_code: str):
    return event_registration_cancel_confirm_form(
        request,
        event_code=event_code,
        form_template="dds_registration/event_registration_cancel_confirm.html.django",
        success_redirect="profile",
    )


@login_required
def event_registration_cancel_process(request: HttpRequest, event_code: str):
    return event_registration_cancel_process_action(
        request,
        event_code=event_code,
        #  form_template=None,
        success_redirect="profile",
    )


@login_required
def event_registration_new_success(request: HttpRequest, event_code: str):
    return show_registration_form_success(
        request,
        event_code=event_code,
        template="dds_registration/event_registration_new_success.html.django",
    )


@login_required
def event_registration_edit_success(request: HttpRequest, event_code: str):
    return show_registration_form_success(
        request,
        event_code=event_code,
        template="dds_registration/event_registration_edit_success.html.django",
    )


# @login_required
# def event_registration_invoice(request: HttpRequest, event_code: str):
#     # XXX: OBSOLETE: Moved to `billing`
#     """
#     Check if there is an invoice for this event/registration.
#     Create it if not.
#     Redirect to or show a download link.
#     """
#     # TODO: Generate invoice pdf
#     template = "dds_registration/event_registration_invoice.html.django"
#     context = get_event_invoice_context(request, event_code)
#     context_redirect = context.get("redirect")
#     if context_redirect:
#         return context_redirect
#     return render(request, template, context)


# @login_required
# def event_registration_invoice_download(request: HttpRequest, event_code: str):
#     # XXX: OBSOLETE: Moved to `billing`
#     # TODO: Generate invoice pdf
#     template = "dds_registration/event_registration_invoice_download.html.django"
#     context = get_event_invoice_context(request, event_code)
#     show_debug = False
#     if show_debug:
#         return render(request, template, context)
#     pdf = create_invoice_pdf(context)
#     return HttpResponse(bytes(pdf.output()), content_type="application/pdf")


@login_required
def event_registration_payment(request: HttpRequest, event_code: str):
    # XXX: OBSOLETE: Should be moved to `billing`
    try:
        # TODO: Place payment link/info here
        template = "dds_registration/event_registration_payment.html.django"
        context = get_event_registration_context(request, event_code)
        return render(request, template, context)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = 'Can not get payment information the for event "{}": {}'.format(event_code, sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "event_code": event_code,
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (redirecting to profile): %s", error_text, debug_data)
        raise Exception(error_text)


__all__ = [
    event_registration,
    event_registration_edit,
    event_registration_new_success,
    event_registration_edit_success,
]
