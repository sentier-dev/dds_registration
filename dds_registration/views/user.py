import logging
import traceback

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import redirect, render

from ..core.helpers.errors import errorToString

from ..forms import UpdateUserForm
from .helpers import send_re_actvation_email

LOG = logging.getLogger(__name__)


@login_required
def edit_user_profile(request: HttpRequest):
    """
    @see https://dev.to/earthcomfy/django-update-user-profile-33ho

    TODO: If don't need to use complex combination of two forms ()user and
    linked profile), then we probably could use django stock form handling
    mechanism?
    """
    try:
        success = True
        user = request.user
        if request.method == "POST":
            user_form = UpdateUserForm(request.POST, instance=user)
            #  # UNUSED: Address has integrated into the base user model
            #  profile, created = Profile.objects.get_or_create(user=user)
            #  profile_form = UpdateProfileForm(
            #      request.POST,
            #      #  request.FILES,
            #      instance=profile,
            #  )
            if user_form.is_valid():  # and profile_form.is_valid():
                user_data = user_form.cleaned_data
                email_has_changed = "email" in user_form.changed_data
                #  profile_data = profile_form.cleaned_data
                debug_data = {
                    "email_has_changed": email_has_changed,
                }
                LOG.debug("Save params: %s", debug_data)
                # TODO: Send email activation request and make the user inactive
                LOG.debug("Save user data: %s", user_data)
                user_form.save()
                #  profile_form.save()
                if email_has_changed:
                    debug_data = {
                        "email_has_changed": email_has_changed,
                        "user_form": user_form,
                    }
                    LOG.debug("Email has changed: %s", debug_data)
                    send_re_actvation_email(request, user)
                    user.is_active = False
                    user.save()
                    messages.success(
                        request,
                        "Your email has already changed. Now you have to re-activate your account. Please check your e-mail for an activation message.",
                    )
                    # TODO: Use specific template
                    return redirect("django_registration_complete")
                messages.success(request, "Your profile is updated successfully")
                if success:
                    return redirect("profile")
        else:
            user_form = UpdateUserForm(instance=user)
            #  profile, created = Profile.objects.get_or_create(user=user)
            #  profile_form = UpdateProfileForm(instance=profile)
        context = {
            "user_form": user_form,
            #  'profile_form': profile_form,
        }
        return render(request, "dds_registration/profile_edit.html.django", context)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            "err": err,
            "traceback": sTraceback,
        }
        LOG.error("Caught error %s (re-raising): %s", sError, debug_data)
        raise err
