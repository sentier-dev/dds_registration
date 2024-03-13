# @module views
# @changed 2024.03.13, 16:09

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import render, redirect


import logging


from ..models import (
    Event,
)

from .helpers import (
    get_events_list,
)


LOG = logging.getLogger(__name__)


def index(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect('profile')
    else:
        return render(request, 'dds_registration/index.html.django')


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


def components_demo(request: HttpRequest):
    return render(request, 'components-demo.html.django')


__all__ = [
    index,
    profile,
    components_demo,
]
