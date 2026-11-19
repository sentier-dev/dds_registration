"""Access-control tests for the private team calendar view."""

import tempfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


class TeamCalendarAccessTests(TestCase):
    def test_anonymous_is_redirected_to_login(self):
        response = self.client.get(reverse("team_calendar"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response["Location"])

    def test_authenticated_user_gets_the_page(self):
        user = get_user_model().objects.create_user(
            username="caluser",
            email="caluser@example.com",
            password="pw-test-12345",
        )
        self.client.force_login(user)
        response = self.client.get(reverse("team_calendar"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"DdS Team Calendar", response.content)


class TeamCalendarSourceTests(TestCase):
    """The calendar file is deployed separately from the app release."""

    def setUp(self):
        user = get_user_model().objects.create_user(
            username="caluser2",
            email="caluser2@example.com",
            password="pw-test-12345",
        )
        self.client.force_login(user)

    def test_serves_the_file_named_by_the_setting(self):
        with tempfile.TemporaryDirectory() as folder:
            calendar = Path(folder) / "index.html"
            calendar.write_text("<html><title>deployed calendar</title></html>", encoding="utf-8")
            with override_settings(TEAM_CALENDAR_PATH=str(calendar)):
                response = self.client.get(reverse("team_calendar"))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"deployed calendar", response.content)

    def test_missing_file_answers_503_not_500(self):
        with tempfile.TemporaryDirectory() as folder:
            missing = Path(folder) / "index.html"
            with override_settings(TEAM_CALENDAR_PATH=str(missing)):
                with self.assertLogs("dds_registration.views.team_calendar", level="ERROR") as logs:
                    response = self.client.get(reverse("team_calendar"))
        self.assertEqual(response.status_code, 503)
        self.assertIn(b"not available", response.content)
        self.assertIn(str(missing), logs.output[0])

    def test_page_is_sandboxed_from_the_events_origin(self):
        response = self.client.get(reverse("team_calendar"))
        policy = response["Content-Security-Policy"]
        self.assertTrue(policy.startswith("sandbox "))
        self.assertIn("allow-scripts", policy)
        self.assertNotIn("allow-same-origin", policy)

    def test_bundled_fallback_holds_no_member_data(self):
        bundled = Path(settings.BASE_DIR) / "dds_registration" / "team_calendar" / "index.html"
        text = bundled.read_text(encoding="utf-8")
        self.assertNotIn("annualDays", text)
        self.assertNotIn("@", text)
