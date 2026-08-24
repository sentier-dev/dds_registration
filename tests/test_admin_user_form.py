import pytest
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from dds_registration.forms import UserAdminForm


def test_password_field_is_readonly_hash_field():
    field = UserAdminForm.base_fields["password"]
    assert isinstance(field, ReadOnlyPasswordHashField)


@pytest.mark.django_db
def test_admin_form_ignores_submitted_password_value():
    User = get_user_model()
    user = User.objects.create_user(
        username="bo@example.com",
        email="bo@example.com",
        password="original-password",
    )
    original_hash = user.password
    form = UserAdminForm(data={"password": "!Temporal2026"}, instance=user)
    assert form["password"].value() == original_hash
