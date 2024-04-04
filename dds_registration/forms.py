from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.forms.models import ModelForm

from django_registration.forms import RegistrationForm as BaseRegistrationForm

from .models import (
    Event,
    RegistrationOption,
    User,
    Invoice,
)

# A text field to use in those TextField's which don't require large texts, but can use one-line text inputs
textInputWidget = forms.TextInput(attrs={"class": "vLargeTextField"})
textAreaWidget = forms.Textarea(attrs={"class": "vLargeTextField", "rows": 5})


class BillingInvoiceForm(ModelForm):

    class Meta:
        model = Invoice
        fields = [
            "name",
            "address",
            "payment_method",
            "extra_invoice_text",
        ]
        labels = {
            "extra_invoice_text": "Extra invoice text details, like reference or purchase order numbers",
        }
        help_texts = {
            "name": "In case it needs to be different on the invoice or receipt.",
            "address": "In case it needs to be different on the invoice or receipt.",
        }
        widgets = {
            # Issue #71: Make payment method control inline, add option
            # icons. To clarify: Add 'highlighting'? Change names to
            # 'Credit Card' or 'Invoice'? Probably it'll be neccesary to
            # redefine widget class.
            "payment_method": forms.RadioSelect(attrs={"class": "form-control form-check-inline"}),
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
            "extra_invoice_text": forms.Textarea(attrs={"class": "form-control", "rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].required = True
        self.fields["address"].required = True


class BillingEventForm(BillingInvoiceForm):
    pass


class BillingMembershipForm(BillingInvoiceForm):
    pass


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


class InvoiceAdminForm(ModelForm):
    class Meta:
        model = Invoice
        widgets = {
            "name": textInputWidget,
            "address": textAreaWidget,
            "data": textAreaWidget,
            "extra_invoice_text": textAreaWidget,
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


# Issue #63: Temporarily unused
#  class DiscountCodeAdminForm(ModelForm):
#      class Meta:
#          model = DiscountCode
#          widgets = {
#              "code": textInputWidget,
#          }
#          fields = "__all__"
