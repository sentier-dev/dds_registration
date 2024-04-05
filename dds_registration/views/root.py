# @module views
# @changed 2024.03.25, 16:07

import logging

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import redirect, render

from ..models import Event, Registration

LOG = logging.getLogger(__name__)


def index(request: HttpRequest):
    events = [obj for obj in Event.objects.filter(public=True) if obj.can_register]
    if request.user:
        for event in events:
            event.registration = event.get_active_event_registration_for_user(request.user)

    return render(request=request, template_name="dds_registration/index.html.django", context={
            'user': request.user,
            'events': events
        })


@login_required
def profile(request: HttpRequest):
    if not request.user.is_authenticated:
        return redirect("index")
    return render(request=request, template_name="dds_registration/profile.html.django", context={'active_regs': Registration.active_for_user(request.user), 'user': request.user})


def components_demo(request: HttpRequest):
    return render(request, "components-demo.html.django")


__all__ = [
    index,
    profile,
    components_demo,
]
