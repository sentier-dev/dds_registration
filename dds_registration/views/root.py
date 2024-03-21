# @module views
# @changed 2024.03.21, 17:23

import logging
from functools import reduce

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import redirect, render

from ..models import Event
from .helpers import get_events_list

LOG = logging.getLogger(__name__)


def index(request: HttpRequest):
    user = request.user
    events = Event.objects.filter(public=True)
    #  # This user' events' registrations...
    #  registered_events = {}
    #  if user.is_authenticated:
    #      registered_events = {event.code: event.has_active_user_registration(user) for event in events}
    # Prepare data to display...
    events_data = []
    for event in events:
        user_registration = event.get_active_user_registration(user)
        data = {
            'event_code': event.code,
            'event': event,
            'user_registration': user_registration,
            'user_has_registration': bool(user_registration),
        }
        events_data.append(data)
    context = {
        'events_data': events_data,
    }
    #  debug_data = {
    #      #  'registered_events': registered_events,
    #      'events': events,
    #      'context': context,
    #  }
    #  LOG.debug('Render landing', debug_data)
    return render(request, 'dds_registration/index.html.django', context)


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
    #     messages.info(request, "You don't have any active registrations yet")
    return render(request, 'dds_registration/profile.html.django', context)


def components_demo(request: HttpRequest):
    return render(request, 'components-demo.html.django')


__all__ = [
    index,
    profile,
    components_demo,
]
