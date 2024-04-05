import stripe

from ...money import get_stripe_amount_for_currency


def get_stripe_client_secret(
    currency: str,
    price: float,
    email: str,
    optional_metadata: dict = {},
):
    stripe_amount = get_stripe_amount_for_currency(amount=price, currency=currency)

    # TODO: Probably it'd be better to use old approach: to start payment and to fetch the secret via async ajax request: this operation requires a noticeable time (up to 1-2 seconds required to open the page)
    # @see https://docs.stripe.com/api/metadata
    # @see https://docs.stripe.com/api/payment_intents/create
    intent = stripe.PaymentIntent.create(
        amount=stripe_amount,
        currency=currency,
        metadata=optional_metadata,
        # @see: https://docs.stripe.com/api/payment_intents/confirm#confirm_payment_intent-receipt_email
        receipt_email=email,
    )
    return intent
