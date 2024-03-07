from django.urls import path
from django.contrib import admin
from django.views.decorators.cache import cache_page
from django.conf import settings

from . import views

cache_timeout = 15 * 60  # in seconds: {min}*60
if settings.LOCAL or settings.DEBUG:
    cache_timeout = 0

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", views.index, name="index"),
    path("me", views.events_mine, name="events_mine"),
    path("event/<str:code>", views.events_main, name="event_view"),

    # Demo pages...
    path('components-demo', views.components_demo, name='components_demo'),

    # Service pages...
    path('robots.txt', cache_page(cache_timeout)(views.RobotsView.as_view()), name='robots'),
    #  url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemap.sitemaps_dict}, name='sitemap'),
]
