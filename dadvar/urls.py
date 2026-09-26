from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from home.sitemaps import LawyerSitemap, StaticSitemap, LandingPageSitemap, LawyerListSitemap

sitemaps = {
    'lawyers': LawyerSitemap,
    'landing_pages': LandingPageSitemap,  # مهم‌ترین صفحات SEO - قبلاً نبود!
    'lawyer_lists': LawyerListSitemap,
    'static': StaticSitemap,
}


def robots_txt(request):
    """
    robots.txt داینامیک - قبلاً TemplateView بود و URL سایت‌مپ رندر نمیشد
    """
    scheme = 'https' if request.is_secure() else 'http'
    host = request.get_host()
    sitemap_url = f"{scheme}://{host}/sitemap.xml"
    llms_url = f"{scheme}://{host}/llms.txt"

    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        "# مسدودسازی پنل ادمین برای ربات‌ها",
        "Disallow: /admin/",
        "Disallow: /accounts/login/",
        "Disallow: /accounts/signup/",
        "Disallow: /ckeditor/",
        "Disallow: /media/uploads/",
        "Disallow: /payment-verify/",
        "",
        "# اجازه دسترسی به فایل‌های مهم",
        "Allow: /static/",
        "Allow: /media/lawyers/",
        "",
        "# سایت‌مپ",
        f"Sitemap: {sitemap_url}",
        "",
        "# فایل راهنمای هوش مصنوعی",
        f"# LLMs: {llms_url}",
        "",
        "# تنظیمات خاص موتورهای جستجو",
        "User-agent: Googlebot",
        "Crawl-delay: 1",
        "",
        "User-agent: bingbot",
        "Crawl-delay: 2",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),

    # robots.txt داینامیک (قبلاً TemplateView بود و داده رندر نمیشد)
    path('robots.txt', robots_txt, name='robots_txt'),

    path('accounts/', include('accounts.urls')),
    path('', include('home.urls')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
