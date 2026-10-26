from datetime import date, timedelta
from unittest import mock

import pytest
from django.urls import reverse

from dds_registration.forms import MembershipForm
from dds_registration.models import Membership, OrganizationType


def form_data(**overrides):
    data = {
        "name": "Ada Lovelace",
        "address": "Zurich",
        "extra": "",
        "membership_type": "NORMAL",
        "payment_method": "INVOICE",
        "mailing_list": "on",
        "organization": "ETH",
        "organization_type": "UNIVERSITY",
    }
    data.update(overrides)
    return data


def test_organization_is_required():
    form = MembershipForm(form_data(organization=""))
    assert not form.is_valid()
    assert "organization" in form.errors


def test_organization_type_is_required():
    form = MembershipForm(form_data(organization_type=""))
    assert not form.is_valid()
    assert "organization_type" in form.errors


@pytest.fixture
def user(django_user_model):
    return django_user_model.objects.create_user(
        username="ada@example.com", email="ada@example.com", password="x", first_name="Ada", last_name="Lovelace"
    )


@pytest.mark.django_db
@mock.patch("dds_registration.models.Payment.email_invoice")
def test_new_member_gets_one_year_and_organization_stored(_invoice, client, user):
    client.force_login(user)
    response = client.post(reverse("membership_application"), form_data())
    assert response.status_code == 302
    membership = Membership.objects.get(user=user)
    assert membership.started == date.today()
    assert membership.until == date.today().replace(year=date.today().year + 1)
    assert membership.organization == "ETH"
    assert membership.organization_type == OrganizationType.UNIVERSITY
    assert membership.payment.data["until"] == membership.until.isoformat()
    assert membership.payment.data["membership"]["organization"] == "ETH"


@pytest.mark.django_db
def test_active_member_outside_window_is_refused(client, user):
    Membership.objects.create(user=user, until=date.today() + timedelta(days=200))
    client.force_login(user)
    response = client.get(reverse("membership_application"))
    assert response.status_code == 302
    assert response["Location"] == reverse("profile")


@pytest.mark.django_db
@mock.patch("dds_registration.models.Payment.email_invoice")
def test_active_member_inside_window_renews_from_current_end(_invoice, client, user):
    current_until = date.today() + timedelta(days=30)
    Membership.objects.create(user=user, until=current_until, started=date(2024, 5, 5))
    client.force_login(user)
    response = client.post(reverse("membership_application"), form_data())
    assert response.status_code == 302
    membership = Membership.objects.get(user=user)
    assert membership.until == current_until.replace(year=current_until.year + 1)
    assert membership.started == date(2024, 5, 5)


@pytest.mark.django_db
def test_form_prefilled_from_existing_membership(client, user):
    Membership.objects.create(
        user=user, until=date.today() - timedelta(days=1), organization="ETH", organization_type="UNIVERSITY"
    )
    client.force_login(user)
    response = client.get(reverse("membership_application"))
    assert response.status_code == 200
    assert response.context["form"].initial["organization"] == "ETH"
