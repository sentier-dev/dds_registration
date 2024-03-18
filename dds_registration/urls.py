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
    path(
        'accounts/',
        include('django_registration.backends.activation.urls'),
    ),
    path('accounts/', include('django.contrib.auth.urls')),
    #  path(
    #      # Overrided registration form (with extra fields), causes error
    #      'accounts/signup',
    #      views.SignUpView.as_view(),
    #      name='django_registration_register',
    #  ),
    path('profile', views.profile, name='profile'),
    path(
        'profile/edit',
        views.edit_user_profile,
        name='profile_edit',
    ),
    path('event/<str:event_code>/registration/new', views.event_registration_new, name='event_registration_new'),
    path(
        'event/<str:event_code>/registration/new/success',
        views.event_registration_new_success,
        name='event_registration_new_success',
    ),
    path('event/<str:event_code>/registration/edit', views.event_registration_edit, name='event_registration_edit'),
    path(
        'event/<str:event_code>/registration/edit/success',
        views.event_registration_edit_success,
        name='event_registration_edit_success',
    ),
    path(
        'event/<str:event_code>/registration/invoice',
        views.event_registration_invoice,
        name='event_registration_invoice',
    ),
    path(
        'event/<str:event_code>/registration/payment',
        views.event_registration_payment,
        name='event_registration_payment',
    ),
    # Demo pages...
    path('components-demo', views.components_demo, name='components_demo'),
    # Service pages...
    path('robots.txt', cache_page(cache_timeout)(views.RobotsView.as_view()), name='robots'),
    #  url(r'^sitemap\.xml$', 'django.contrib.sitemaps.views.sitemap', {'sitemaps': sitemap.sitemaps_dict}, name='sitemap'),
]
