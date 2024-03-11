from django.urls import include, path
from django.contrib import admin
from django.views.decorators.cache import cache_page
from django.conf import settings

from . import views


cache_timeout = 15 * 60  # in seconds: {min}*60
if settings.LOCAL or settings.DEBUG:
    cache_timeout = 0


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    # Account urls.
    #  path('accounts/', include('accounts.urls')),  # Our own signup extension
    path(
        'accounts/', include('django_registration.backends.activation.urls')
    ),  # django_registration: https://django-registration.readthedocs.io
    path('accounts/', include('django.contrib.auth.urls')),
    path('profile', views.profile, name='profile'),
    path('events/mine', views.events_list_mine, name='events_list_mine'),
    path('event/<str:code>', views.events_view, name='event_view'),
    # Demo pages...
    path('components-demo', views.components_demo, name='components_demo'),
    # Service pages...
    path('robots.txt', cache_page(cache_timeout)(views.RobotsView.as_view()), name='robots'),
    #  url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemap.sitemaps_dict}, name='sitemap'),
]
