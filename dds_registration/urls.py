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
        # @see https://django-registration.readthedocs.io/en/latest/quickstart.html#setting-up-urls
        # The following URL names are defined by django_registration.backends.activation.urls:
        # - django_registrater is the account-registration view.
        # - django_registration_complete is the post-registration success message.
        # - django_registration_activate is the account-activation view.
        # - django_registration_activation_complete is the post-activation success message.
        # - django_registration_disallowed is a message indicating registration is not currently permitted.
        'accounts/',
        include('django_registration.backends.activation.urls'),
    ),  # django_registration: https://django-registration.readthedocs.io
    path('accounts/', include('django.contrib.auth.urls')),
    path('profile', views.profile, name='profile'),
    #  path('event/<str:code>', views.events_view, name='event_view'), # ???
    path('event/<str:event_code>/registration', views.event_registration, name='event_registration'),
    # Demo pages...
    path('components-demo', views.components_demo, name='components_demo'),
    # Service pages...
    path('robots.txt', cache_page(cache_timeout)(views.RobotsView.as_view()), name='robots'),
    #  url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemap.sitemaps_dict}, name='sitemap'),
]
