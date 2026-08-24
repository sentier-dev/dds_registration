import pytest
from django.contrib.auth import authenticate, get_user_model


def make_user(email, password="correct-horse"):
    return get_user_model().objects.create_user(username=email, email=email, password=password)


@pytest.mark.django_db
def test_login_email_is_case_insensitive():
    make_user("bo@example.com")
    user = authenticate(None, username="Bo@Example.COM", password="correct-horse")
    assert user is not None
    assert user.email == "bo@example.com"


@pytest.mark.django_db
def test_mixed_case_stored_email_accepts_lowercase_login():
    make_user("Jane.Doe@example.com")
    user = authenticate(None, username="jane.doe@example.com", password="correct-horse")
    assert user is not None
    assert user.email == "Jane.Doe@example.com"


@pytest.mark.django_db
def test_wrong_password_still_rejected():
    make_user("bo@example.com")
    assert authenticate(None, username="Bo@Example.com", password="wrong") is None


@pytest.mark.django_db
def test_unknown_email_rejected():
    assert authenticate(None, username="nobody@example.com", password="whatever") is None


@pytest.mark.django_db
def test_case_duplicate_accounts_fall_back_to_exact_match():
    # The unique constraint on email is case-sensitive, so case-variant
    # duplicates can exist; each must still log into its own account.
    make_user("bo@example.com", password="lower-pass")
    make_user("BO@example.com", password="upper-pass")
    user = authenticate(None, username="bo@example.com", password="lower-pass")
    assert user is not None and user.email == "bo@example.com"
    user = authenticate(None, username="BO@example.com", password="upper-pass")
    assert user is not None and user.email == "BO@example.com"
