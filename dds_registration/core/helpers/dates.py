from datetime import date

from ..membership.validity import add_one_year


def this_year():
    return date.today().year


def next_year():
    return this_year() + 1


def one_year_from_today():
    return add_one_year(date.today())


def end_of_this_year():
    return date(this_year(), 12, 31)
