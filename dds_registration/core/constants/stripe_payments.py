from django.conf import settings


# Stripe link for academic membership
academic_membership_stripe_payment_link = "https://buy.stripe.com/aEU5nr3Al3oVe9a4gg"

# Stripe link for regular membership
regular_membership_stripe_payment_link = "https://buy.stripe.com/6oEeY17QBbVraWY5kl"


if settings.DEV:
    # NOTE: Temporarily use demo payment link for lilliputten's stripe account:
    demo_payment_link = "https://buy.stripe.com/test_6oE03lcbQgUpeJidQQ"
    academic_membership_stripe_payment_link = demo_payment_link
    regular_membership_stripe_payment_link = demo_payment_link


__all__ = [
    academic_membership_stripe_payment_link,
    regular_membership_stripe_payment_link,
]
