# @module dds_registration/urls/event.py
# @changed 2024.04.02, 00:30

from django.urls import path

from ..views import event_registration as event_registration_views


urlpatterns = [
    path(
        "event/<str:event_code>/registration",
        event_registration_views.event_registration,
        name="event_registration",
    ),
    # path(
    #     "event/<str:event_code>/registration/cancel",
    #     event_registration_views.event_registration_cancel_confirm,
    #     name="event_registration_cancel",
    # ),
    # path(
    #     "event/<str:event_code>/registration/cancel/process",
    #     event_registration_views.event_registration_cancel_process,
    #     name="event_registration_cancel_process",
    # ),
    # path(
    #     "event/<str:event_code>/registration/payment",
    #     event_registration_views.event_registration_payment,
    #     name="event_registration_payment",
    # ),
]
