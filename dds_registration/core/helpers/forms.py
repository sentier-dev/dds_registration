import logging

from django.forms import ModelForm
from django.contrib import messages
from django.http import HttpRequest

from .utils import capitalize_id


__all__ = [
    "pass_form_errors_to_messages",
]


LOG = logging.getLogger(__name__)


def pass_form_errors_to_messages(request: HttpRequest, form: ModelForm):
    # TODO: Process (join, sort out?) dubplicated errors?
    errors = form.errors
    error_items = errors.items()
    if len(error_items):
        # TODO: Show errors?
        # Data example: {'name': ['This field is required.'], 'email': ['This field is required.']}
        LOG.error("Form has errors")
        # Pass messages to the client...
        for error, texts in error_items:
            msg = capitalize_id(error) + ": " + " ".join(texts)
            messages.error(request, msg)
