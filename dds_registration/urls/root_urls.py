# @module XXX
# @changed 2024.04.02, 00:28

from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.decorators.cache import cache_page

from .. import views
from .application_urls import urlpatterns as application_urlpatterns

cache_timeout = 0 if settings.DEV or settings.DEBUG else 15 * 60  # in seconds: {min}*60

urlpatterns = [
    # App-provided paths...
    path("admin/", admin.site.urls, name="admin"),
    path("captcha/", include("captcha.urls")),
    path("hijack/", include("hijack.urls")),
    path("applications/", include((application_urlpatterns, "djf_surveys"))),
    # Service pages...
    path(
        "robots.txt",
        cache_page(cache_timeout)(views.RobotsView.as_view()),
        name="robots",
    ),
]

if settings.DEV:
    # Demo pages (for debug/dev purposes only)...
    urlpatterns.append(
        path("components-demo", views.components_demo, name="components_demo"),
    )
