from django.apps import AppConfig


class RegConfig(AppConfig):
    name = 'dds_registration'
    verbose_name = "DdS Registration and Events"

    def ready(self):
        from django.conf import settings
        from djf_surveys.app_settings import SURVEY_FIELD_VALIDATORS
        import stripe

        stripe.api_key = settings.STRIPE_SECRET_KEY

        SURVEY_FIELD_VALIDATORS["min_length"]["text_area"] = 3
