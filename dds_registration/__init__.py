import stripe
from django.conf import settings

# Initalize stripe api
stripe.api_key = settings.STRIPE_SECRET_KEY  # 'sk_...'


# Project version properties
__version__ = "1.0.9"
__timestamp__ = "2024.04.08 13:55 +0700"
__timetag__ = "240408-1355"


__all__ = (
    __version__,
    __timestamp__,
    __timetag__,
)
