from datetime import date

import pytest
from django.urls import reverse

from dds_registration.models import Membership


@pytest.fixture
def member(django_user_model):
    user = django_user_model.objects.create_user(username="m@example.com", email="m@example.com", password="x")
    Membership.objects.create(user=user, until=date.today())  # inside the renewal window
    return user


@pytest.mark.django_db
def test_member_without_details_is_redirected_from_profile(client, member):
    client.force_login(member)
    response = client.get(reverse("profile"))
    assert response.status_code == 302
    assert response["Location"] == reverse("membership_details")


@pytest.mark.django_db
def test_details_page_itself_and_apply_page_are_reachable(client, member):
    client.force_login(member)
    assert client.get(reverse("membership_details")).status_code == 200
    assert client.get(reverse("membership_application")).status_code == 200


@pytest.mark.django_db
def test_sso_gateway_is_never_redirected(client, member):
    client.force_login(member)
    response = client.get(reverse("dashboard_auth", args=["somekey"]))
    assert response.status_code in (200, 403)


@pytest.mark.django_db
def test_user_without_membership_is_not_redirected(client, django_user_model):
    user = django_user_model.objects.create_user(username="n@example.com", email="n@example.com", password="x")
    client.force_login(user)
    assert client.get(reverse("profile")).status_code == 200


@pytest.mark.django_db
def test_staff_is_not_redirected(client, django_user_model):
    staff = django_user_model.objects.create_user(
        username="s@example.com", email="s@example.com", password="x", is_staff=True
    )
    Membership.objects.create(user=staff)
    client.force_login(staff)
    assert client.get(reverse("profile")).status_code == 200


@pytest.mark.django_db
def test_posting_details_clears_the_redirect(client, member):
    client.force_login(member)
    response = client.post(reverse("membership_details"), {"organization": "ETH", "organization_type": "UNIVERSITY"})
    assert response.status_code == 302
    assert response["Location"] == reverse("profile")
    assert Membership.objects.get(user=member).organization == "ETH"
    assert client.get(reverse("profile")).status_code == 200


@pytest.mark.django_db
def test_profile_links_to_details_when_filled(client, member):
    Membership.objects.filter(user=member).update(organization="ETH", organization_type="UNIVERSITY")
    client.force_login(member)
    body = client.get(reverse("profile")).content.decode()
    assert "ETH" in body and reverse("membership_details") in body
