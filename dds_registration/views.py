# from django.conf import settings
from multiprocessing.managers import BaseManager
from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.db.models.query_utils import Q
from django.http import HttpRequest, HttpResponse, Http404

from django.shortcuts import render, redirect, get_object_or_404

# from django.template.defaultfilters import slugify
# from django.utils import timezone
from django.views.generic import TemplateView

import traceback
import logging

from .models import Event, Registration, RegistrationOption, Message, DiscountCode, GroupDiscount


LOG = logging.getLogger(__name__)


def index(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect('profile')
    else:
        return render(request, 'landing.html.django')


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
def events_list_mine(request: HttpRequest):
    # We don't have personalities in event objects
    context = {'events_shown': 'mine'}
    #  query = Q(registrations__person=request.user,
    #            #  registrations__cancelledOn=None,
    #            )
    # query = query | Q(organisers=request.user)
    # query = query | Q(owner=request.user)
    events = Event.objects.all()  # filter(query).distinct()
    events_list = get_events_list(request, events)
    if not events_list or not len(events_list):
        messages.info(request, "You don't have any events yet")
    else:
        context['events'] = events_list
    return render(request, 'events_list.html.django', context)


@login_required
def profile(request: HttpRequest):
    if not request.user.is_authenticated:
        return redirect('index')
    context = {'events_shown': 'mine'}
    events = Event.objects.all()  # filter(query).distinct()
    events_list = get_events_list(request, events)
    if not events_list or not len(events_list):
        messages.info(request, "You don't have any events yet")
    else:
        #  messages.success(request, 'Already has events: {}'.format(len(events_list)))
        context['events'] = events_list
    return render(request, 'profile.html.django', context)


def events_view(request: HttpRequest, code):
    # TODO: View particular event application
    try:
        event = Event.objects.get(code=code)
    except Event.DoesNotExist:
        return Http404

    return render(request, 'profile.html.django', {'event': event})


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
