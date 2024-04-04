def get_stripe_amount_for_currency(amount: int, currency: str) -> int:
    """Stripe fees vary by country.

    Note: Assumes amount in stripe basic unit!!!"""
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
    if currency in ("CAD", "CHF", "EUR", "CAD"):
        return amount * 100
    else:
        raise ValueError(f"Unrecognized currency {currency}")
