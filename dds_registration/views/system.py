import logging

from django.contrib.sites.models import Site
from django.shortcuts import render
from django.views.generic import TemplateView


LOG = logging.getLogger(__name__)


# Misc...


class RobotsView(TemplateView):
    template_name = "robots.txt"
    content_type = "text/plain"

    def get_context_data(self, **kwargs):
        context = super(RobotsView, self).get_context_data(**kwargs)
        site = Site.objects.get_current()
        context["site"] = site
        scheme = "https" if self.request.is_secure() else "http"
        context["scheme"] = scheme
        return context


# Error pages...


def page403(request, *args, **argv):
    LOG.error("403 error")
    return render(request, "403.html", {}, status=403)


def page404(request, *args, **argv):
    LOG.error("404 error")
    return render(request, "404.html", {}, status=404)


def page500(request, *args, **argv):
    LOG.error("500 error")
    return render(request, "500.html", {}, status=500)


__all__ = [
    RobotsView,
    page403,
    page404,
    page500,
]
