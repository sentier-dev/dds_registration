from django.contrib import messages
from django.forms import ModelForm
from django.http import HttpRequest
from loguru import logger

from .utils import capitalize_id

__all__ = [
    "pass_form_errors_to_messages",
]


def pass_form_errors_to_messages(request: HttpRequest, form: ModelForm):
    # TODO: Process (join, sort out?) dubplicated errors?
    errors = form.errors
    error_items = errors.items()
    if len(error_items):
        # TODO: Show errors?
        # Data example: {'name': ['This field is required.'], 'email': ['This field is required.']}
        logger.debug("Form has errors")
        # Pass messages to the client...
        for error, texts in error_items:
            msg = capitalize_id(error) + ": " + " ".join(texts)
            messages.error(request, msg)
