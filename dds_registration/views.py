# @module views
# @changed 2024.03.11, 13:24

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
                sTraceback = str(traceback.format_exc())
                LOG.error(
                    'Caught error',
                    {
                        'err': err,
                        'traceback': sTraceback,
                    },
                )
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
    #     messages.info(request, "You don't have any events yet")
    return render(request, 'dds_registration/profile.html.django', context)


@login_required
def event_registration(request: HttpRequest, event_code: str):
    user = request.user
    if not user.is_authenticated:
        return redirect('index')
    event = None
    reg_options = None
    checked_option_ids = []  # Will be got from post request, see below
    # Is data ready to save
    data_ok = False

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

    # TODO: Check if any registrations are existed for this event and user and go to the next stage with a message text?
    # Try to find rgistrations for this event...
    try:
        regs = Registration.objects.filter(event=event)
        if len(regs):
            msg_text = 'You already have a registration for this event'
            debug_data = {
                'event_code': event_code,
            }
            LOG.info('Message: %s (redirecting to profile): %s', msg_text, debug_data)
            messages.info(request, msg_text)
            return redirect('profile')
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
        data_ok = True

    try:
        reg_options_basic = reg_options.filter(add_on=False)
        reg_options_basic_ids = list(map(lambda item: item.id, reg_options_basic))
        reg_options_basic_checked_ids = list(set(checked_option_ids) & set(reg_options_basic_ids))
        has_reg_options_basic_checked = bool(len(reg_options_basic_checked_ids))
        # NOTE: It's required to have at least one checked basic option
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
            data_ok = False
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
            'data_ok': data_ok,
        }
        # If data_ok: save data and go to the next stage
        if data_ok:
            # TODO: If data_ok: save data and go to the next stage
            options = RegistrationOption.objects.filter(id__in=checked_option_ids)
            reg = Registration()
            reg.event = event
            reg.user = user
            reg.save()
            reg.options.set(options)
            debug_data = {
                'options': options,
                'checked_option_ids': checked_option_ids,
            }
            LOG.debug('Creating a registration: %s', debug_data)
            # reg.save()
            # TODO: Redirect to the next stage?
        LOG.debug('Rendering with context: %s', context)
        return render(request, 'dds_registration/event_registration.html.django', context)
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
