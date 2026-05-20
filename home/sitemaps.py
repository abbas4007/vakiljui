from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import LawyerProfile, City, Specialty, LandingPageContent


class LawyerSitemap(Sitemap) :
    changefreq = "weekly"
    priority = 0.9

    def items(self) :
        return LawyerProfile.objects.filter(is_active = True).select_related('user')

    def location(self, obj) :
        return obj.get_absolute_url()

    def lastmod(self, obj) :
        return obj.updated_at


class LandingPageSitemap(Sitemap) :
    """
    صفحات لندینگ /بهترین-وکیل/تخصص/شهر/
    مهم‌ترین صفحات SEO - اولویت ۱
    """
    changefreq = "daily"
    priority = 1.0

    def items(self) :
        # روش اول: استفاده از مدل LandingPageContent (اگه داری)
        if LandingPageContent.objects.exists() :
            return LandingPageContent.objects.filter(is_active = True)

        # روش دوم: تولید خودکار از روی City و Specialty
        items = []
        cities = City.objects.filter(is_active = True)
        specialties = Specialty.objects.filter(is_active = True)
        for city in cities :
            for specialty in specialties :
                items.append({
                    'speciality' : specialty.slug,
                    'city' : city.slug,
                })
        return items

    def location(self, item) :
        # اگه از مدل LandingPageContent استفاده می‌کنی
        if hasattr(item, 'speciality') :
            return reverse('home:seo_landing', kwargs = {
                'speciality' : item.speciality,
                'city' : item.city
            })
        # اگه از دیکشنری استفاده می‌کنی
        return reverse('home:seo_landing', kwargs = {
            'speciality' : item['speciality'],
            'city' : item['city']
        })

    def lastmod(self, item) :
        if hasattr(item, 'updated_at') :
            return item.updated_at
        return None


class LawyerListSitemap(Sitemap) :
    """صفحات لیست وکلا بر اساس تخصص - اولویت ۰.۸"""
    changefreq = "daily"
    priority = 0.8

    def items(self) :
        return Specialty.objects.filter(is_active = True)

    def location(self, obj) :
        return reverse('home:lawyer_list', kwargs = {'speciality' : obj.slug})


class LawyerListCitySitemap(Sitemap) :
    """صفحات لیست وکلا بر اساس تخصص + شهر - اولویت ۰.۷"""
    changefreq = "daily"
    priority = 0.7

    def items(self) :
        items = []
        cities = City.objects.filter(is_active = True)
        specialties = Specialty.objects.filter(is_active = True)
        for city in cities :
            for specialty in specialties :
                items.append({
                    'speciality' : specialty.slug,
                    'city' : city.slug,
                })
        return items

    def location(self, item) :
        return reverse('home:lawyer_list_city', kwargs = {
            'speciality' : item['speciality'],
            'city' : item['city']
        })


class StaticSitemap(Sitemap) :
    """فقط صفحات مهم استاتیک (بدون صفحات لاگین و ثبت‌نام)"""
    priority = 0.5
    changefreq = "monthly"

    def items(self) :
        # حذف accounts:login و accounts:signup
        return [
            'home:index',
            'home:subscription_plans',
        ]

    def location(self, item) :
        return reverse(item)