from ...core.constants.payments import site_supported_currencies


def get_stripe_amount_for_currency(amount: int, currency: str, convert_basic_unit: bool = True) -> int:
    """Stripe fees vary by country.

    Note: Assumes amount in stripe basic unit!!!"""
    if convert_basic_unit:
        amount = get_stripe_basic_unit(amount=amount, currency=currency)
    # NOTE: Must match the list of currencies in `site_supported_currencies`
    if currency == "USD":
        # Stripe fee is 2.9%, currency conversion loss is 1%
        return round(30 + (1 + 0.029 + 0.01) * amount)
    elif currency == "CHF":
        # Stripe fee is 2.9%, currency conversion loss is 1%
        return round(30 + (1 + 0.029 + 0.01) * amount)
    elif currency == "EUR":
        # Stripe fee is 1.5%
        return round(25 + (1 + 0.015) * amount)
    elif currency == "CAD":
        # Stripe fee is 2.9%, currency conversion loss is 1%
        return round(30 + (1 + 0.029 + 0.01) * amount)
    else:
        raise ValueError(f"Unrecognized currency {currency}")


def get_stripe_basic_unit(amount: float, currency: str) -> int:
    """Stripe wants numbers in lower divisible unit.

    This varies by country."""
    currency_ids = dict(site_supported_currencies).keys()
    if currency in currency_ids:
        return round(amount * 100)
    else:
        raise ValueError(f"Unrecognized currency {currency}")


def convert_from_stripe_units(amount: float, currency: str) -> float:
    currency_ids = dict(site_supported_currencies).keys()
    if currency in currency_ids:
        return round(amount / 100, 2)
    else:
        raise ValueError(f"Unrecognized currency {currency}")
