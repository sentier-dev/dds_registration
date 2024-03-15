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

#  from django_registration import RegistrationView as BaseCoreRegistrationView
from django_registration.views import RegistrationView as BaseRegistrationView


from ..forms import SignUpForm

from functools import reduce
import traceback
import logging


LOG = logging.getLogger(__name__)


class RegistrationView(BaseRegistrationView):
    form_class = SignUpForm
