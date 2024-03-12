# @module views
# @changed 2024.03.12, 23:14

# from django.conf import settings
from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site  # To access site properties
from django.db.models.query_utils import Q  # To use for objects querying
from django.http import HttpRequest, HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404

# from django.template.defaultfilters import slugify
# from django.utils import timezone
from django.views.generic import TemplateView

import traceback
import logging

from core.helpers.errors import errorToString

from .models import (
    Event,
    Registration,
    RegistrationOption,
    # Message,
    # DiscountCode,
    # GroupDiscount,
)


LOG = logging.getLogger(__name__)


def index(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect('profile')
    else:
        return render(request, 'dds_registration/index.html.django')


def get_events_list(request: HttpRequest, events: list[Event], show_archived=False):
    if not events or not events.count():
        return None
    result = []
    for event in events:
        event_info = {'event': event, 'registration': None}
        #  # Hide events that the user can not list
        #  if not event.user_can_list(request.user, show_archived):
        #      continue
        if request.user.is_authenticated:
            # Look for a possible registration by the user
            try:
                #  registration = event.get_active_registrations().get(user=request.user)
                registration = event.registrations.get(user=request.user, active=True)
                event_info['registration'] = registration
                #  event_info["user_can_cancel"] = registration.user_can_cancel(
                #      request.user
                #  )
                result.append(event_info)
            except Registration.DoesNotExist:
                pass
            except Exception as err:
                sError = errorToString(err, show_stacktrace=False)
                sTraceback = str(traceback.format_exc())
                debug_data = {
                    'events': events,
                    'event_info': event_info,
                    'err': err,
                    'traceback': sTraceback,
                }
                LOG.error('Caught error %s (re-raising): %s', sError, debug_data)

            #  event_info["user_can_book"] = event.user_can_book(request.user)
            #  event_info["user_can_update"] = event.user_can_update(request.user)
            #  event_info["price_for_user"] = event.user_price(request.user)
    return result


@login_required
def profile(request: HttpRequest):
    if not request.user.is_authenticated:
        return redirect('index')
    context = {'events_shown': 'mine'}
    events = Event.objects.all()  # filter(query).distinct()
    events_list = get_events_list(request, events)
    if events_list and len(events_list):
        context['events'] = events_list
    # else:
    #     messages.info(request, "You don't have any registrations yet")
    return render(request, 'dds_registration/profile.html.django', context)


def get_event_registration_form_context(request: HttpRequest, event_code: str, create_new: bool = False):
    context = {
        'event_code': event_code,
    }

    user = request.user
    if not user.is_authenticated:
        context['redirect'] = 'index'
        return context

    # Variables to collect the data for form context...
    event = None
    reg = None
    reg_options = None
    checked_option_ids = []  # Will be got from post request, see below
    payment_method = Registration.DEFAULT_PAYMENT_METHOD
    # Is data ready to save
    data_ready = False

    # Try to get event object by code...
    try:
        event = Event.objects.get(code=event_code)
    except Exception as err:
        error_text = 'Not found event code "{}"'.format(event_code)
        messages.error(request, error_text)
        #  sError = errors.toString(err, show_stacktrace=False)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            'event_code': event_code,
            'err': err,
            'traceback': sTraceback,
        }
        LOG.error('%s (redirecting to profile): %s', error_text, debug_data)
        # Redirect to profile page with error messages (see above)
        context['redirect'] = 'profile'
        return context

    context['event'] = event

    # Try to find active registrations for this event (prevent constrain exception)...
    try:
        # TODO: Go to the next stage with a message text?
        regs = Registration.objects.filter(event=event, active=True)
        regs_count = len(regs)
        has_reg = bool(regs_count)
        if not create_new:
            if not has_reg:
                msg_text = 'Not found an active registration for the event "{}"'.format(event.title)
                debug_data = {
                    'event_code': event_code,
                }
                LOG.info('%s (redirecting): %s', msg_text, debug_data)
                messages.info(request, msg_text)
                # TODO: Already exists redirect?
                context['redirect'] = 'SUCCESS'
                return context
            else:
                reg = regs[0]
        elif has_reg:
            msg_text = 'An active registration for the event "{}" already exists'.format(event.title)
            debug_data = {
                'event_code': event_code,
            }
            LOG.info('%s (redirecting): %s', msg_text, debug_data)
            messages.info(request, msg_text)
            context['redirect'] = 'profile'
            return context
    except Exception as err:
        error_text = 'Got error while tried to check existed registrations for event "{}"'.format(event_code)
        messages.error(request, error_text)
        #  sError = errors.toString(err, show_stacktrace=False)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            'event_code': event_code,
            'err': err,
            'traceback': sTraceback,
        }
        LOG.error('%s (redirecting to profile): %s', error_text, debug_data)
        # Redirect to profile page with error messages (see above)
        context['redirect'] = 'profile'
        return context

    # Try to get all available for this event options...
    try:
        reg_options = RegistrationOption.objects.filter(event=event)
        context['reg_options'] = reg_options
    except Exception as err:
        error_text = 'Got error while finding registration options for event "{}"'.format(event_code)
        messages.error(request, error_text)
        #  sError = errors.toString(err, show_stacktrace=False)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            'event_code': event_code,
            'err': err,
            'traceback': sTraceback,
        }
        LOG.error('%s (redirecting to profile): %s', error_text, debug_data)
        # Redirect to profile page with error messages (see above)
        context['redirect'] = 'profile'
        return context

    # Get data from registration object, if it's found...
    if reg:
        payment_method = reg.payment_method
        options = reg.options
        checked_option_ids = list(map(lambda item: item.id, options.all()))
        debug_data = {
            'reg': reg,
            'payment_method': payment_method,
            'checked_option_ids': checked_option_ids,
        }
        LOG.debug('Object data: %s', debug_data)

    # If request has posted form data...
    has_post_data = request.method == 'POST'
    if has_post_data:
        # Get payment method...
        payment_method = request.POST.get('payment_method', Registration.DEFAULT_PAYMENT_METHOD)
        # Retrieve new options list from the post data...
        new_checked_option_ids = request.POST.getlist('checked_option_ids')
        checked_option_ids = list(map(int, new_checked_option_ids))
        debug_data = {
            'request.POST': request.POST,
            'payment_method': payment_method,
            'checked_option_ids': checked_option_ids,
        }
        LOG.debug('Post data: %s', debug_data)
        # Allow form save
        data_ready = True

    # Final step: prepare data, save created registration, render form...
    try:
        # NOTE: It's required to have at least one checked basic option! Going to check it...
        reg_options_basic = reg_options.filter(add_on=False)
        reg_options_basic_ids = list(map(lambda item: item.id, reg_options_basic))
        reg_options_basic_checked_ids = list(set(checked_option_ids) & set(reg_options_basic_ids))
        has_reg_options_basic_checked = bool(len(reg_options_basic_checked_ids))
        if not has_reg_options_basic_checked:
            # Continue form edit and show message
            error_text = 'At least one basic option should be selected'
            debug_data = {
                'reg_options': reg_options,
                'reg_options_basic': reg_options_basic,
                'reg_options_basic_ids': reg_options_basic_ids,
                'reg_options_basic_checked_ids': reg_options_basic_checked_ids,
                'has_reg_options_basic_checked': has_reg_options_basic_checked,
                'checked_option_ids': checked_option_ids,
            }
            LOG.error('Checking error: %s: %s', error_text, debug_data)
            if len(reg_options_basic_ids):
                # Silently make the first basic option selected (if no user data has posted yet)...
                checked_option_ids.append(reg_options_basic_ids[0])
            if has_post_data:
                # If had user data posted then show an error mnessgae...
                messages.warning(request, error_text)
            data_ready = False
        #  reg_options_addons = reg_options.filter(add_on=True)
        context['checked_option_ids'] = checked_option_ids
        context['PAYMENT_METHODS'] = Registration.PAYMENT_METHODS
        context['payment_method'] = payment_method
        # If data_ready: save data and go to the next stage
        if data_ready:
            # TODO: If data_ready: save data and go to the next stage
            options = RegistrationOption.objects.filter(id__in=checked_option_ids)
            if not reg and create_new:
                # Create new object for a 'create new' strategy...
                reg = Registration()
                reg.event = event
                reg.user = user
            # Set/update parameters...
            reg.payment_method = payment_method
            if create_new:
                reg.save()  # Save object before set many-to-many relations
            reg.options.set(options)
            reg.save()  # Save object before set many-to-many relations
            debug_data = {
                'options': options,
                'checked_option_ids': checked_option_ids,
                'payment_method': payment_method,
            }
            LOG.debug('Creating a registration: %s', debug_data)
            # TODO: Send an e-mail message
            # Redirect to the success message page
            context['redirect'] = 'SUCCESS'
            context['registration_created'] = True
            return context
        LOG.debug('Rendering with context: %s', context)
        context['render'] = True
        return context
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            'event_code': event_code,
            'err': err,
            'traceback': sTraceback,
        }
        LOG.error('Caught error %s (re-raising): %s', sError, debug_data)
        raise err


def render_event_registration_form(
    request: HttpRequest,
    event_code: str,
    form_template: str,
    success_redirect: str = None,
    create_new: bool = False,
):
    context = get_event_registration_form_context(request, event_code=event_code, create_new=create_new)
    # Redirect on errors or other special cases...
    if 'redirect' in context:
        if context['redirect'] == 'SUCCESS':
            if success_redirect:
                return redirect(success_redirect, event_code=event_code)
        elif context['redirect'] == 'event_registration_new_success':
            return redirect(context['redirect'], event_code=event_code)
        else:
            return redirect(context['redirect'])
    # Else render form...
    return render(request, form_template, context)


@login_required
def event_registration_new(request: HttpRequest, event_code: str):
    return render_event_registration_form(
        request,
        event_code=event_code,
        form_template='dds_registration/event_registration_new.html.django',
        success_redirect='event_registration_new_success',
        create_new=True,
    )


@login_required
def event_registration_edit(request: HttpRequest, event_code: str):
    return render_event_registration_form(
        request,
        event_code=event_code,
        form_template='dds_registration/event_registration_edit.html.django',
        success_redirect='event_registration_edit_success',
    )


def show_registration_form_success(request: HttpRequest, event_code: str, template: str):
    user = request.user
    if not user.is_authenticated:
        return redirect('index')

    # TODO: To check if active registration is present?

    # Try to get event object by code...
    try:
        event = Event.objects.get(code=event_code)
    except Exception as err:
        error_text = 'Not found event "{}"'.format(event_code)
        messages.error(request, error_text)
        #  sError = errors.toString(err, show_stacktrace=False)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            'event_code': event_code,
            'err': err,
            'traceback': sTraceback,
        }
        LOG.error('%s (redirecting to profile): %s', error_text, debug_data)
        # Redirect to profile page with error messages (see above)
        return redirect('profile')

    context = {
        'event_code': event_code,
        'event': event,
    }
    return render(request, template, context)


@login_required
def event_registration_new_success(request: HttpRequest, event_code: str):
    return show_registration_form_success(
        request, event_code=event_code, template='dds_registration/event_registration_new_success.html.django'
    )


@login_required
def event_registration_edit_success(request: HttpRequest, event_code: str):
    return show_registration_form_success(
        request, event_code=event_code, template='dds_registration/event_registration_edit_success.html.django'
    )


def components_demo(request: HttpRequest):
    return render(request, 'components-demo.html.django')


# Misc...


class RobotsView(TemplateView):
    template_name = 'robots.txt'
    content_type = 'text/plain'

    def get_context_data(self, **kwargs):
        context = super(RobotsView, self).get_context_data(**kwargs)
        context['domain'] = Site.objects.get_current().domain
        return context


# Error pages...


def page403(request, *args, **argv):
    LOG.debug('403 error')
    return render(request, '403.html', {}, status=403)


def page404(request, *args, **argv):
    LOG.debug('404 error')
    return render(request, '404.html', {}, status=404)


def page500(request, *args, **argv):
    LOG.debug('500 error')
    return render(request, '500.html', {}, status=500)
