import json

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from .models import ClickEvent, ShortURL


class URLShortenerTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = get_user_model().objects.create_user(
            username="link-owner",
            email="owner@example.com",
            password="Secure-test-password-93",
        )

    def test_guest_can_create_short_url(self):
        response = self.client.post(
            reverse("shortener:shorten"),
            {"url": "https://example.com/a/long/page"},
        )

        short_url = ShortURL.objects.get()
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            reverse("shortener:created", args=[short_url.short_code]),
        )
        self.assertIsNone(short_url.user)
        self.assertEqual(len(short_url.short_code), 7)

    def test_invalid_scheme_is_rejected(self):
        response = self.client.post(
            reverse("shortener:shorten"),
            {"url": "javascript:alert(1)"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(ShortURL.objects.exists())

    def test_redirect_tracks_click_and_returns_to_destination(self):
        short_url = ShortURL.create(original_url="https://example.com/article", user=self.user)

        response = self.client.get(reverse("shortener:redirect", args=[short_url.short_code]))

        short_url.refresh_from_db()
        self.assertRedirects(response, "https://example.com/article", fetch_redirect_response=False)
        self.assertEqual(short_url.clicks, 1)
        self.assertEqual(ClickEvent.objects.filter(short_url=short_url).count(), 1)

    def test_qr_route_returns_png(self):
        short_url = ShortURL.create(original_url="https://example.com", user=self.user)

        response = self.client.get(reverse("shortener:qr_code", args=[short_url.short_code]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/png")
        self.assertTrue(response.content.startswith(b"\x89PNG\r\n\x1a\n"))

    def test_authenticated_dashboard_shows_owned_links(self):
        self.client.force_login(self.user)
        short_url = ShortURL.create(original_url="https://example.com", user=self.user)

        response = self.client.get(reverse("shortener:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, short_url.short_code)
        self.assertContains(response, "Click activity")

    def test_api_create_and_list_are_scoped_to_authenticated_user(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("shortener:api_urls"),
            data=json.dumps({"url": "https://example.com/api"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        payload = response.json()
        self.assertEqual(payload["url"], "https://example.com/api")
        self.assertTrue(payload["short_url"].endswith(f"/{payload['short_code']}/"))

        listing = self.client.get(reverse("shortener:api_urls"))
        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.json()["count"], 1)
        self.assertEqual(listing.json()["results"][0]["short_code"], payload["short_code"])

        other_user = get_user_model().objects.create_user(
            username="another-owner",
            email="another@example.com",
            password="Secure-test-password-93",
        )
        self.client.force_login(other_user)
        detail = self.client.get(
            reverse("shortener:api_url_detail", args=[payload["short_code"]])
        )
        self.assertEqual(detail.status_code, 404)

    def test_api_rejects_malformed_json(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("shortener:api_urls"),
            data="{not json",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())

    def test_api_requires_authentication(self):
        response = self.client.get(reverse("shortener:api_urls"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response.url)

    def test_dashboard_redirects_anonymous_visitors_to_login(self):
        response = self.client.get(reverse("shortener:dashboard"))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('shortener:dashboard')}",
        )

    def test_failed_login_shows_concise_error(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.user.username, "password": "incorrect-password"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "We couldn't sign you in.")
        self.assertNotContains(response, "Note that both fields may be case-sensitive")

    def test_login_accepts_case_insensitive_username(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.user.username.upper(), "password": "Secure-test-password-93"},
        )

        self.assertRedirects(response, reverse("shortener:dashboard"))

    def test_login_accepts_case_insensitive_email(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.user.email.upper(), "password": "Secure-test-password-93"},
        )

        self.assertRedirects(response, reverse("shortener:dashboard"))

    def test_login_still_checks_password_case(self):
        response = self.client.post(
            reverse("login"),
            {"username": self.user.username, "password": "secure-test-password-93"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "We couldn't sign you in.")

    def test_registration_creates_active_account_without_signing_user_in(self):
        response = self.client.post(
            reverse("shortener:register"),
            {
                "username": "new-linker",
                "email": "new@example.com",
                "password1": "Unique-test-password-731",
                "password2": "Unique-test-password-731",
            },
        )

        user = get_user_model().objects.get(username="new-linker")
        self.assertTrue(user.is_active)
        self.assertRedirects(response, reverse("login"))
        self.assertNotIn("_auth_user_id", self.client.session)

        login_response = self.client.post(
            reverse("login"),
            {"username": user.email, "password": "Unique-test-password-731"},
        )
        self.assertRedirects(login_response, reverse("shortener:dashboard"))
        self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)

    def test_guest_shortening_is_rate_limited(self):
        for _ in range(10):
            response = self.client.post(
                reverse("shortener:shorten"),
                {"url": "https://example.com"},
                REMOTE_ADDR="203.0.113.14",
            )
            self.assertEqual(response.status_code, 302)

        limited_response = self.client.post(
            reverse("shortener:shorten"),
            {"url": "https://example.com"},
            REMOTE_ADDR="203.0.113.14",
        )

        self.assertEqual(limited_response.status_code, 429)
