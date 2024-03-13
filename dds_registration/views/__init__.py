# @module dds_registration/views/__init__.py
# @changed 2024.03.13, 16:09


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
)

from .system import (
    RobotsView,
    page403,
    page404,
    page500,
)
