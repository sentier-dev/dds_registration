from datetime import date
from unittest import mock

import pytest
from django.contrib.auth import get_user_model

from dds_registration.models import Membership, Payment


def make_user(email="p@example.com"):
    return get_user_model().objects.create_user(username=email, email=email, password="x")


def event_payment(user, **membership_keys):
    data = {
        "kind": "event",
        "user": {"id": user.id, "name": "P", "address": ""},
        "event": {"id": 1, "title": "Spring School"},
        "option": {"item": "Ticket"},
        "price": 100,
        "currency": "EUR",
        "method": "INVOICE",
        "includes_membership": True,
    }
    data.update(membership_keys)
    return Payment.objects.create(status="ISSUED", data=data)


@pytest.mark.django_db
@mock.patch("dds_registration.models.Payment.email_receipt")
def test_mark_paid_creates_membership_from_new_date_key(_receipt):
    user = make_user()
    event_payment(user, membership_until="2027-06-30").mark_paid()
    assert Membership.objects.get(user=user).until == date(2027, 6, 30)


@pytest.mark.django_db
@mock.patch("dds_registration.models.Payment.email_receipt")
def test_mark_paid_accepts_legacy_year_key(_receipt):
    user = make_user()
    event_payment(user, membership_end_year=2027).mark_paid()
    assert Membership.objects.get(user=user).until == date(2027, 12, 31)


@pytest.mark.django_db
@mock.patch("dds_registration.models.Payment.email_receipt")
def test_mark_paid_never_shortens_an_existing_membership(_receipt):
    user = make_user()
    Membership.objects.create(user=user, until=date(2028, 1, 1))
    event_payment(user, membership_until="2027-06-30").mark_paid()
    assert Membership.objects.get(user=user).until == date(2028, 1, 1)
