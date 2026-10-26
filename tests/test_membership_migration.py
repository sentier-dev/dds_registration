"""The data-migration helpers are plain functions in the migration module."""

import importlib
from datetime import date

import pytest
from django.contrib.auth import get_user_model

from dds_registration.models import Membership, MembershipReminder, OrganizationType, RegistrationOption

migration = importlib.import_module("dds_registration.migrations.0025_membership_dates_and_organization")


def test_until_year_to_date_is_end_of_year():
    assert migration.year_to_until(2026) == date(2026, 12, 31)


def test_started_from_paid_date_when_present():
    assert migration.started_from({"paid_date": "2025-03-14"}, 2025) == date(2025, 3, 14)


def test_year_zero_or_none_falls_back_to_current_year():
    # production has a RegistrationOption with membership_end_year = 0
    assert migration.year_to_until(0) == date(date.today().year, 12, 31)
    assert migration.year_to_until(None) == date(date.today().year, 12, 31)
    assert migration.started_from({"paid_date": "garbage"}, 0) == date(date.today().year, 1, 1)


def test_started_from_ignores_renewal_paid_in_a_later_year():
    # membership.payment points at the latest (renewal) payment, not the first one
    assert migration.started_from({"paid_date": "2025-03-14"}, 2024) == date(2024, 1, 1)


def test_started_from_falls_back_to_jan_1():
    assert migration.started_from({}, 2024) == date(2024, 1, 1)
    assert migration.started_from(None, 2024) == date(2024, 1, 1)


@pytest.mark.django_db
def test_membership_fields_are_dates_and_organization_defaults_blank():
    user = get_user_model().objects.create_user(username="m@example.com", email="m@example.com", password="x")
    membership = Membership.objects.create(user=user)
    assert membership.started == date.today()
    assert membership.until > membership.started
    assert membership.organization == ""
    assert membership.organization_type == ""
    assert membership.needs_details is True
    membership.organization = "ETH"
    membership.organization_type = OrganizationType.UNIVERSITY
    assert membership.needs_details is False


@pytest.mark.django_db
def test_membership_active_compares_dates():
    user = get_user_model().objects.create_user(username="a@example.com", email="a@example.com", password="x")
    membership = Membership.objects.create(user=user, until=date.today())
    assert membership.active is True
    membership.until = date.today().replace(year=date.today().year - 1)
    assert membership.active is False


@pytest.mark.django_db
def test_reminder_log_is_unique_per_membership_until_stage():
    from django.db import IntegrityError

    user = get_user_model().objects.create_user(username="r@example.com", email="r@example.com", password="x")
    membership = Membership.objects.create(user=user)
    MembershipReminder.objects.create(membership=membership, until=membership.until, stage="expiry")
    with pytest.raises(IntegrityError):
        MembershipReminder.objects.create(membership=membership, until=membership.until, stage="expiry")


def test_registration_option_membership_until_default_is_end_of_year():
    option = RegistrationOption()
    assert option.membership_until == date(date.today().year, 12, 31)
