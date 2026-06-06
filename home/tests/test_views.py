from django.test import TestCase
from django.urls import reverse

class HomeViewsTest(TestCase):

    def test_home_page(self):
        res = self.client.get(reverse("home:index"))
        self.assertEqual(res.status_code, 200)