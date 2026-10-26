"""Send members with an incomplete membership record to the details form."""

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse

from ..models import Membership

EXEMPT_PREFIXES = (
    "/admin/",
    "/accounts/",
    "/dashboards/",
    "/static/",
    "/media/",
    "/payments/",
    "/membership/",
    "/hijack/",
    "/captcha/",
    "/robots.txt",
)


class MembershipDetailsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._needs_redirect(request):
            messages.info(request, "Please tell us your organization to complete your membership record.")
            return redirect(reverse("membership_details"))
        return self.get_response(request)

    @staticmethod
    def _needs_redirect(request) -> bool:
        user = getattr(request, "user", None)
        if user is None or not user.is_authenticated or user.is_staff:
            return False
        if request.path.startswith(EXEMPT_PREFIXES):
            return False
        membership = Membership.objects.filter(user=user).only("organization", "organization_type").first()
        return bool(membership and membership.needs_details)
