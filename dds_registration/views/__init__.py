# @module dds_registration/views/__init__.py
# @changed 2024.03.15, 19:53


from .root import (
    index,
    profile,
    components_demo,
)

from .event_registration import (
    event_registration_new,
    event_registration_edit,
    event_registration_new_success,
    event_registration_edit_success,
    event_registration_invoice,
    event_registration_payment,
)

from .user import (
    # SignUpView,
    edit_user_profile,
)

from .system import (
    RobotsView,
    page403,
    page404,
    page500,
)
