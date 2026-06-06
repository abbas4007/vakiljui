import pytest
from home.tests.factories import CityFactory, SpecialtyFactory

pytestmark = pytest.mark.django_db


def test_city():
    city = CityFactory()
    assert str(city) is not None


def test_specialty():
    spec = SpecialtyFactory()
    assert str(spec) is not None