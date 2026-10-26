from datetime import date
from io import BytesIO

import pandas as pd
import pytest
from django.urls import reverse

from dds_registration.models import Membership, OrganizationType


@pytest.fixture
def admin_client(client, django_user_model):
    admin = django_user_model.objects.create_superuser(
        username="adm@example.com", email="adm@example.com", password="x"
    )
    client.force_login(admin)
    return client


@pytest.fixture
def members(django_user_model):
    out = []
    for first, last, org in [("Ada", "Lovelace", "ETH"), ("Bo", "Weidema", "2.-0 LCA")]:
        user = django_user_model.objects.create_user(
            username=f"{first}@example.com",
            email=f"{first}@example.com",
            password="x",
            first_name=first,
            last_name=last,
        )
        out.append(
            Membership.objects.create(
                user=user,
                organization=org,
                organization_type=OrganizationType.UNIVERSITY if first == "Ada" else OrganizationType.CONSULTANCY,
                started=date(2025, 3, 1),
                until=date(2026, 12, 31),
            )
        )
    return out


CHANGELIST = "admin:dds_registration_membership_changelist"


@pytest.mark.django_db
def test_changelist_shows_names_and_organization(admin_client, members):
    body = admin_client.get(reverse(CHANGELIST)).content.decode()
    for text in [
        "Lovelace",
        "Ada",
        "ETH",
        "University",
        "Weidema",
        "2.-0 LCA",
        "Consultancy",
        "2025-03-01",
        "2026-12-31",
    ]:
        assert text in body


@pytest.mark.django_db
def test_changelist_sorts_by_last_name(admin_client, members):
    body = admin_client.get(reverse(CHANGELIST) + "?o=-2").content.decode()
    assert body.index("Weidema") < body.index("Lovelace")


@pytest.mark.django_db
def test_search_by_organization(admin_client, members):
    body = admin_client.get(reverse(CHANGELIST) + "?q=ETH").content.decode()
    assert "Lovelace" in body and "Weidema" not in body


@pytest.mark.django_db
def test_export_contains_new_columns(admin_client, members):
    response = admin_client.post(
        reverse(CHANGELIST),
        {"action": "export_current_member_list", "_selected_action": [m.pk for m in members]},
    )
    df = pd.read_excel(BytesIO(response.content))
    assert list(df.columns) == [
        "email",
        "id",
        "first_name",
        "last_name",
        "organization",
        "organization_type",
        "started",
        "until",
        "on_mailing_list",
        "type",
    ]
    assert set(df["organization"]) == {"ETH", "2.-0 LCA"}
