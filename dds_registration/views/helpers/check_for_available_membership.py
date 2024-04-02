# @module dds_registration/views/helpers/check_for_available_membership.py
# @changed 2024.04.02, 14:37


from django.contrib import messages
from django.http import HttpRequest, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import redirect


from ...models import Membership


class check_for_available_membership:
    """
    Check if it's possible to apply for a membership
    """

    response: None | HttpResponsePermanentRedirect | HttpResponseRedirect = None
    success: bool = False

    def __init__(self, request: HttpRequest):
        self.success = True  # Assume success by default
        user = request.user
        # Check for the existing membership...
        if user.is_authenticated:
            memberships = Membership.objects.filter(user=user)
            # Are there memberships for this user?
            if memberships and len(memberships):
                messages.success(request, "You're already a member (or waiting for your membership activation)")
                # TODO: Display the membership data on the profile page?
                self.response = redirect("profile")
                self.success = False

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass
