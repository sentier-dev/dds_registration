# @module dds_registration/views/team_calendar.py
# Serve the private DdS team calendar behind login.

from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse

# The calendar is a self-contained HTML document shipped in the repo, outside
# `static/` so it is never served publicly -- the only way in is this gated view.
CALENDAR_HTML_PATH = Path(__file__).resolve().parent.parent / "team_calendar" / "index.html"


@login_required
def team_calendar(request: HttpRequest) -> HttpResponse:
    """Return the team calendar page to authenticated users only.

    Unauthenticated requests are redirected to ``/accounts/login/?next=`` by
    ``login_required``. The page is standalone HTML, so it is served verbatim
    rather than through the template engine.
    """
    html = CALENDAR_HTML_PATH.read_text(encoding="utf-8")
    return HttpResponse(html)


__all__ = [team_calendar]
