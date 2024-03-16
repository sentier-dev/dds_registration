from django.urls import path

from .views import SignUpView


urlpatterns = [
    # UNUSED?
    path('signup/', SignUpView.as_view(), name='signup'),
]
