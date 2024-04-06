from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpRequest
from django.shortcuts import redirect, render

from ..models import Event, Payment, Registration, RegistrationOption
from ..forms import RegistrationForm

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

    registration = event.get_active_event_registration_for_user(request.user)
    if registration and registration.payment.status == "PAID":
        messages.error("Paid event registration can't be edited manually; please either cancel and start again, or contact events@d-d-s.ch. Sorry for the inconvenience.")
        redirect("profile")

    if request.method == "POST":
        form = RegistrationForm(data=request.POST, option_choices=[(obj.id, obj.form_label) for obj in event.options.all()],)

        print(request.POST)
        print(form.is_valid())
        if not form.is_valid():
            print(form.errors)
        print(form.data)

        if form.is_valid():
            option = RegistrationOption.objects.get(id=form.cleaned_data['option'])
            if registration:
                # Set up new payment
                if registration.payment:
                    registration.payment.status = "OBSOLETE"
                    registration.payment.save()
                registration.option = option
                registration.send_update_emails = form.cleaned_data['send_update_emails']
                registration.status = "SUBMITTED"
            else:
                registration = Registration(
                    event=event,
                    status="SUBMITTED",
                    user=request.user,
                    send_update_emails=form.cleaned_data['send_update_emails'],
                    option=option,
                )
            registration.save()

            if not registration.option.price:
                messages.success(request, f"You have successfully registered for {event.title}.")
                registration.complete_registration()
                return redirect("profile")

            payment = Payment(
                status="CREATED",
                data={
                    "user": {
                        "id": request.user.id,
                        "name": form.cleaned_data['name'],
                        "address": form.cleaned_data['address'],
                    },
                    "extra": form.cleaned_data['extra'],
                    "kind": "event",
                    "method": form.cleaned_data['payment_method'],
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

            if payment.data["method"] == "INVOICE":
                payment.email_invoice()
                payment.status = "ISSUED"
                payment.save()
                messages.success(
                    request,
                    f"Your registration for {event.title} has been created! An invoice has been sent to your email address; it can also be downloaded from your profile. Please note your registration is not in force until the invoice is paid.",
                )
                return redirect("profile")
            elif payment.data["method"] == "STRIPE":
                return redirect("payment_stripe", payment_id=payment.id)
    else:
        # TODO: Populate template with existing choices instead of defaults
        if registration:
            print("existing registration")
            messages.success(request, "You are now editing an existing registration application. Please be careful not to make unwanted changes.")
            form = RegistrationForm(
                option_choices=[(obj.id, obj.form_label) for obj in event.options.all()],
                initial={
                    'name': registration.payment.data['user']['name'],
                    'address': registration.payment.data['user']['name'],
                    'extra': registration.payment.data['extra'],
                    'option': registration.option.id,
                    'send_update_emails': registration.send_update_emails,
                }
            )
        else:
            print("new registration")
            for option in event.options.all():
                print(option.form_label)
            form = RegistrationForm(
                option_choices=[(obj.id, obj.form_label) for obj in event.options.all()],
                initial={
                    "name": request.user.get_full_name(),
                    "address": request.user.address,
                    "extra": "",
                    'send_update_emails': True,
                }
            )
    return render(
        request=request,
        template_name="dds_registration/event_registration_new.html.django",
        context={
            "form": form,
            "event": event,
        },
    )



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
