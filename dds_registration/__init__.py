import stripe
from django.conf import settings


# Initalize stripe api
stripe.api_key = settings.STRIPE_SECRET_KEY  # 'sk_...'


# Project version properties
__version__ = "0.0.15"
__timestamp__ = "2024.04.05 17:53 +0700"
__timetag__ = "240405-1753"


__all__ = (
    __version__,
    __timestamp__,
    __timetag__,
)
