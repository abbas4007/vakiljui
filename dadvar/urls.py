from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from home.sitemaps import LawyerSitemap, StaticSitemap, LandingPageSitemap, LawyerListSitemap,LawyerListCitySitemap

sitemaps = {
    'lawyers' : LawyerSitemap,
    'landing_pages' : LandingPageSitemap,
    'lawyer_lists' : LawyerListSitemap,
    "lawyer_lists_city" : LawyerListCitySitemap,
    'static' : StaticSitemap,
}


def robots_txt(request) :
    scheme = "https"
    host = request.get_host()
    sitemap_url = f"{scheme}://{host}/sitemap.xml"
    llms_url = f"{scheme}://{host}/llms.txt"

    lines = [
        "User-agent: *",
        "Allow: /",
        "",
        "Disallow: /admin/",
        "Disallow: /accounts/login/",
        "Disallow: /accounts/signup/",
        "Disallow: /ckeditor/",
        "Disallow: /media/uploads/",
        "Disallow: /payment-verify/",
        "",
        "Allow: /static/",
        "Allow: /media/lawyers/",
        "",
        f"Sitemap: {sitemap_url}",
        "",
        f"# LLMs: {llms_url}",
        "",
        "User-agent: Googlebot",
        "Crawl-delay: 1",
        "",
        "User-agent: bingbot",
        "Crawl-delay: 2",
    ]
    return HttpResponse("\n".join(lines), content_type = "text/plain; charset=utf-8")


urlpatterns = [
                  path('admin/', admin.site.urls, name = 'admin'),
                  path('sitemap.xml', sitemap, {'sitemaps' : sitemaps}, name = 'sitemap'),
                  path('robots.txt', robots_txt, name = 'robots_txt'),

                  path('accounts/', include('accounts.urls')),

                  path('', include('home.urls')),
                  path('ckeditor/', include('ckeditor_uploader.urls')),
              ] + static(settings.MEDIA_URL, document_root = settings.MEDIA_ROOT)
