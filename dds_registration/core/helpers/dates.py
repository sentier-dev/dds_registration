from datetime import date


def this_year():
    return date.today().year


def next_year():
    return this_year() + 1
