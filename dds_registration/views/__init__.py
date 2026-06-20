# @module dds_registration/views/__init__.py
# @changed 2024.03.15, 19:53


from .root import components_demo, index, profile
from .sso_gateway import SubdomainLoginView, dashboard_auth
from .system import RobotsView, page403, page404, page500
from .team_calendar import team_calendar
from .user import edit_user_profile  # SignUpView,
from .user_registration import DdsRegistrationView
