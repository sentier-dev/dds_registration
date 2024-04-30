import stripe
from django.conf import settings

# Initalize stripe api
stripe.api_key = settings.STRIPE_SECRET_KEY  # 'sk_...'


# Project version properties
__version__ = "1.0.10"
__timestamp__ = "2024.04.30 15:01 +0200"
__timetag__ = "240430-1501"


__all__ = (
    __version__,
    __timestamp__,
    __timetag__,
)
