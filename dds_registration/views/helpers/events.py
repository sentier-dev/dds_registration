# @module dds_registration/views/helpers.py
# @changed 2024.04.04, 20:27

import logging
import traceback
from functools import reduce

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import AnonymousUser
from django.contrib.sites.shortcuts import get_current_site
from django.core import signing
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.template.loader import render_to_string

from ...core.helpers.errors import errorToString

from ...models import (
    REGISTRATION_ACTIVE_QUERY,
    Event,
    Registration,
    RegistrationOption,
    User,
)

# For django_registration related stuff, see:
# .venv/Lib/site-packages/django_registration/backends/activation/views.py

REGISTRATION_SALT = getattr(settings, "REGISTRATION_SALT", "registration")


LOG = logging.getLogger(__name__)


def get_activation_key(user: AbstractBaseUser | AnonymousUser):
    """
    Generate the activation key which will be emailed to the user.
    Adopted from: .venv/Lib/site-packages/django_registration/backends/activation/views.py
    """
    return signing.dumps(obj=user.get_username(), salt=REGISTRATION_SALT)


def get_email_context(request: HttpRequest, activation_key: str):
    """
    Build the template context used for the activation email.
    Adopted from: .venv/Lib/site-packages/django_registration/backends/activation/views.py
    """
    scheme = "https" if request.is_secure() else "http"
    return {
        "scheme": scheme,
        "activation_key": activation_key,
        "expiration_days": settings.ACCOUNT_ACTIVATION_DAYS,
        "site": get_current_site(request),
    }


def send_re_actvation_email(request: HttpRequest, user: AbstractBaseUser | AnonymousUser):
    """
    Send the activation email. The activation key is the username,
    signed using TimestampSigner.
    Adopted from: .venv/Lib/site-packages/django_registration/backends/activation/views.py
    """
    try:
        # TODO: Use changed for the re-activate case template?
        email_body_template = "django_registration/activation_email_body.txt"
        email_subject_template = "django_registration/activation_email_subject.txt"
        activation_key = get_activation_key(user)
        context = get_email_context(request, activation_key)
        context["user"] = user

        subject = render_to_string(
            template_name=email_subject_template,
            context=context,
            request=request,
        )
        # Force subject to a single line to avoid header-injection issues.
        subject = "".join(subject.splitlines()).strip()
        message = render_to_string(
            template_name=email_body_template,
            context=context,
            request=request,
        )
        user.email_user(subject, message)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("Caught error %s (re-raising): %s", sError, debug_data)
        raise err


def get_events_list(request: HttpRequest, events: list[Event]):
    if not events or not events.count():
        return None
    result = []
    for event in events:
        event_info = {"event": event, "registration": None}
        if request.user.is_authenticated:
            try:
                # Look for a possible registration by the user
                registration = event.registrations.get(REGISTRATION_ACTIVE_QUERY, user=request.user)
                event_info["registration"] = registration
                # Look for a possible invoice by the user
                if registration:
                    invoice = registration.invoice
                    event_info["invoice"] = invoice
                result.append(event_info)
            except Registration.DoesNotExist:
                pass
            except Exception as err:
                sError = errorToString(err, show_stacktrace=False)
                sTraceback = str(traceback.format_exc())
                debug_data = {
                    "events": events,
                    "event_info": event_info,
                    "err": err,
                    "traceback": sTraceback,
                }
                LOG.error("Caught error %s (re-raising): %s", sError, debug_data)
    return result


def get_event_registration_form_context(request: HttpRequest, event_code: str, create_new: bool = False):
    context = {
        "event_code": event_code,
    }

    user = request.user
    if not user.is_authenticated:
        context["redirect"] = "index"
        return context

    # Variables to collect the data for form context...
    event = None
    reg = None
    reg_options = None
    checked_option_ids = []  # Will be got from post request, see below
    # Is data ready to save
    data_ready = False

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
        regs = Registration.objects.filter(REGISTRATION_ACTIVE_QUERY, event=event, user=user)
        # regs = Registration.objects.filter(event=event, user=user, active=True)
        regs_count = len(regs)
        has_reg = bool(regs_count)
        if not create_new:
            if not has_reg:
                msg_text = 'Not found an active registration for the event "{}"'.format(event.title)
                debug_data = {
                    "event_code": event_code,
                }
                LOG.info("%s (redirecting): %s", msg_text, debug_data)
                messages.info(request, msg_text)
                # TODO: Already exists redirect?
                context["redirect"] = "profile"
                return context
            else:
                reg = regs[0]
        elif has_reg:
            msg_text = 'An active registration for the event "{}" already exists'.format(event.title)
            debug_data = {
                "event_code": event_code,
            }
            LOG.info("%s (redirecting): %s", msg_text, debug_data)
            messages.info(request, msg_text)
            context["redirect"] = "profile"
            return context
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

    # Try to get all available for this event options...
    try:
        reg_options = RegistrationOption.objects.filter(event=event)
        context["reg_options"] = reg_options
    except Exception as err:
        error_text = 'Got error while finding registration options for event "{}"'.format(event_code)
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
    if reg:
        option = reg.option
        options = [option]
        checked_option_ids = list(map(lambda item: item.id, options))

    # If request has posted form data...
    has_post_data = request.method == "POST"
    if has_post_data:
        # Retrieve new options list from the post data...
        new_checked_option_ids = request.POST.getlist("checked_option_ids")
        checked_option_ids = list(map(int, new_checked_option_ids))
        # Allow form save
        data_ready = True

    # Final step: prepare data, save created registration, render form...
    try:
        # NOTE: It's required to have at least one checked basic option! Going to check it...
        reg_options_basic = reg_options.all()
        reg_options_basic_ids = list(map(lambda item: item.id, reg_options_basic))
        reg_options_basic_checked_ids = list(set(checked_option_ids) & set(reg_options_basic_ids))
        has_reg_options_basic_checked = bool(len(reg_options_basic_checked_ids))
        many_reg_options_basic_checked = has_reg_options_basic_checked and len(reg_options_basic_checked_ids) > 1
        if not has_reg_options_basic_checked:
            # Only if any basic options already exist...
            if len(reg_options_basic_ids):
                # Return to form editing and show message
                error_text = "At least one basic option should be selected"
                # Silently make the first available (if any) basic option selected...
                if len(reg_options_basic_ids):
                    checked_option_ids.append(reg_options_basic_ids[0])
                if has_post_data:
                    # If had user data posted then show an error mnessgae...
                    messages.warning(request, error_text)
                data_ready = False
        elif many_reg_options_basic_checked:
            # Return to form editing and show message
            error_text = "Only one basic option should be selected"
            checked_option_ids = [reg_options_basic_ids[0]]
            if has_post_data:
                # If had user data posted then show an error mnessgae...
                messages.warning(request, error_text)
            data_ready = False
        context["reg_options_basic"] = reg_options_basic
        context["checked_option_ids"] = checked_option_ids
        # If data_ready: save data and go to the next stage
        if data_ready:
            # TODO: If data_ready: save data and go to the next stage
            options = RegistrationOption.objects.filter(id__in=checked_option_ids)
            option = options[0] if len(options) else None
            if not reg and create_new:
                # Create new object for a 'create new' strategy...
                reg = Registration()
                reg.event = event
                reg.user = user
            # Set/update parameters...
            reg.option = option
            # The status is set to either SUBMITTED or PAYMENT_PENDING, depending on the event type
            reg.status = "SUBMITTED"  # Later will be changed to "PAYMENT_PENDING" ()at the moment of invoice creation)
            # TODO: Issue #63: Create and set an invoice? + Add a template selection to the form?
            reg.save()  # Save object before set many-to-many relations
            # Redirect to the success message page
            context["redirect"] = "SUCCESS"
            context["registration_created"] = True
            return context
        # LOG.debug("Rendering with context: %s", context)
        context["render"] = True
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


def event_registration_form(
    request: HttpRequest,
    event_code: str,
    form_template: str,
    success_redirect: str = None,
    create_new: bool = False,
):
    context = get_event_registration_form_context(request, event_code=event_code, create_new=create_new)
    # Redirect on errors or other special cases...
    if "redirect" in context:
        if context["redirect"] == "SUCCESS":
            if success_redirect:
                return redirect(success_redirect, event_code=event_code)
        elif context["redirect"] == "event_registration_new_success":
            return redirect(context["redirect"], event_code=event_code)
        else:
            return redirect(context["redirect"])
    # Else render form...
    return render(request, form_template, context)


def show_registration_form_success(request: HttpRequest, event_code: str, template: str):
    user = request.user
    if not user.is_authenticated:
        return redirect("index")

    # TODO: To check if active registration is present?

    # Try to get event object by code...
    try:
        event = Event.objects.get(code=event_code)
    except Exception as err:
        error_text = 'Not found event "{}"'.format(event_code)
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
        return redirect("profile")

    context = {
        "event_code": event_code,
        "event": event,
    }
    return render(request, template, context)


def calculate_total_registration_price(registration: Registration) -> int:
    option = registration.option
    options = [option]
    options_price = reduce(lambda sum, opt: sum + opt.price if opt.price else sum, options, 0)
    total_price = options_price
    return total_price


def get_event_registration_context(request: HttpRequest, event_code: str):
    user = request.user
    scheme = "https" if request.is_secure() else "http"
    context = {
        "event_code": event_code,
        "user": user,
        "site": get_current_site(request),
        "scheme": scheme,
    }
    event = None
    registration = None
    invoice = None
    # Try to get event object by code...
    try:
        event = Event.objects.get(code=event_code)
        registration = event.registrations.get(REGISTRATION_ACTIVE_QUERY, user=user, event=event)
        if not registration:
            raise Exception("Not found active registrations")
        context["event"] = event
        context["registration"] = registration
        context["total_price"] = calculate_total_registration_price(registration)  # Is it used?
        context["invoice"] = registration.invoice
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        error_text = 'Not found event code "{}": {}'.format(event_code, sError)
        messages.error(request, error_text)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "event_code": event_code,
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("%s (redirecting to profile): %s", error_text, debug_data)
        raise Exception(error_text)
    return context


def send_event_registration_success_message(request: HttpRequest, event_code: str):
    """
    Send successful event registration created message to the user

    TODO: Send different messages depending on the `payment_method`?

    TODO: Issue #74: Send invoice pdf (see `create_invoice_pdf`) as atachment for `INVOICE` payment method
    """

    email_body_template = "dds_registration/event_registration_new_success_message_body.txt"
    email_subject_template = "dds_registration/event_registration_new_success_message_subject.txt"

    user = request.user

    context = get_event_registration_context(request, event_code)

    invoice = context.get("invoice")

    try:
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
        user.email_user(subject, body)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("Caught error %s (re-raising): %s", sError, debug_data)
        raise err


__all__ = [
    get_events_list,
    event_registration_form,
    show_registration_form_success,
    get_event_registration_context,
]
