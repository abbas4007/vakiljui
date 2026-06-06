import pytest
from django.core.cache import cache
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_cache(client):
    cache.clear()
    response = client.get(reverse("home:index"))
    assert response.status_code == 200