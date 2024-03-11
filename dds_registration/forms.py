from django.forms.models import ModelForm
from django import forms

from .models import (
    Event,
    RegistrationOption,
    DiscountCode,
)


# A text field to use in those TextField's which don't require large texts, but can use one-line text inputs
textInputWidget = forms.TextInput(attrs={'class': 'vLargeTextField'})


class RegistrationOptionAdminForm(ModelForm):
    class Meta:
        model = RegistrationOption
        widgets = {
            'item': textInputWidget,
        }
        fields = '__all__'


class EventAdminForm(ModelForm):
    class Meta:
        model = Event
        widgets = {
            'code': textInputWidget,
            'title': textInputWidget,
            'currency': textInputWidget,
        }
        fields = '__all__'


class DiscountCodeAdminForm(ModelForm):
    class Meta:
        model = DiscountCode
        widgets = {
            'code': textInputWidget,
        }
        fields = '__all__'
