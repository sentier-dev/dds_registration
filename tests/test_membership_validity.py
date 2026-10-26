from datetime import date

import pytest

from dds_registration.core.membership.validity import (
    add_one_year,
    renewal_until,
    until_label,
    within_renewal_window,
)


def test_add_one_year_same_calendar_date():
    assert add_one_year(date(2026, 10, 26)) == date(2027, 10, 26)


def test_add_one_year_feb_29_maps_to_feb_28():
    assert add_one_year(date(2028, 2, 29)) == date(2029, 2, 28)


def test_renewal_until_new_member_runs_one_year_from_today():
    assert renewal_until(None, today=date(2026, 10, 26)) == date(2027, 10, 26)


def test_renewal_until_lapsed_member_restarts_from_today():
    assert renewal_until(date(2026, 1, 31), today=date(2026, 10, 26)) == date(2027, 10, 26)


def test_renewal_until_active_member_extends_from_current_end():
    assert renewal_until(date(2026, 12, 31), today=date(2026, 11, 15)) == date(2027, 12, 31)


def test_renewal_until_on_last_valid_day_extends_from_current_end():
    assert renewal_until(date(2026, 12, 31), today=date(2026, 12, 31)) == date(2027, 12, 31)


@pytest.mark.parametrize(
    "until,today,expected",
    [
        (date(2026, 12, 31), date(2026, 11, 1), True),  # exactly 60 days before
        (date(2026, 12, 31), date(2026, 10, 31), False),  # 61 days before
        (date(2026, 12, 31), date(2027, 3, 1), True),  # lapsed is always allowed
        (None, date(2026, 10, 26), True),  # no membership yet
    ],
)
def test_within_renewal_window(until, today, expected):
    assert within_renewal_window(until, today=today, window_days=60) is expected


def test_until_label_accepts_legacy_year_and_date_string():
    assert until_label(2026) == "2026-12-31"
    assert until_label("2027-03-04") == "2027-03-04"
    assert until_label(date(2027, 3, 4)) == "2027-03-04"
