# @module dds_registration/views/user.py
# @changed 2024.03.15, 19:53

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.sites.shortcuts import get_current_site
from django.http import HttpRequest
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.conf import settings
from django.views import generic

# from django_registration.views import RegistrationView as BaseSignUpView

from functools import reduce
import traceback
import logging

from core.helpers.errors import errorToString

from ..forms import SignUpForm, UpdateUserForm, UpdateProfileForm

from ..models import (
    Profile,
)

from .helpers import send_re_actvation_email


LOG = logging.getLogger(__name__)


# class SignUpView(BaseSignUpView):
#     # NOTE: It causes a bug: `NonImplemented`
#     form_class = SignUpForm


@login_required
def edit_user_profile(request: HttpRequest):
    """
    @see https://dev.to/earthcomfy/django-update-user-profile-33ho
    """
    try:
        success = True
        user = request.user
        if request.method == 'POST':
            user_form = UpdateUserForm(request.POST, instance=user)
            profile, created = Profile.objects.get_or_create(user=user)
            profile_form = UpdateProfileForm(
                request.POST,
                #  request.FILES,
                instance=profile,
            )
            if user_form.is_valid() and profile_form.is_valid():
                user_data = user_form.cleaned_data
                #  old_user = User.objects.get(id=user.id)
                # old_user.email != user_data['email']
                email_has_changed = 'email' in user_form.changed_data
                profile_data = profile_form.cleaned_data
                debug_data = {
                    'email_has_changed': email_has_changed,
                }
                LOG.debug('Save params: %s', debug_data)
                # TODO: Send email activation request and make the user inactive
                LOG.debug('Save user data: %s', user_data)
                LOG.debug('Save profile data: %s', profile_data)
                user_form.save()
                profile_form.save()
                if email_has_changed:
                    debug_data = {
                        'email_has_changed': email_has_changed,
                        'user_form': user_form,
                    }
                    LOG.debug('Email has changed: %s', debug_data)
                    send_re_actvation_email(request, user)
                    #  user_form.fields['is_active'] = False
                    user.is_active = False
                    user.save()
                    messages.success(
                        request,
                        'Your email has already changed. Now you have to re-activate your account. Please check your e-mail for an activation message.',
                    )
                    # TODO: Use specific template
                    return redirect('django_registration_complete')
                messages.success(request, 'Your profile is updated successfully')
                if success:
                    return redirect('profile')
        else:
            user_form = UpdateUserForm(instance=user)
            profile, created = Profile.objects.get_or_create(user=user)
            profile_form = UpdateProfileForm(instance=profile)
        LOG.debug('debug profile_form: %s', profile_form)
        context = {
            'user_form': user_form,
            'profile_form': profile_form,
        }
        return render(request, 'dds_registration/profile_edit.html.django', context)
    except Exception as err:
        sError = errorToString(err, show_stacktrace=False)
        sTraceback = str(traceback.format_exc())
        debug_data = {
            'err': err,
            'traceback': sTraceback,
        }
        LOG.error('Caught error %s (re-raising): %s', sError, debug_data)
        raise err
