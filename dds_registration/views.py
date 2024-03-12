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
    for evt in events:
        event_info = {'event': evt, 'registration': None}
        #  # Hide events that the user can not list
        #  if not evt.user_can_list(request.user, show_archived):
        #      continue
        if request.user.is_authenticated:
            # Look for a possible registration by the user
            try:
                user_registration = evt.get_active_registrations().get(user=request.user)
                event_info['registration'] = user_registration
                #  event_info["user_can_cancel"] = user_registration.user_can_cancel(
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

            #  event_info["user_can_book"] = evt.user_can_book(request.user)
            #  event_info["user_can_update"] = evt.user_can_update(request.user)
            #  event_info["price_for_user"] = evt.user_price(request.user)
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


@login_required
def event_registration_new(request: HttpRequest, event_code: str):
    user = request.user
    if not user.is_authenticated:
        return redirect('index')
    event = None
    reg_options = None
    checked_option_ids = []  # Will be got from post request, see below
    payment_method = Registration.DEFAULT_PAYMENT_METHOD
    # Is data ready to save
    data_ready = False

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

    # Try to find active registrations for this event (prevent constrain exception)...
    try:
        # TODO: Go to the next stage with a message text?
        regs = Registration.objects.filter(event=event, active=True)
        if len(regs):
            msg_text = 'The registration for this event already exists'
            debug_data = {
                'event_code': event_code,
            }
            LOG.info('%s (redirecting): %s', msg_text, debug_data)
            messages.info(request, msg_text)
            return redirect('event_registration_new_success', event_code=event_code)
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
        return redirect('profile')

    # Try to get event options...
    try:
        reg_options = RegistrationOption.objects.filter(event=event)
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
        return redirect('profile')

    # If request has posted form data...
    has_post_data = request.method == 'POST'
    if has_post_data:
        # Get payment method...
        if 'payment_method' in request.POST:
            payment_method = request.POST.get('payment_method')
        # Retrieve new options list from the post data...
        if 'checked_option_ids' in request.POST:
            new_checked_option_ids = request.POST.getlist('checked_option_ids')
            checked_option_ids = list(map(int, new_checked_option_ids))
        debug_data = {
            'checked_option_ids': checked_option_ids,
            'has_post_data': has_post_data,
            'reg_options': reg_options,
            'request.POST': request.POST,
        }
        LOG.debug('Post data: %s', debug_data)
        # Allow form save
        data_ready = True
        return redirect('event_registration_new_success', event_code=event_code)

    # Final step: prepare data, save created registration, render form...
    try:
        reg_options_basic = reg_options.filter(add_on=False)
        reg_options_basic_ids = list(map(lambda item: item.id, reg_options_basic))
        reg_options_basic_checked_ids = list(set(checked_option_ids) & set(reg_options_basic_ids))
        has_reg_options_basic_checked = bool(len(reg_options_basic_checked_ids))
        # NOTE: It's required to have at least one checked basic option!
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
        reg_options_addons = reg_options.filter(add_on=True)
        context = {
            'event_code': event_code,
            'username': user.username,
            'event': event,
            'reg_options': reg_options,
            'reg_options_basic': reg_options_basic,
            'reg_options_basic_ids': reg_options_basic_ids,
            'has_reg_options_basic_checked': has_reg_options_basic_checked,
            'reg_options_addons': reg_options_addons,
            'checked_option_ids': checked_option_ids,
            'PAYMENT_METHODS': Registration.PAYMENT_METHODS,
            'payment_method': payment_method,
            'data_ready': data_ready,
        }
        # If data_ready: save data and go to the next stage
        if data_ready:
            # TODO: If data_ready: save data and go to the next stage
            options = RegistrationOption.objects.filter(id__in=checked_option_ids)
            reg = Registration()
            reg.event = event
            reg.user = user
            reg.payment_method = payment_method
            reg.save()  # Save object before set many-to-many relations
            reg.options.set(options)
            debug_data = {
                'options': options,
                'checked_option_ids': checked_option_ids,
                'payment_method': payment_method,
            }
            LOG.debug('Creating a registration: %s', debug_data)
            # TODO: Send a message
            # Redirect to the success message page
            return redirect('event_registration_new_success', event_code=event_code)
            # reg.save() # Do save again?
        LOG.debug('Rendering with context: %s', context)
        return render(request, 'dds_registration/event_registration_new.html.django', context)
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


@login_required
def event_registration_edit(request: HttpRequest, event_code: str):
    user = request.user
    if not user.is_authenticated:
        return redirect('index')

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
        'event': event,
    }
    return render(request, 'dds_registration/event_registration_edit.html.django', context)


@login_required
def event_registration_new_success(request: HttpRequest, event_code: str):
    user = request.user
    if not user.is_authenticated:
        return redirect('index')

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
    return render(request, 'dds_registration/event_registration_new_success.html.django', context)


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
