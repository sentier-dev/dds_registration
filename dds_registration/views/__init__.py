# @module dds_registration/views/__init__.py
# @changed 2024.03.15, 19:53


from .registration import DdsRegistrationView
from .event_registration import (
    event_registration_edit,
    event_registration_edit_success,
    event_registration_invoice,
    event_registration_new,
    event_registration_new_success,
    event_registration_payment,
    event_registration_cancel_confirm,
    event_registration_cancel_process,
)
from .root import components_demo, index, profile
from .system import RobotsView, page403, page404, page500
from .user import edit_user_profile  # SignUpView,
