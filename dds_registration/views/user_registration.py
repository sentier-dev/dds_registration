# @module dds_registration/views/registration.py
# @changed 2024.03.22, 19:20

import logging

from django_registration.backends.activation.views import (
    RegistrationView as BackendRegistrationView,
)

from ..forms import DdsRegistrationForm

LOG = logging.getLogger(__name__)


class DdsRegistrationView(BackendRegistrationView):
    form_class = DdsRegistrationForm

    def get_form_class(self):
        """Return the form class to use."""
        return self.form_class

    def get_form(self, form_class=None):
        form_class = DdsRegistrationForm
        return form_class(**self.get_form_kwargs())


__all__ = [
    DdsRegistrationView,
]
