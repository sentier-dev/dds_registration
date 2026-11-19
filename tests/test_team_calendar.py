"""Access-control tests for the private team calendar view."""

import tempfile
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

BUNDLED = Path(settings.BASE_DIR) / "dds_registration" / "team_calendar" / "index.html"


@override_settings(TEAM_CALENDAR_PATH=str(BUNDLED))
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

    def assert_sandboxed(self, response):
        policy = response["Content-Security-Policy"]
        self.assertTrue(policy.startswith("sandbox "))
        self.assertIn("allow-scripts", policy)
        self.assertNotIn("allow-same-origin", policy)

    def test_page_is_sandboxed_from_the_events_origin(self):
        with override_settings(TEAM_CALENDAR_PATH=str(BUNDLED)):
            self.assert_sandboxed(self.client.get(reverse("team_calendar")))

    def test_unavailable_page_is_sandboxed_too(self):
        with override_settings(TEAM_CALENDAR_PATH="/nonexistent/index.html"):
            with self.assertLogs("dds_registration.views.team_calendar", level="ERROR"):
                response = self.client.get(reverse("team_calendar"))
        self.assertEqual(response.status_code, 503)
        self.assert_sandboxed(response)

    def test_file_is_served_byte_for_byte_in_production_mode(self):
        page = "<html><script>\nconst a = '<!-- kept -->';\n  if (1 < 2) { run(); }\n</script></html>\n"
        with tempfile.TemporaryDirectory() as folder:
            calendar = Path(folder) / "index.html"
            calendar.write_text(page, encoding="utf-8")
            with override_settings(TEAM_CALENDAR_PATH=str(calendar), DEV=False):
                response = self.client.get(reverse("team_calendar"))
        self.assertEqual(response.content.decode("utf-8"), page)

    def test_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as folder:
            secret = Path(folder) / "secret.txt"
            secret.write_text("SECRET_KEY=abc", encoding="utf-8")
            link = Path(folder) / "index.html"
            link.symlink_to(secret)
            with override_settings(TEAM_CALENDAR_PATH=str(link)):
                with self.assertLogs("dds_registration.views.team_calendar", level="ERROR"):
                    response = self.client.get(reverse("team_calendar"))
        self.assertEqual(response.status_code, 503)
        self.assertNotIn(b"SECRET_KEY", response.content)

    def test_empty_file_answers_503(self):
        with tempfile.TemporaryDirectory() as folder:
            calendar = Path(folder) / "index.html"
            calendar.write_text("  \n", encoding="utf-8")
            with override_settings(TEAM_CALENDAR_PATH=str(calendar)):
                with self.assertLogs("dds_registration.views.team_calendar", level="ERROR"):
                    response = self.client.get(reverse("team_calendar"))
        self.assertEqual(response.status_code, 503)

    def test_bundled_fallback_holds_no_member_data(self):
        text = BUNDLED.read_text(encoding="utf-8")
        self.assertNotIn("annualDays", text)
        self.assertNotIn("@", text)
