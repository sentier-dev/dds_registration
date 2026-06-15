"""Access-control tests for the private team calendar view."""

from django.contrib.auth import get_user_model
from django.test import TestCase
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
