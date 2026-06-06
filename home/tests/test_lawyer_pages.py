from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

User = get_user_model()

class LawyerPagesTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="lawyer1",
            password="12345",
            is_lawyer=True,
            slug="lawyer1"
        )

    def test_lawyer_detail_page(self):
        res = self.client.get(
            reverse("home:lawyer_detail", args=[self.user.slug])
        )
        self.assertEqual(res.status_code, 200)