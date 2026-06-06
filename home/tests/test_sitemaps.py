from django.test import TestCase
from django.urls import reverse

class SitemapTest(TestCase):

    def test_sitemap_loads(self):
        res = self.client.get("/sitemap.xml")
        self.assertEqual(res.status_code, 200)