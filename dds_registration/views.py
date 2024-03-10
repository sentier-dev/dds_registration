from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.http.response import Http404
from django.http import HttpRequest, HttpResponse
from django.views.generic import TemplateView
from django.contrib.sites.models import Site
import logging

from .models import Event


LOG = logging.getLogger(__name__)


def index(request: HttpRequest):
    if request.user.is_authenticated:
        return redirect("profile")
    else:
        return render(request, "landing.html.django")


# def login(request: HttpRequest, code):
#     """
#     See: https://docs.djangoproject.com/en/5.0/topics/auth/default/
#     """
#     try:
#         event = Event.objects.get(code=code)
#     except Event.DoesNotExist:
#         return Http404

#     return render(request, "login.html.django", {"event": event})


@login_required
def profile(request: HttpRequest):
    if not request.user.is_authenticated:
        return redirect("index")

    return render(request, "profile.html.django")


def events_view(request: HttpRequest, code):
    # TODO: View particular event application
    try:
        event = Event.objects.get(code=code)
    except Event.DoesNotExist:
        return Http404

    return render(request, "profile.html.django", {"event": event})


def components_demo(request: HttpRequest):
    return render(request, "components-demo.html.django")


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
