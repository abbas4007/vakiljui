from django.test import TestCase
from django.urls import reverse

class AccountsViewsTest(TestCase):

    def test_signup_page(self):
        res = self.client.get(reverse("accounts:signup"))
        self.assertEqual(res.status_code, 200)

    def test_login_page(self):
        res = self.client.get(reverse("accounts:login"))
        self.assertEqual(res.status_code, 200)