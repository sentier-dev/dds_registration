"""Pure date rules for DdS membership validity and renewal.

A membership runs for one year from its start. Renewing while still active
extends from the current end date; renewing after a lapse restarts from today.
"""

from datetime import date, timedelta


def add_one_year(day: date) -> date:
    """Same calendar date next year; Feb 29 becomes Feb 28."""
    try:
        return day.replace(year=day.year + 1)
    except ValueError:
        return day.replace(year=day.year + 1, day=28)


def renewal_until(current_until: date | None, today: date) -> date:
    """End date after a renewal submitted on ``today``."""
    if current_until is None or current_until < today:
        return add_one_year(today)
    return add_one_year(current_until)


def within_renewal_window(current_until: date | None, today: date, window_days: int) -> bool:
    """True when a member may renew: no membership, lapsed, or ending within ``window_days``."""
    if current_until is None:
        return True
    return current_until - today <= timedelta(days=window_days)


def until_label(value) -> str:
    """ISO date for an ``until`` value stored as date, ISO string, or legacy year int."""
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, int):
        return date(value, 12, 31).isoformat()
    return str(value)
