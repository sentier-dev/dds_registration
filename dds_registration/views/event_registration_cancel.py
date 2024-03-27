# @module dds_registration/views/event_registration_cancel_confirm_form.py
# @changed 2024.03.20, 12:39

from django.contrib import messages

from django.http import HttpRequest
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site

import traceback
import logging

from ..core.helpers.errors import errorToString

from ..models import (
    Event,
    Registration,
)


LOG = logging.getLogger(__name__)


def send_event_registration_cancelled_message(request: HttpRequest, context: dict):
    """
    Send successful event registration cancellation message to the user
    """

    email_body_template = "dds_registration/event_registration_cancelled_message_body.txt"
    email_subject_template = "dds_registration/event_registration_cancelled_message_subject.txt"

    user = request.user

    try:
        # LOG.debug("start: %s", context)
        subject = render_to_string(
            template_name=email_subject_template,
            context=context,
            request=request,
        )
        subject = " ".join(subject.splitlines()).strip()
        body = render_to_string(
            template_name=email_body_template,
            context=context,
            request=request,
        )
        debug_data = {
            "subject": subject,
            "body": body,
        }
        # LOG.debug("mail_user: %s", context)
        user.email_user(subject, body, settings.DEFAULT_FROM_EMAIL)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("Caught error %s (re-raising): %s", sError, debug_data)
        raise err


def get_event_registration_cancel_context(request: HttpRequest, event_code: str):
    context = {
        "success": None,
        "redirect": None,
        "event_code": event_code,
        "event": None,
        "registration": None,
        "site": get_current_site(request),
    }

    user = request.user
    if not user.is_authenticated:
        context["redirect"] = "index"
        return context

    # Variables to collect the data for form context...
    event = None
    registration = None

    # Try to get event object by code...
    try:
        event = Event.objects.get(code=event_code)
    except Exception as err:
        error_text = 'Not found event code "{}"'.format(event_code)
        messages.error(request, error_text)
        #  sError = errorToString(err, show_stacktrace=False)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "event_code": event_code,
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (redirecting to profile): %s", error_text, debug_data)
        # Redirect to profile page with error messages (see above)
        context["redirect"] = "profile"
        return context

    context["event"] = event

    # Try to find active registrations for this event (prevent constrain exception)...
    try:
        # TODO: Go to the next stage with a message text?
        regs = Registration.objects.filter(event=event, user=user, active=True)
        regs_count = len(regs)
        has_reg = bool(regs_count)
        if not has_reg:
            msg_text = 'Not found an active registration for the event "{}"'.format(event.title)
            debug_data = {
                "event_code": event_code,
            }
            LOG.info("%s (redirecting): %s", msg_text, debug_data)
            messages.info(request, msg_text)
            # TODO: Already exists redirect?
            context["redirect"] = "SUCCESS"
            return context
        else:
            registration = regs[0]
    except Exception as err:
        error_text = 'Got error while tried to check existed registrations for event "{}"'.format(event_code)
        messages.error(request, error_text)
        #  sError = errorToString(err, show_stacktrace=False)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "event_code": event_code,
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (redirecting to profile): %s", error_text, debug_data)
        # Redirect to profile page with error messages (see above)
        context["redirect"] = "profile"
        return context

    # Get data from registration object, if it's found...
    if registration:
        debug_data = {
            "registration": registration,
        }
        # LOG.debug("Object data: %s", debug_data)
        context["registration"] = registration

    # Final step: prepare data, save created registration, render form...
    try:
        # LOG.debug("Successfully got context: %s", context)
        context["success"] = True
        return context
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "event_code": event_code,
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("Caught error %s (re-raising): %s", sError, debug_data)
        raise err


def event_registration_cancel_confirm_form(
    request: HttpRequest,
    event_code: str,
    form_template: str,
    success_redirect: str = None,
):
    context = get_event_registration_cancel_context(request, event_code=event_code)
    # Redirect on errors or other special cases...
    if "redirect" in context and context["redirect"]:
        if context["redirect"] == "SUCCESS":
            if success_redirect:
                return redirect(success_redirect)  # , event_code=event_code)
        else:
            return redirect(context["redirect"])
    if not context["success"]:
        return redirect("profile")
    # Else render form...
    return render(request, form_template, context)


def event_registration_cancel_process_action(
    request: HttpRequest,
    event_code: str,
    success_redirect: str = None,
):
    context = get_event_registration_cancel_context(request, event_code=event_code)
    # Redirect on errors or other special cases...
    if "redirect" in context and context["redirect"]:
        if context["redirect"] == "SUCCESS":
            if success_redirect:
                return redirect(success_redirect)  # , event_code=event_code)
        else:
            return redirect(context["redirect"])
    if not context["success"]:
        return redirect("profile")
    # Else (on success) make a registration record inactive and go to profile page with a message...
    registration: Registration = context["registration"]
    registration.active = False
    registration.save()
    # Send an email message?
    send_event_registration_cancelled_message(request, context)
    # Show message to the user
    messages.success(request, "Registration has been successfully cancelled")
    # Go to the profile page
    return redirect("profile")
