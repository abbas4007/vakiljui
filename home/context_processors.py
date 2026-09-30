from django.core.cache import cache
from .models import Specialty


def nav_specialties(request) :
    specialties = cache.get('active_specialties')
    if not specialties :
        specialties = list(Specialty.objects.filter(is_active = True))
        cache.set('active_specialties', specialties, 3600)
    return {'nav_specialties' : specialties}
