# @module dds_registration/views/event_registration.py
# @changed 2024.03.13, 16:09

from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import render, redirect


import traceback
import logging


from ..models import (
    Event,
)

from .helpers import (
    event_registration_form,
    show_registration_form_success,
)


LOG = logging.getLogger(__name__)


@login_required
def event_registration_new(request: HttpRequest, event_code: str):
    return event_registration_form(
        request,
        event_code=event_code,
        form_template='dds_registration/event_registration_new.html.django',
        success_redirect='event_registration_new_success',
        create_new=True,
    )


@login_required
def event_registration_edit(request: HttpRequest, event_code: str):
    return event_registration_form(
        request,
        event_code=event_code,
        form_template='dds_registration/event_registration_edit.html.django',
        success_redirect='event_registration_edit_success',
    )


@login_required
def event_registration_new_success(request: HttpRequest, event_code: str):
    return show_registration_form_success(
        request, event_code=event_code, template='dds_registration/event_registration_new_success.html.django'
    )


@login_required
def event_registration_edit_success(request: HttpRequest, event_code: str):
    return show_registration_form_success(
        request, event_code=event_code, template='dds_registration/event_registration_edit_success.html.django'
    )


__all__ = [
    event_registration_new,
    event_registration_edit,
    event_registration_new_success,
    event_registration_edit_success,
]
