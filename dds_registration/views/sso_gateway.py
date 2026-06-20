# @module dds_registration/views/sso_gateway.py
# Gateway endpoints that let nginx put the static LCA dashboards on
# dashboard.d-d-s.ch behind this app's SSO, authorised per user and per route.

from django.conf import settings
from django.contrib.auth.views import LoginView
from django.http import HttpRequest, HttpResponse


def dashboard_auth(request: HttpRequest, key: str) -> HttpResponse:
    """Target for nginx ``auth_request`` -- one route (``key``) per dashboard.

    - 401 when there is no session -> nginx redirects to the SSO login.
    - 403 when logged in but not authorised for this dashboard -> nginx shows a
      "forbidden" page (returning 401 here would cause a login loop).
    - 200 when authorised: superusers, or members of the ``dashboard:<key>``
      group.

    The route ``key`` arrives from the URL and authorisation is checked against
    group membership, so the private dashboard names live only in nginx config
    and the database -- never in this (public) repo.
    """
    if not request.user.is_authenticated:
        return HttpResponse(status=401)
    authorised = request.user.is_superuser or request.user.groups.filter(name=f"dashboard:{key}").exists()
    return HttpResponse(status=200 if authorised else 403)


class SubdomainLoginView(LoginView):
    """Login view that also trusts the dashboard host as a ``?next=`` target.

    Django only honours a cross-host ``next`` when the host is explicitly
    allowed, so without this a login started from the dashboard host would
    bounce back to the events home page instead of the requested dashboard.
    """

    def get_success_url_allowed_hosts(self) -> set[str]:
        return {self.request.get_host(), settings.DASHBOARD_HOST}


__all__ = ["dashboard_auth", "SubdomainLoginView"]
