# @module dds_registration/views/team_calendar.py
# Serve the private DdS team calendar behind login.

import logging
from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse

LOG = logging.getLogger(__name__)

# The calendar is a self-contained HTML document that lives outside `static/`,
# so it is never served publicly -- the only way in is this gated view. The
# real calendar is deployed to `settings.TEAM_CALENDAR_PATH` separately from
# the app release; the file bundled in the repo is a placeholder without data.

# The calendar is published without review of this app's maintainers, so it runs
# in a sandboxed (opaque) origin: its script cannot use the visitor's session on
# this site. It needs scripts and outbound links, nothing else.
SANDBOX_POLICY = "sandbox allow-scripts allow-popups allow-popups-to-escape-sandbox"

UNAVAILABLE_HTML = (
    "<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'>"
    "<title>DdS Team Calendar</title></head><body>"
    "<p>The team calendar is not available right now. Please try again later.</p>"
    "</body></html>"
)


@login_required
def team_calendar(request: HttpRequest) -> HttpResponse:
    """Return the team calendar page to authenticated users only.

    Unauthenticated requests are redirected to ``/accounts/login/?next=`` by
    ``login_required``. The page is standalone HTML, so it is served verbatim
    rather than through the template engine. The file is read on every request,
    so a newly deployed calendar shows up without a restart.
    """
    path = Path(settings.TEAM_CALENDAR_PATH)
    try:
        html = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        LOG.error("Team calendar file %s cannot be read: %s", path, error)
        response = HttpResponse(UNAVAILABLE_HTML, status=503)
    else:
        response = HttpResponse(html)
    response["Content-Security-Policy"] = SANDBOX_POLICY
    return response


__all__ = [team_calendar]
