from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.forms.models import ModelForm

from .models import DiscountCode, Event, Profile, RegistrationOption

# A text field to use in those TextField's which don't require large texts, but can use one-line text inputs
textInputWidget = forms.TextInput(attrs={"class": "vLargeTextField"})


class RegistrationOptionAdminForm(ModelForm):
    class Meta:
        model = RegistrationOption
        widgets = {
            "item": textInputWidget,
        }
        fields = "__all__"


class EventAdminForm(ModelForm):
    class Meta:
        model = Event
        widgets = {
            "code": textInputWidget,
            "title": textInputWidget,
            "currency": textInputWidget,
        }
        fields = "__all__"


class DiscountCodeAdminForm(ModelForm):
    class Meta:
        model = DiscountCode
        widgets = {
            "code": textInputWidget,
        }
        fields = "__all__"


class SignUpForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )


class UpdateUserForm(forms.ModelForm):
    email = forms.EmailField(
        required=True, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    is_active = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = User
        fields = [
            #  'username',
            "email",  # Needs re-activation
            "first_name",
            "last_name",
            "is_active",
        ]


class UpdateProfileForm(forms.ModelForm):
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 5}),
    )

    class Meta:
        model = Profile
        fields = [
            "address",
        ]
