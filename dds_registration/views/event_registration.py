import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, HttpRequest
from django.shortcuts import redirect, render
from loguru import logger

from ..forms import FreeRegistrationForm, RegistrationForm
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

    registration = event.get_active_event_registration_for_user(request.user)

    if not registration:
        if not event.can_register(request.user):
            messages.error(request, f"Registration for {event.title} isn't open")
            return redirect("index")

        if event.members_only and not request.user.is_member:
            messages.error(request, f"{event.title} is only for members")
            return redirect("index")
        if event.application_form:
            return redirect("djf_surveys:create", slug=event.application_form.slug)
    elif registration.payment and registration.payment.status == "PAID":
        messages.error(
            request,
            f"Paid event registrations can't be edited manually; please either cancel and start again, or contact {settings.DEFAULT_CONTACT_EMAIL}. Sorry for the inconvenience.",
        )
        return redirect("profile")
    elif registration.application and registration.status == "SUBMITTED":
        # Applied but not yet accepted/rejected - can edit application form
        return redirect("djf_surveys:edit", pk=registration.application.id)

    logger.debug(f"Working on registration {registration}")

    if request.method == "POST":
        logger.debug(f"POST response {request.POST}")
        if event.free:
            form = FreeRegistrationForm(
                data=request.POST,
            )
            if form.is_valid():
                if registration:
                    registration.send_update_emails = form.cleaned_data["send_update_emails"]
                    registration.status = "REGISTERED"
                else:
                    registration = Registration(
                        event=event,
                        status="REGISTERED",
                        user=request.user,
                        send_update_emails=form.cleaned_data["send_update_emails"],
                    )
                registration.save()
                registration.complete_registration()

                if settings.SLACK_REGISTRATIONS_WEBHOOK:
                    requests.post(
                        url=settings.SLACK_REGISTRATIONS_WEBHOOK,
                        json={
                            "text": "Registration by {} for {} ({})".format(
                                request.user.get_full_name(), event.title, event.get_admin_url()
                            )
                        },
                    )

                messages.success(request, f"You have successfully registered for {event.title}.")
                return redirect("profile")
        else:
            form = RegistrationForm(
                data=request.POST,
                option_choices=[(obj.id, obj.form_label) for obj in RegistrationOption.free_spots(event)],
                credit_cards=event.credit_cards,
            )

            if form.is_valid():
                option = RegistrationOption.objects.get(id=form.cleaned_data["option"])
                if registration:
                    # Set up new payment
                    if registration.payment:
                        registration.payment.mark_obsolete()
                    registration.option = option
                    registration.send_update_emails = form.cleaned_data["send_update_emails"]
                    registration.status = "PAYMENT_PENDING"
                else:
                    registration = Registration(
                        event=event,
                        status="PAYMENT_PENDING",
                        user=request.user,
                        send_update_emails=form.cleaned_data["send_update_emails"],
                        option=option,
                    )
                registration.save()

                if settings.SLACK_REGISTRATIONS_WEBHOOK:
                    requests.post(
                        url=settings.SLACK_REGISTRATIONS_WEBHOOK,
                        json={
                            "text": "Registration by {} for {} ({})".format(
                                request.user.get_full_name(), event.title, event.get_admin_url()
                            )
                        },
                    )

                if not registration.option.price:
                    messages.success(request, f"You have successfully registered for {event.title}.")
                    registration.complete_registration()
                    return redirect("profile")

                payment = Payment(
                    status="CREATED",
                    data={
                        "user": {
                            "id": request.user.id,
                            "name": form.cleaned_data["name"],
                            "address": form.cleaned_data["address"],
                        },
                        "extra": form.cleaned_data["extra"],
                        "kind": "event",
                        "method": form.cleaned_data["payment_method"],
                        "event": {
                            "id": event.id,
                            "title": event.title,
                            "vat_rate": event.vat_rate,
                        },
                        "registration": {
                            "id": registration.id,
                        },
                        "option": {
                            "id": option.id,
                            "item": option.item,
                        },
                        "price": option.price,
                        "net_price": option.net_price(),
                        "currency": option.currency,
                        "includes_membership": option.includes_membership,
                        "membership_end_year": option.membership_end_year,
                    },
                )
                payment.save()

                logger.debug(f"Created or updated payment {payment.data}")

                registration.payment = payment
                registration.save()

                if payment.data["method"] == "INVOICE":
                    payment.email_invoice(extra_address=form.cleaned_data["additional_email"])
                    payment.status = "ISSUED"
                    payment.save()
                    messages.success(
                        request,
                        f"Your registration for {event.title} has been created! An invoice has been sent to {request.user.email} from events@d-d-s.ch. The invoice can also be downloaded from your profile. Please note your registration is not in force until the invoice is paid.",
                    )
                    return redirect("profile")
                elif payment.data["method"] == "STRIPE":
                    return redirect("payment_stripe", payment_id=payment.id)
            else:
                errors = form.errors.as_data()
                logger.debug(f"Invalid form with POST data for paid event {event}: {errors}")
    elif event.free:
        if registration:
            form = FreeRegistrationForm(
                initial={
                    "send_update_emails": registration.send_update_emails,
                },
            )
        else:
            form = FreeRegistrationForm()
    else:
        if registration:
            # TODO: What to do if there no payment property in the registration object (as a result of a inconsistency)?
            if registration.option:
                messages.success(
                    request,
                    "You are now editing an existing registration application. Please be careful not to make unwanted changes.",
                )
            if registration.payment:
                name = registration.payment.data["user"]["name"]
                address = registration.payment.data["user"]["address"]
                extra = registration.payment.data["extra"]
            else:
                name = request.user.get_full_name()
                address = request.user.address
                extra = ""
            option = registration.option.id if registration.option else None

            form = RegistrationForm(
                option_choices=[(obj.id, obj.form_label) for obj in RegistrationOption.free_spots(event)],
                credit_cards=event.credit_cards,
                initial={
                    "name": name,
                    "address": address,
                    "extra": extra,
                    "option": option,
                    "send_update_emails": registration.send_update_emails,
                },
            )
        else:
            form = RegistrationForm(
                option_choices=[(obj.id, obj.form_label) for obj in event.options.all()],
                credit_cards=event.credit_cards,
                initial={
                    "name": request.user.get_full_name(),
                    "address": request.user.address,
                    "extra": "",
                    "send_update_emails": True,
                },
            )
    return render(
        request=request,
        template_name="dds_registration/event/event_registration_new.html.django",
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
#         form_template="dds_registration/event/event_registration_cancel_confirm.html.django",
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
