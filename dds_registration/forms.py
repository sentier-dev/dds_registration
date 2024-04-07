from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.forms.models import ModelForm
from django_registration.forms import RegistrationForm as BaseRegistrationForm

from .models import MEMBERSHIP_DATA, Event, Payment, RegistrationOption, User

# A text field to use in those TextField's which don't require large texts, but can use one-line text inputs
textInputWidget = forms.TextInput(attrs={"class": "vLargeTextField"})
textAreaWidget = forms.Textarea(attrs={"class": "vLargeTextField", "rows": 5})


class MembershipForm(forms.Form):
    name = forms.CharField(
        label="Name on invoice",
        max_length=100,
        widget=textInputWidget,
        help_text="In case it needs to be different on the invoice or receipt.",
        required=True,
    )
    address = forms.CharField(label="Address on invoice", widget=textAreaWidget, required=True)
    extra = forms.CharField(
        label="Extra invoice text details, like reference or purchase order numbers",
        widget=textAreaWidget,
        required=False,
    )
    membership_type = forms.ChoiceField(
        choices=MEMBERSHIP_DATA.public_choice_field_with_prices,
        widget=forms.RadioSelect,
        required=True,
        label="Membership type",
    )
    payment_method = forms.ChoiceField(
        choices=Payment.METHODS, required=True, widget=forms.RadioSelect, label="Payment method"
    )
    mailing_list = forms.BooleanField(
        initial=True, label="Send me the DdS newsletter, and emails about DdS events, courses, and online seminars"
    )


class RegistrationForm(forms.Form):
    option = forms.ChoiceField(
        choices=[],
        widget=forms.RadioSelect,
        required=True,
        label="Registration option",
    )
    send_update_emails = forms.BooleanField(label="Send me emails about this event", required=False, initial=True)
    name = forms.CharField(
        label="Name on invoice",
        max_length=100,
        widget=textInputWidget,
        help_text="In case it needs to be different on the invoice or receipt.",
        required=True,
    )
    address = forms.CharField(label="Address on invoice", widget=textAreaWidget, required=True)
    extra = forms.CharField(
        label="Extra invoice text details, like reference or purchase order numbers",
        widget=textAreaWidget,
        required=False,
    )
    payment_method = forms.ChoiceField(
        choices=Payment.METHODS,
        required=True,
        widget=forms.RadioSelect,
        label="Payment method",
        help_text="Choose something even if the event is free",
    )

    def __init__(self, option_choices, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["option"].choices = option_choices


class DdsRegistrationForm(BaseRegistrationForm):

    # @see https://django-registration.readthedocs.io/en/3.4/custom-user.html

    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 5}),
    )

    class Meta:
        model = User
        fields = [
            #  'username',
            "email",
            "password1",
            "password2",
            "first_name",
            "last_name",
            "address",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-control"}),
            "last_name": forms.TextInput(attrs={"class": "form-control"}),
            #  'username' : forms.HiddenInput(),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "password1": forms.PasswordInput(attrs={"class": "form-control"}),
            "password2": forms.PasswordInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True


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
            "description": textAreaWidget,
            "payment_details": textAreaWidget,
        }
        fields = "__all__"


class PaymentAdminForm(ModelForm):
    class Meta:
        model = Payment
        widgets = {
            "name": textInputWidget,
            "address": textAreaWidget,
            "data": textAreaWidget,
        }
        fields = "__all__"


class UserAdminForm(ModelForm):
    class Meta:
        model = User
        widgets = {
            "first_name": textInputWidget,
            "last_name": textInputWidget,
            "address": textAreaWidget,
        }
        fields = "__all__"


class SignUpForm(UserCreationForm):
    class Meta:
        model = get_user_model()
        fields = (
            # 'username',
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
        )


class UpdateUserForm(forms.ModelForm):
    email = forms.EmailField(required=True, widget=forms.TextInput(attrs={"class": "form-control"}))
    #  is_active = forms.CharField(widget=forms.HiddenInput(), required=False)  # ???

    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 5}),
    )

    class Meta:
        model = User
        fields = [
            #  'username',
            "email",  # Needs re-activation
            "first_name",
            "last_name",
            "address",
            #  'is_active',  # ???
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
