from django.contrib import messages
from django.views.generic import TemplateView, View
from django.http import HttpResponse, JsonResponse
from .ai_matcher import analyze_legal_query, AIMatcherError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import requests
from django.conf import settings
from .models import (
    LawyerProfile, City, Specialty, LandingPageContent, SubscriptionPlan, LawyerSubscription,
    ConsultationSetting, ConsultationRequest, ConsultationMessage, LawyerPayout,
    Article,
)
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
import json
from django.views.generic import ListView, DetailView
from django.db.models import Q, Max, F


from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator


@method_decorator(ensure_csrf_cookie, name='dispatch')
class HomeView(TemplateView):
    template_name = 'home/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        # ============ شهرها ============
        cities = cache.get('active_cities')
        if not cities:
            cities = list(City.objects.filter(is_active=True))
            cache.set('active_cities', cities, 3600)

        # ============ تخصص‌ها ============
        specialties = cache.get('active_specialties')
        if not specialties:
            specialties = list(Specialty.objects.filter(is_active=True))
            cache.set('active_specialties', specialties, 3600)

        # تعداد واقعی وکلا در هر شهر
        for city in cities:
            real_count = LawyerProfile.objects.filter(is_active=True, city=city.name).count()
            city.real_lawyer_count = real_count if real_count > 0 else city.lawyer_count

        ctx['cities'] = cities
        ctx['specialties'] = specialties

        # ============ وکلای طلایی ============
        top_lawyers = cache.get('top_lawyers')

        if top_lawyers is None:
            try:
                gold_plan = SubscriptionPlan.objects.get(
                    Q(name__icontains='طلا') | Q(name__iexact='gold'),
                    is_active=True
                )
            except SubscriptionPlan.DoesNotExist:
                gold_plan = SubscriptionPlan.objects.filter(
                    is_active=True
                ).order_by('-priority').first()

            if gold_plan:
                top_lawyers = list(LawyerProfile.objects.filter(
                    is_active=True,
                    subscriptions__plan=gold_plan,
                    subscriptions__is_paid=True,
                    subscriptions__end_date__gt=timezone.now()
                ).select_related('user').distinct().order_by(
                    '-subscriptions__start_date'
                )[:8])

                if not top_lawyers:
                    top_lawyers = list(LawyerProfile.objects.filter(
                        is_active=True,
                        subscriptions__is_paid=True,
                        subscriptions__end_date__gt=timezone.now()
                    ).select_related('user').distinct().order_by(
                        '-subscriptions__plan__priority',
                        '-subscriptions__start_date'
                    )[:8])
            else:
                top_lawyers = list(LawyerProfile.objects.filter(
                    is_active=True
                ).select_related('user').order_by('-success_rate')[:8])

            cache.set('top_lawyers', top_lawyers, 300)

        ctx['top_lawyers'] = top_lawyers

        # ============ متا تگ‌ها ============
        ctx['meta_title'] = getattr(settings, 'DEFAULT_META_TITLE', 'وکیل جو | سامانه تخصصی وکلای ایران')
        ctx['meta_description'] = getattr(settings, 'DEFAULT_META_DESCRIPTION', 'بهترین وکلای ایران را پیدا کنید')
        ctx['canonical_url'] = self.request.build_absolute_uri('/')
        ctx['og_image'] = self.request.build_absolute_uri('/static/img/back.jfif')

        # ============ Schema برای صفحه اصلی ============
        ctx['site_schema'] = json.dumps({
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "وکیل جو",
            "url": self.request.build_absolute_uri('/'),
            "description": ctx['meta_description'],
            "potentialAction": {
                "@type": "SearchAction",
                "target": {
                    "@type": "EntryPoint",
                    "urlTemplate": self.request.build_absolute_uri('/') + "جستجو?q={search_term_string}"
                },
                "query-input": "required name=search_term_string"
            }
        }, ensure_ascii=False)

        # ============ پردازش پارامتر q برای سئو ============
        query = self.request.GET.get('q', '').strip()
        if query:
            valid_specialty_names = [s.name for s in specialties]
            valid_city_names = [c.name for c in cities]

            try:
                result = analyze_legal_query(query, valid_specialty_names, valid_city_names)
                ctx['initial_ai_query'] = query
                ctx['initial_ai_result'] = result
                ctx['panel_should_open'] = True

                # برای ریچ‌اسنیپت گوگل، یک FAQPage با سوال و جواب تولید می‌کنیم
                if result.get('summary'):
                    ctx['faq_schema_for_seo'] = json.dumps({
                        "@context": "https://schema.org",
                        "@type": "FAQPage",
                        "mainEntity": [{
                            "@type": "Question",
                            "name": query,
                            "acceptedAnswer": {
                                "@type": "Answer",
                                "text": result['summary']
                            }
                        }]
                    }, ensure_ascii=False)
                # کانونیکال رو به صفحه اصلی بدون پارامتر تنظیم می‌کنیم تا محتوای تکراری نداشته باشیم
                ctx['canonical_url'] = self.request.build_absolute_uri('/')

            except AIMatcherError:
                # در صورت خطا، پنل باز نمی‌شه
                ctx['panel_should_open'] = False
                ctx['initial_ai_result'] = None
        else:
            ctx['panel_should_open'] = False
            ctx['initial_ai_result'] = None

        return ctx


class LawyerListView(ListView) :
    model = LawyerProfile
    template_name = 'home/lawyer_list.html'
    paginate_by = 20
    context_object_name = 'lawyers'

    def get_queryset(self) :
        qs = LawyerProfile.objects.filter(is_active = True).select_related('user')

        speciality = self.kwargs.get('speciality', '')
        city = self.kwargs.get('city', '')

        if speciality and speciality != 'همه' :
            speciality_clean = speciality.replace('-', ' ')
            # استفاده از iexact برای تطابق دقیق (به جای icontains)
            qs = qs.filter(speciality__iexact = speciality_clean)

        if city :
            city_clean = city.replace('-', ' ')
            qs = qs.filter(city__iexact = city_clean)

        return qs.order_by('-success_rate', '-years_of_experience')

    def get_context_data(self, **kwargs) :
        ctx = super().get_context_data(**kwargs)

        speciality = self.kwargs.get('speciality', '')
        city = self.kwargs.get('city', '')

        speciality_clean = speciality.replace('-', ' ') if speciality else ''
        city_clean = city.replace('-', ' ') if city else ''

        ctx['speciality'] = speciality_clean
        ctx['city'] = city_clean

        # H1 برای سئو
        if speciality_clean and city_clean :
            ctx['h1_title'] = f'بهترین وکلای {speciality_clean} در {city_clean}'
            ctx['meta_title'] = f'بهترین وکلای {speciality_clean} در {city_clean} | وکیل جو'
            ctx[
                'meta_description'] = f'لیست بهترین وکلای متخصص {speciality_clean} در {city_clean} به همراه رزومه، نرخ موفقیت و نظرات کاربران'
        elif speciality_clean :
            ctx['h1_title'] = f'بهترین وکلای {speciality_clean}'
            ctx['meta_title'] = f'بهترین وکلای {speciality_clean} | وکیل جو'
            ctx['meta_description'] = f'معرفی بهترین وکلای {speciality_clean} با سابقه کاری، نرخ موفقیت و نظرات کاربران'
        else :
            ctx['h1_title'] = 'لیست وکلای متخصص'
            ctx['meta_title'] = 'لیست بهترین وکلای ایران | وکیل جو'
            ctx['meta_description'] = 'لیست بهترین وکلای ایران در تمامی تخصص‌ها و شهرها با رزومه و نرخ موفقیت'

        ctx['canonical_url'] = self.request.build_absolute_uri(self.request.path)

        # ========== Breadcrumb Schema ==========
        breadcrumb_items = [
            {"@type" : "ListItem", "position" : 1, "name" : "خانه", "item" : self.request.build_absolute_uri('/')}
        ]
        if speciality_clean :
            breadcrumb_items.append({
                "@type" : "ListItem",
                "position" : 2,
                "name" : f"وکیل {speciality_clean}",
                "item" : self.request.build_absolute_uri(self.request.path)
            })
        if city_clean :
            breadcrumb_items.append({
                "@type" : "ListItem",
                "position" : 3,
                "name" : city_clean,
                "item" : self.request.build_absolute_uri(self.request.path)
            })

        ctx['breadcrumb_schema'] = json.dumps({
            "@context" : "https://schema.org",
            "@type" : "BreadcrumbList",
            "itemListElement" : breadcrumb_items
        }, ensure_ascii = False)

        # ========== لینک به صفحات لندینگ (Internal Linking) ==========
        if speciality_clean and city_clean :
            ctx['landing_page_url'] = self.request.build_absolute_uri(
                f'/بهترین-وکیل/{speciality_clean.replace(" ", "-")}/{city_clean.replace(" ", "-")}/'
            )

        # شهرها و تخصص‌های مرتبط برای لینک‌دهی داخلی
        ctx['related_cities'] = City.objects.filter(is_active = True).exclude(name = city_clean)[
                                :6] if city_clean else []
        ctx['related_specialties'] = Specialty.objects.filter(is_active = True).exclude(name = speciality_clean)[
                                     :6] if speciality_clean else []

        return ctx


class LawyerDetailView(DetailView) :
    model = LawyerProfile
    template_name = 'home/lawyer_detail.html'
    context_object_name = 'lawyer'
    slug_url_kwarg = 'slug'

    def get_queryset(self) :
        return LawyerProfile.objects.filter(is_active = True).select_related('user')

    def get_context_data(self, **kwargs) :
        ctx = super().get_context_data(**kwargs)
        lawyer = self.object

        full_name = lawyer.user.get_full_name()
        summary = lawyer.ai_summary or f'معرفی وکیل {full_name} متخصص در {lawyer.speciality}، {lawyer.city}، با {lawyer.years_of_experience} سال سابقه و {lawyer.success_rate} درصد موفقیت'

        # ========== متا تگ‌ها ==========
        ctx['meta_title'] = f'{full_name} | بهترین وکیل {lawyer.speciality} در {lawyer.city} | وکیل جو'
        ctx['meta_description'] = summary[:160]
        ctx['canonical_url'] = self.request.build_absolute_uri(lawyer.get_absolute_url())
        ctx['og_image'] = self.request.build_absolute_uri(
            lawyer.profile_image.url) if lawyer.profile_image else self.request.build_absolute_uri(
            '/static/img/back.jfif')

        # ========== وکلا مشابه (برای Internal Linking) ==========
        ctx['similar_lawyers'] = LawyerProfile.objects.filter(
            is_active = True,
            speciality = lawyer.speciality,
            city = lawyer.city
        ).exclude(id = lawyer.id).select_related('user')[:4]

        # ========== Attorney JSON-LD Schema (اصلی) ==========
        attorney_schema = {
            "@context" : "https://schema.org",
            "@type" : "Attorney",
            "name" : full_name,
            "url" : ctx['canonical_url'],
            "description" : summary,
            "specialty" : lawyer.speciality,
            "address" : {
                "@type" : "PostalAddress",
                "addressLocality" : lawyer.city,
                "addressCountry" : "IR"
            },
            "telephone" : lawyer.phone_display or "",
            "yearsInBusiness" : lawyer.years_of_experience,
            "image" : ctx['og_image'],
            "sameAs" : [
                f"https://t.me/share/url?url={ctx['canonical_url']}",
            ],
        }

        # aggregateRating (برای سئوی بهتر)
        if lawyer.success_rate > 0 :
            attorney_schema["aggregateRating"] = {
                "@type" : "AggregateRating",
                "ratingValue" : lawyer.success_rate,
                "bestRating" : "100",
                "worstRating" : "0",
                "ratingCount" : lawyer.rating_count if lawyer.rating_count > 0 else 1,
                "reviewCount" : lawyer.rating_count if lawyer.rating_count > 0 else 1,
            }

        # اضافه کردن geo (برای Local SEO)
        city_coords = {
            'تهران' : {'lat' : 35.6892, 'lng' : 51.3890},
            'مشهد' : {'lat' : 36.2605, 'lng' : 59.6168},
            'اصفهان' : {'lat' : 32.6546, 'lng' : 51.6670},
        }
        if lawyer.city in city_coords :
            attorney_schema["geo"] = {
                "@type" : "GeoCoordinates",
                "latitude" : city_coords[lawyer.city]['lat'],
                "longitude" : city_coords[lawyer.city]['lng']
            }

        # priceRange (برای شفافیت)
        attorney_schema["priceRange"] = "$$$"

        ctx['attorney_schema'] = json.dumps(attorney_schema, ensure_ascii = False)

        # ========== FAQ Schema (برای GEO و سئو) ==========
        if lawyer.faq_data and isinstance(lawyer.faq_data, dict) :
            faq_items = []
            for q, a in lawyer.faq_data.items() :
                if q and a :
                    faq_items.append({
                        "@type" : "Question",
                        "name" : q,
                        "acceptedAnswer" : {
                            "@type" : "Answer",
                            "text" : a
                        }
                    })
            if faq_items :
                ctx['faq_schema'] = json.dumps({
                    "@context" : "https://schema.org",
                    "@type" : "FAQPage",
                    "mainEntity" : faq_items
                }, ensure_ascii = False)

        # ========== Breadcrumb Schema ==========
        ctx['breadcrumb_schema'] = json.dumps({
            "@context" : "https://schema.org",
            "@type" : "BreadcrumbList",
            "itemListElement" : [
                {
                    "@type" : "ListItem",
                    "position" : 1,
                    "name" : "خانه",
                    "item" : self.request.build_absolute_uri('/')
                },
                {
                    "@type" : "ListItem",
                    "position" : 2,
                    "name" : f"وکیل {lawyer.speciality}",
                    "item" : self.request.build_absolute_uri(f'/وکلای-{lawyer.speciality}/')
                },
                {
                    "@type" : "ListItem",
                    "position" : 3,
                    "name" : full_name,
                    "item" : ctx['canonical_url']
                },
            ]
        }, ensure_ascii = False)

        # ========== Organization Schema (برای اعتبار سایت) ==========
        ctx['organization_schema'] = json.dumps({
            "@context" : "https://schema.org",
            "@type" : "Organization",
            "name" : "وکیل جو",
            "url" : self.request.build_absolute_uri('/'),
            "logo" : self.request.build_absolute_uri('/static/img/back.jfif'),
            "sameAs" : [
                "https://t.me/vakiljo",
                "https://instagram.com/vakiljo"
            ]
        }, ensure_ascii = False)

        return ctx


class SeoLandingView(TemplateView) :
    template_name = 'home/seo_landing.html'

    def get_context_data(self, **kwargs) :
        ctx = super().get_context_data(**kwargs)

        # دریافت پارامترها از URL
        speciality = self.kwargs.get('speciality', '').replace('-', ' ')
        city = self.kwargs.get('city', '').replace('-', ' ')

        ctx['speciality'] = speciality
        ctx['city'] = city
        ctx['h1_title'] = f'بهترین وکیل {speciality} در {city}'

        # محتوای اختصاصی که از پنل ادمین (مدل LandingPageContent) وارد شده،
        # اگه برای این ترکیب تخصص/شهر ثبت شده باشه
        landing_content = LandingPageContent.objects.filter(
            speciality = speciality,
            city = city,
            is_active = True
        ).first()

        if speciality and city :
            # وکلای مرتبط
            related_lawyers = LawyerProfile.objects.filter(
                is_active = True,
                speciality__icontains = speciality,
                city__icontains = city
            )[:10]
            ctx['related_lawyers'] = related_lawyers
            ctx['total_lawyers'] = related_lawyers.count()

            # میانگین نرخ موفقیت
            if related_lawyers.exists() :
                avg_rate = sum(l.success_rate for l in related_lawyers) // related_lawyers.count()
                ctx['avg_success_rate'] = avg_rate
            else :
                ctx['avg_success_rate'] = 85

            # ========== لینک‌های داخلی ==========
            # سایر شهرها
            other_cities = City.objects.filter(is_active = True).exclude(name = city)[:8]
            ctx['other_cities'] = other_cities

            # سایر تخصص‌ها
            other_specialties = Specialty.objects.filter(is_active = True).exclude(name = speciality)[:6]
            ctx['other_specialties'] = other_specialties

            # لینک‌های راهنما - به بخش‌های همین صفحه (anchor) لینک می‌دن، نه صفحات جداگانه‌ی ناموجود
            current_path = self.request.path
            ctx['related_guides'] = [
                {'title' : f'مراحل {speciality} در {city}', 'url' : f'{current_path}#main-content'},
                {'title' : f'نکات انتخاب وکیل {speciality}', 'url' : f'{current_path}#tips-content'},
                {'title' : f'سوالات متداول درباره {speciality}', 'url' : f'{current_path}#faq-section'},
            ]

            # لینک به صفحه لیست
            ctx['list_page_url'] = reverse('home:lawyer_list_city', kwargs = {
                'speciality' : speciality.replace(' ', '-'),
                'city' : city.replace(' ', '-')
            })

            # ========== محتوای متنی پیش‌فرض ==========
            ctx['intro_text'] = f"""
            <p>اگر به دنبال <strong>بهترین وکیل {speciality} در {city}</strong> هستید، این صفحه راهنمای کاملی برای شماست.</p>
            <p>در سامانه وکیل جو، {ctx['total_lawyers']} وکیل متخصص در حوزه {speciality} در {city} شناسایی شده‌اند.</p>
            """

            ctx['main_content'] = f"""
            <h2>لیست بهترین وکلای {speciality} در {city}</h2>
            <p>در این صفحه لیست بهترین وکلای {speciality} در {city} را مشاهده می‌کنید. این وکلا بر اساس نرخ موفقیت، سابقه کاری و نظرات کاربران رتبه‌بندی شده‌اند.</p>
            """

            ctx['tips_content'] = f"""
            <h2>راهنمای انتخاب بهترین وکیل {speciality}</h2>
            <ul>
                <li><strong>سابقه کاری:</strong> وکیلی با حداقل ۵ سال سابقه در حوزه {speciality} انتخاب کنید.</li>
                <li><strong>نرخ موفقیت:</strong> آمار پرونده‌های موفق وکیل را بررسی کنید.</li>
                <li><strong>نظرات موکلان:</strong> تجربیات دیگران می‌تواند راهنمای خوبی باشد.</li>
            </ul>
            """

            ctx['faq_list'] = [
                {"question" : f"بهترین وکیل {speciality} در {city} کیست?",
                 "answer" : f"بر اساس رتبه‌بندی وکیل جو، وکلای بالای جدول بهترین گزینه‌ها هستند."},
                {"question" : f"هزینه وکیل {speciality} در {city} چقدر است?",
                 "answer" : f"هزینه وکالت در {city} بسته به عوامل مختلفی متغیر است."},
                {"question" : f"چگونه بهترین وکیل {speciality} را پیدا کنم?",
                 "answer" : f"به سابقه کاری، نرخ موفقیت و نظرات موکلان قبلی توجه کنید."},
            ]

            # ========== LocalBusiness Schema ==========
            city_coords = {
                'تهران' : {'lat' : 35.6892, 'lng' : 51.3890},
                'مشهد' : {'lat' : 36.2605, 'lng' : 59.6168},
                'اصفهان' : {'lat' : 32.6546, 'lng' : 51.6670},
                'شیراز' : {'lat' : 29.5918, 'lng' : 52.5837},
                'تبریز' : {'lat' : 38.0800, 'lng' : 46.2919},
                'کرج' : {'lat' : 35.8400, 'lng' : 50.9391},
            }

            local_business = {
                "@context" : "https://schema.org",
                "@type" : "LegalService",
                "name" : f"بهترین وکیل {speciality} در {city}",
                "url" : self.request.build_absolute_uri(self.request.path),
                "description" : ctx.get('meta_description', f'لیست بهترین وکلای {speciality} در {city}'),
                "address" : {
                    "@type" : "PostalAddress",
                    "addressLocality" : city,
                    "addressCountry" : "IR"
                },
                "areaServed" : {"@type" : "City", "name" : city},
                "serviceType" : speciality,
                "priceRange" : "متوسط ۵۰۰,۰۰۰ - ۳,۰۰۰,۰۰۰ تومان",
                "telephone" : "۰۲۱-۱۲۳۴۵۶۷۸",
            }

            if city in city_coords :
                local_business["geo"] = {
                    "@type" : "GeoCoordinates",
                    "latitude" : city_coords[city]['lat'],
                    "longitude" : city_coords[city]['lng']
                }

            ctx['local_business_schema'] = local_business

            # متا تگ‌ها (پیش‌فرض)
            ctx['meta_title'] = f'بهترین وکیل {speciality} در {city} | وکیل جو'
            ctx[
                'meta_description'] = f'لیست بهترین وکلای {speciality} در {city} به همراه رزومه، نرخ موفقیت و نظرات کاربران'

            # ========== جایگزینی با محتوای واقعیِ ثبت‌شده در ادمین (اگر موجود باشد) ==========
            # هر فیلد فقط زمانی override میشه که واقعاً پر شده باشه؛
            # در غیر این صورت همون محتوای خودکار بالا باقی می‌مونه (fallback)
            if landing_content :
                if landing_content.meta_title :
                    ctx['meta_title'] = landing_content.meta_title
                if landing_content.meta_description :
                    ctx['meta_description'] = landing_content.meta_description
                if landing_content.h1_title :
                    ctx['h1_title'] = landing_content.h1_title
                if landing_content.intro_text :
                    ctx['intro_text'] = landing_content.intro_text
                if landing_content.main_content :
                    ctx['main_content'] = landing_content.main_content
                if landing_content.tips_content :
                    ctx['tips_content'] = landing_content.tips_content
                if landing_content.faq_content :
                    normalized_faq = []
                    for item in landing_content.faq_content :
                        if isinstance(item, dict) :
                            question = item.get('question') or item.get('سوال')
                            answer = item.get('answer') or item.get('پاسخ')
                            if question and answer :
                                normalized_faq.append({'question' : question, 'answer' : answer})
                    if normalized_faq :
                        ctx['faq_list'] = normalized_faq
                if landing_content.total_lawyers :
                    ctx['total_lawyers'] = landing_content.total_lawyers
                if landing_content.avg_success_rate :
                    ctx['avg_success_rate'] = landing_content.avg_success_rate

            ctx['landing_content'] = landing_content

        else :
            ctx['related_lawyers'] = []
            ctx['total_lawyers'] = 0
            ctx['avg_success_rate'] = 0
            ctx['other_cities'] = []
            ctx['other_specialties'] = []
            ctx['related_guides'] = []
            ctx['intro_text'] = ''
            ctx['main_content'] = ''
            ctx['tips_content'] = ''
            ctx['faq_list'] = []
            ctx['meta_title'] = 'بهترین وکیل | وکیل جو'
            ctx['meta_description'] = 'پیدا کردن بهترین وکیل در هر تخصص و شهری'

        ctx['canonical_url'] = self.request.build_absolute_uri(self.request.path)

        # نکته: article_schema اینجا با json.dumps ساخته میشه (قبلاً دیکشنری خام
        # بود که JSON نامعتبر تولید می‌کرد و گوگل نمی‌تونست پارسش کنه - فیکس شد)
        ctx['article_schema'] = json.dumps({
            "@context" : "https://schema.org",
            "@type" : "Article",
            "headline" : ctx['h1_title'],
            "description" : ctx.get('meta_description', ''),
            "url" : self.request.build_absolute_uri(self.request.path),
            "datePublished" : "2025-01-01",
            "dateModified" : timezone.now().isoformat(),
            "author" : {
                "@type" : "Organization",
                "name" : "وکیل جو",
                "url" : self.request.build_absolute_uri('/')
            },
            "publisher" : {
                "@type" : "Organization",
                "name" : "وکیل جو",
                "logo" : {
                    "@type" : "ImageObject",
                    "url" : self.request.build_absolute_uri('/static/img/back.jfif')
                }
            },
            "mainEntityOfPage" : {
                "@type" : "WebPage",
                "@id" : self.request.build_absolute_uri(self.request.path)
            },
            "articleSection" : speciality,
            "articleBody" : ctx.get('main_content', '')[:500]
        }, ensure_ascii = False)

        return ctx


class LLMsTextView(View) :
    def get(self, request) :
        content = self._generate_llms_txt(request)
        return HttpResponse(content, content_type = 'text/plain; charset=utf-8')

    def _generate_llms_txt(self, request) :
        lines = [
            "# وکیل جو - سامانه تخصصی وکلای ایران",
            "## خلاصه",
            "این سایت یک دایرکتوری تخصصی برای معرفی بهترین وکلای ایران است.",
            "",
            "## صفحات اصلی",
            f"- صفحه اصلی: {request.build_absolute_uri('/')}",
            f"- سایت‌مپ: {request.build_absolute_uri('/sitemap.xml')}",
            "",
            "## وکلای ویژه",
        ]
        top_lawyers = LawyerProfile.objects.filter(is_active = True).select_related('user')[:20]
        for lawyer in top_lawyers :
            lines.append(
                f"- {lawyer.user.get_full_name()} | {lawyer.speciality} | {lawyer.city} | {request.build_absolute_uri(lawyer.get_absolute_url())}")
        return "\n".join(lines)


@login_required
def subscribe_view(request, plan_id) :
    plan = get_object_or_404(SubscriptionPlan, id = plan_id, is_active = True)
    try :
        lawyer = LawyerProfile.objects.get(user = request.user)
    except LawyerProfile.DoesNotExist :
        messages.error(request, 'پروفایل وکیل یافت نشد.')
        return redirect('home:index')

    if request.method == 'POST' :
        callback_url = request.build_absolute_uri(reverse('home:payment_verify'))
        data = {
            'merchant_id' : settings.ZARINPAL_MERCHANT_ID,
            'amount' : plan.price,
            'callback_url' : callback_url,
            'description' : f'اشتراک {plan.name} - سامانه وکیل جو',
            'metadata' : {
                'email' : request.user.email,
                'mobile' : request.user.phone
            }
        }
        try :
            response = requests.post(
                'https://sandbox.zarinpal.com/pg/v4/payment/request.json',
                json = data,
                timeout = 10
            )
            if response.status_code == 200 :
                result = response.json()
                if result['data']['code'] == 100 :
                    request.session['payment_plan_id'] = plan.id
                    request.session['payment_amount'] = plan.price
                    return redirect(f'https://sandbox.zarinpal.com/pg/StartPay/{result["data"]["authority"]}')
                else :
                    messages.error(request, f'خطا در اتصال به درگاه: {result["data"]["message"]}')
        except requests.RequestException :
            messages.error(request, 'خطا در اتصال به درگاه پرداخت. لطفاً دوباره تلاش کنید.')

    return render(request, 'home/subscribe.html', {
        'plan' : plan,
        'lawyer' : lawyer,
        'meta_title' : f'خرید اشتراک {plan.name} | وکیل جو',
    })


def payment_verify(request) :
    authority = request.GET.get('Authority')
    status = request.GET.get('Status')
    plan_id = request.session.get('payment_plan_id')

    if not plan_id :
        return render(request, 'home/payment_failed.html', {'message' : 'اطلاعات پرداخت یافت نشد.'})

    plan = get_object_or_404(SubscriptionPlan, id = plan_id)

    if status == 'OK' :
        data = {
            'merchant_id' : settings.ZARINPAL_MERCHANT_ID,
            'amount' : plan.price,
            'authority' : authority,
        }
        try :
            response = requests.post(
                'https://sandbox.zarinpal.com/pg/v4/payment/verify.json',
                json = data,
                timeout = 10
            )
            if response.status_code == 200 :
                result = response.json()
                if result['data']['code'] == 100 :
                    try :
                        lawyer = LawyerProfile.objects.get(user = request.user)
                    except LawyerProfile.DoesNotExist :
                        return render(request, 'home/payment_failed.html', {'message' : 'پروفایل وکیل یافت نشد.'})

                    start_date = timezone.now()
                    end_date = start_date + timedelta(days = plan.duration_days)
                    LawyerSubscription.objects.create(
                        lawyer = lawyer,
                        plan = plan,
                        end_date = end_date,
                        is_paid = True,
                        payment_id = authority
                    )
                    request.session.pop('payment_plan_id', None)
                    return render(request, 'home/payment_success.html', {
                        'plan' : plan,
                        'message' : 'پرداخت با موفقیت انجام شد. اشتراک شما فعال شد.'
                    })
                else :
                    return render(request, 'home/payment_failed.html', {
                        'message' : f'پرداخت ناموفق: {result["data"]["message"]}'
                    })
        except requests.RequestException :
            return render(request, 'home/payment_failed.html', {'message' : 'خطا در تأیید پرداخت.'})

    return render(request, 'home/payment_failed.html', {'message' : 'پرداخت توسط کاربر لغو شد.'})


def subscription_plans(request) :
    plans = SubscriptionPlan.objects.filter(is_active = True).order_by('price')
    return render(request, 'home/subscribe.html', {
        'plans' : plans,
        'meta_title' : 'پلن‌های اشتراک | وکیل جو',
        'meta_description' : 'با خرید اشتراک وکیل جو، در صدر نتایج گوگل دیده شوید و مشتری آنلاین دریافت کنید',
        'canonical_url' : request.build_absolute_uri(request.path),
    })


from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import render, redirect

from accounts.models import User
from .models import LawyerProfile


def lawyer_register(request):
    if request.method == 'POST':

        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '')
        password_confirm = request.POST.get('password_confirm', '')

        full_name = request.POST.get('full_name', '').strip()
        speciality = request.POST.get('speciality', '').strip()
        city = request.POST.get('city', '').strip()
        years_experience = request.POST.get('years_experience', '0').strip()
        phone_display = request.POST.get('phone_display', '').strip()
        description = request.POST.get('description', '').strip()
        ai_summary = request.POST.get('ai_summary', '').strip()
        bar_number = request.POST.get('bar_number', '').strip()
        email = request.POST.get('email', '').strip()

        # -------------------------
        # اعتبارسنجی
        # -------------------------

        if not phone or not password or not password_confirm:
            messages.error(
                request,
                'شماره موبایل، رمز عبور و تکرار رمز عبور الزامی است.'
            )
            return render(request, 'home/lawyer_register.html')

        if password != password_confirm:
            messages.error(
                request,
                'رمز عبور و تکرار آن یکسان نیستند.'
            )
            return render(request, 'home/lawyer_register.html')

        if len(password) < 8:
            messages.error(
                request,
                'رمز عبور باید حداقل ۸ کاراکتر باشد.'
            )
            return render(request, 'home/lawyer_register.html')

        if not full_name:
            messages.error(
                request,
                'نام و نام خانوادگی الزامی است.'
            )
            return render(request, 'home/lawyer_register.html')

        if not bar_number:
            messages.error(
                request,
                'شماره پروانه وکالت الزامی است.'
            )
            return render(request, 'home/lawyer_register.html')

        if User.objects.filter(username=phone).exists():
            messages.error(
                request,
                'این شماره موبایل قبلاً ثبت شده است.'
            )
            return render(request, 'home/lawyer_register.html')

        if User.objects.filter(phone=phone).exists():
            messages.error(
                request,
                'این شماره موبایل قبلاً ثبت شده است.'
            )
            return render(request, 'home/lawyer_register.html')

        # -------------------------
        # نام و نام خانوادگی
        # -------------------------

        name_parts = full_name.split()

        first_name = name_parts[0] if name_parts else ''
        last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

        # -------------------------
        # سال سابقه
        # -------------------------

        try:
            years_experience = int(years_experience or 0)
        except ValueError:
            years_experience = 0

        # -------------------------
        # ساخت User
        # -------------------------

        user = User.objects.create_user(
            username=phone,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            is_lawyer=True
        )

        # -------------------------
        # ساخت LawyerProfile
        # -------------------------

        lawyer_profile = LawyerProfile.objects.create(
            user=user,
            speciality=speciality,
            city=city,
            description=description,
            ai_summary=ai_summary,
            years_of_experience=years_experience,
            phone_display=phone_display,
            bar_number=bar_number,

            # بسیار مهم:
            # تا وقتی ادمین تأیید نکرده، عمومی نباشد
            is_active=False,
        )

        # -------------------------
        # عکس پروفایل
        # -------------------------

        profile_image = request.FILES.get('profile_image')

        if profile_image:
            lawyer_profile.profile_image = profile_image
            lawyer_profile.save()

        # -------------------------
        # ورود خودکار کاربر
        # -------------------------

        login(request, user)

        messages.success(
            request,
            'ثبت‌نام با موفقیت انجام شد. پروفایل شما پس از بررسی شماره پروانه وکالت توسط تیم ما فعال خواهد شد.'
        )

        return redirect('home:index')

    return render(
        request,
        'home/lawyer_register.html',
        {
            'meta_title': 'ثبت‌نام وکیل | دادور',
            'meta_description': 'در سامانه دادور ثبت‌نام کنید و در گوگل دیده شوید',
            'canonical_url': request.build_absolute_uri(request.path),
        }
    )

class LandingPage(View) :

    def get(self, request) :
        return render(request, 'home/landing.html')


class LawyerSearchView(ListView):
    model = LawyerProfile
    template_name = 'home/search_results.html'
    context_object_name = 'lawyers'
    paginate_by = 12

    STOP_WORDS = ['وکیل', 'وکلای', 'مشاور', 'برای']

    def get_query(self):
        return self.request.GET.get('q', '').strip()

    def get_keywords(self):
        query = self.get_query()
        if not query:
            return []
        keywords = [w for w in query.split() if w not in self.STOP_WORDS]
        return keywords if keywords else query.split()

    def build_search_field_query(self, word):
        return (
            Q(user__first_name__icontains=word) |
            Q(user__last_name__icontains=word) |
            Q(speciality__icontains=word) |
            Q(sub_speciality__icontains=word) |
            Q(city__icontains=word)
        )

    def get_queryset(self):
        query = self.get_query()
        base_qs = LawyerProfile.objects.filter(
            is_active=True
        ).select_related('user')

        if not query:
            return LawyerProfile.objects.none()

        keywords = self.get_keywords()

        and_query = Q()
        for word in keywords:
            and_query &= self.build_search_field_query(word)

        results = base_qs.filter(and_query).distinct()

        if not results.exists():
            or_query = Q()
            for word in keywords:
                or_query |= self.build_search_field_query(word)
            results = base_qs.filter(or_query).distinct()

        return results

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.get_query()
        context['results_count'] = context['paginator'].count
        return context


class AIMatchView(View):
    MAX_REQUESTS_PER_HOUR = 8
    SESSION_KEY = 'ai_match_requests'

    def _is_rate_limited(self, request):
        now = timezone.now().timestamp()
        history = request.session.get(self.SESSION_KEY, [])
        history = [t for t in history if now - t < 3600]
        if len(history) >= self.MAX_REQUESTS_PER_HOUR:
            request.session[self.SESSION_KEY] = history
            return True
        history.append(now)
        request.session[self.SESSION_KEY] = history
        return False

    def post(self, request):
        if self._is_rate_limited(request):
            return JsonResponse(
                {'error': 'تعداد درخواست‌های شما در این ساعت به حد مجاز رسیده است. کمی بعد دوباره تلاش کنید.'},
                status=429
            )

        try:
            body = json.loads(request.body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'error': 'درخواست نامعتبر است.'}, status=400)

        description = (body.get('description') or '').strip()
        if not description:
            return JsonResponse({'error': 'لطفاً مشکل خود را توضیح دهید.'}, status=400)
        if len(description) < 10:
            return JsonResponse({'error': 'لطفاً کمی بیشتر توضیح دهید تا بتوانیم بهتر راهنمایی کنیم.'}, status=400)

        cities = cache.get('active_cities')
        if not cities:
            cities = list(City.objects.filter(is_active=True))
            cache.set('active_cities', cities, 3600)

        specialties = cache.get('active_specialties')
        if not specialties:
            specialties = list(Specialty.objects.filter(is_active=True))
            cache.set('active_specialties', specialties, 3600)

        valid_specialty_names = [s.name for s in specialties]
        valid_city_names = [c.name for c in cities]

        try:
            result = analyze_legal_query(description, valid_specialty_names, valid_city_names)
        except AIMatcherError as e:
            return JsonResponse({'error': str(e)}, status=503)

        if not result['specialties']:
            return JsonResponse({
                'summary': result['summary'] or 'متوجه ارتباط توضیح شما با تخصص‌های موجود در سایت نشدیم. لطفاً کمی واضح‌تر توضیح دهید یا مستقیماً از لیست تخصص‌ها انتخاب کنید.',
                'city': result['city'],
                'specialties': [],
                'lawyers': [],
                'ai_powered': result.get('source') == 'ai',
                'primary_url': None,
                'disclaimer': 'این پاسخ توسط هوش مصنوعی تولید شده و جایگزین مشاوره‌ی حقوقی با وکیل واقعی نیست.',
            })

        specialties_data = []
        for sp in result['specialties']:
            sp_slug = sp.replace(' ', '-')
            if result['city']:
                url = reverse('home:lawyer_list_city', kwargs={'speciality': sp_slug, 'city': result['city']})
            else:
                url = reverse('home:lawyer_list', kwargs={'speciality': sp_slug})
            specialties_data.append({'name': sp, 'url': url})

        lawyers_data = []
        if result.get('source') == 'ai':
            specialty_query = Q()
            for sp in result['specialties']:
                specialty_query |= Q(speciality=sp)

            lawyers_qs = LawyerProfile.objects.filter(specialty_query, is_active=True).select_related('user')
            if result['city']:
                lawyers_qs = lawyers_qs.filter(city=result['city'])

            lawyers_qs = lawyers_qs.annotate(
                top_priority=Max(
                    'subscriptions__plan__priority',
                    filter=Q(subscriptions__is_paid=True, subscriptions__end_date__gt=timezone.now())
                )
            ).order_by('-top_priority', '-success_rate')[:6]

            for lawyer in lawyers_qs:
                lawyers_data.append({
                    'name': lawyer.user.get_full_name(),
                    'speciality': lawyer.speciality,
                    'city': lawyer.city,
                    'years_of_experience': lawyer.years_of_experience,
                    'url': lawyer.get_absolute_url(),
                })

        return JsonResponse({
            'summary': result['summary'],
            'city': result['city'],
            'specialties': specialties_data,
            'lawyers': lawyers_data,
            'ai_powered': result.get('source') == 'ai',
            'primary_url': specialties_data[0]['url'] if specialties_data else None,
            'disclaimer': 'این پاسخ توسط هوش مصنوعی تولید شده و جایگزین مشاوره‌ی حقوقی با وکیل واقعی نیست.',
        })


# =========================================================
# سیستم مشاوره‌ی آنلاین پولی
# =========================================================

def consultation_lawyer_list_view(request):
    lawyers_qs = LawyerProfile.objects.filter(
        is_active=True,
        consultation_setting__is_available=True,
    ).select_related('user', 'consultation_setting')

    speciality = request.GET.get('speciality', '').strip()
    city = request.GET.get('city', '').strip()
    if speciality:
        lawyers_qs = lawyers_qs.filter(speciality=speciality)
    if city:
        lawyers_qs = lawyers_qs.filter(city=city)

    lawyers_qs = lawyers_qs.order_by('-success_rate', '-years_of_experience')

    return render(request, 'home/consultation_lawyers.html', {
        'lawyers': lawyers_qs,
        'specialties': Specialty.objects.filter(is_active=True),
        'cities': City.objects.filter(is_active=True),
        'selected_speciality': speciality,
        'selected_city': city,
        'meta_title': 'مشاوره‌ی آنلاین با وکیل | وکیل جو',
        'meta_description': 'مستقیم و آنلاین با وکلای متخصص و تأییدشده مشاوره بگیرید؛ چت متنی یا تماس تلفنی.',
        'canonical_url': request.build_absolute_uri(request.path),
    })


@login_required
def consultation_settings_view(request):
    try:
        lawyer = LawyerProfile.objects.get(user=request.user)
    except LawyerProfile.DoesNotExist:
        messages.error(request, 'این بخش فقط برای وکلا در دسترس است.')
        return redirect('home:index')

    setting, _ = ConsultationSetting.objects.get_or_create(lawyer=lawyer)

    if request.method == 'POST':
        setting.is_available = request.POST.get('is_available') == 'on'
        setting.chat_enabled = request.POST.get('chat_enabled') == 'on'
        setting.chat_price = int(request.POST.get('chat_price') or 0)
        setting.voice_enabled = request.POST.get('voice_enabled') == 'on'
        setting.voice_price = int(request.POST.get('voice_price') or 0)
        setting.session_minutes = int(request.POST.get('session_minutes') or 30)
        setting.save()
        messages.success(request, 'تنظیمات مشاوره با موفقیت ذخیره شد.')
        return redirect('home:consultation_settings')

    return render(request, 'home/consultation_settings.html', {
        'setting': setting,
        'meta_title': 'تنظیمات مشاوره | وکیل جو',
    })


@login_required
def request_consultation_view(request, slug, format):
    lawyer = get_object_or_404(LawyerProfile, slug=slug, is_active=True)

    try:
        setting = lawyer.consultation_setting
    except ConsultationSetting.DoesNotExist:
        messages.error(request, 'این وکیل در حال حاضر مشاوره‌ی آنلاین فعال نکرده است.')
        return redirect(lawyer.get_absolute_url())

    if not setting.is_available:
        messages.error(request, 'این وکیل در حال حاضر آماده‌ی پذیرش مشاوره نیست.')
        return redirect(lawyer.get_absolute_url())

    if format == ConsultationRequest.Format.CHAT:
        if not setting.chat_enabled or setting.chat_price <= 0:
            messages.error(request, 'مشاوره‌ی متنی برای این وکیل فعال نیست.')
            return redirect(lawyer.get_absolute_url())
        price = setting.chat_price
    elif format == ConsultationRequest.Format.VOICE:
        if not setting.voice_enabled or setting.voice_price <= 0:
            messages.error(request, 'مشاوره‌ی تلفنی برای این وکیل فعال نیست.')
            return redirect(lawyer.get_absolute_url())
        price = setting.voice_price
    else:
        messages.error(request, 'فرمت مشاوره نامعتبر است.')
        return redirect(lawyer.get_absolute_url())

    if lawyer.user_id == request.user.id:
        messages.error(request, 'نمی‌توانید برای خودتان درخواست مشاوره ثبت کنید.')
        return redirect(lawyer.get_absolute_url())

    consultation = ConsultationRequest.objects.create(
        user=request.user,
        lawyer=lawyer,
        format=format,
        price=price,
        commission_percent=getattr(settings, 'CONSULTATION_COMMISSION_PERCENT', 20),
        session_minutes=setting.session_minutes,
    )

    callback_url = request.build_absolute_uri(
        reverse('home:consultation_payment_verify', args=[consultation.id])
    )
    data = {
        'merchant_id': settings.ZARINPAL_MERCHANT_ID,
        'amount': price,
        'callback_url': callback_url,
        'description': f'مشاوره‌ی {consultation.get_format_display()} با {lawyer.user.get_full_name()}',
        'metadata': {
            'email': request.user.email,
            'mobile': request.user.phone,
        }
    }
    try:
        response = requests.post(
            'https://sandbox.zarinpal.com/pg/v4/payment/request.json',
            json=data, timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            if result['data']['code'] == 100:
                consultation.payment_authority = result['data']['authority']
                consultation.save(update_fields=['payment_authority'])
                return redirect(f'https://sandbox.zarinpal.com/pg/StartPay/{result["data"]["authority"]}')
            else:
                messages.error(request, f'خطا در اتصال به درگاه: {result["data"]["message"]}')
        else:
            messages.error(request, 'خطا در اتصال به درگاه پرداخت.')
    except requests.RequestException:
        messages.error(request, 'خطا در اتصال به درگاه پرداخت. لطفاً دوباره تلاش کنید.')

    consultation.status = ConsultationRequest.Status.CANCELLED
    consultation.save(update_fields=['status'])
    return redirect(lawyer.get_absolute_url())


@login_required
def consultation_payment_verify(request, pk):
    consultation = get_object_or_404(ConsultationRequest, id=pk, user=request.user)
    authority = request.GET.get('Authority')
    status = request.GET.get('Status')

    if consultation.status != ConsultationRequest.Status.PENDING_PAYMENT:
        if consultation.status == ConsultationRequest.Status.PAID:
            return redirect('home:consultation_room', pk=consultation.id)
        return render(request, 'home/payment_failed.html', {'message': 'این تراکنش قبلاً پردازش شده است.'})

    if status == 'OK':
        data = {
            'merchant_id': settings.ZARINPAL_MERCHANT_ID,
            'amount': consultation.price,
            'authority': authority,
        }
        try:
            response = requests.post(
                'https://sandbox.zarinpal.com/pg/v4/payment/verify.json',
                json=data, timeout=10
            )
            if response.status_code == 200:
                result = response.json()
                if result['data']['code'] == 100:
                    consultation.status = ConsultationRequest.Status.PAID
                    consultation.paid_at = timezone.now()
                    consultation.payment_ref_id = str(result['data'].get('ref_id', ''))
                    consultation.save(update_fields=['status', 'paid_at', 'payment_ref_id'])
                    return redirect('home:consultation_room', pk=consultation.id)
                else:
                    return render(request, 'home/payment_failed.html', {
                        'message': f'پرداخت ناموفق: {result["data"]["message"]}'
                    })
        except requests.RequestException:
            return render(request, 'home/payment_failed.html', {'message': 'خطا در تأیید پرداخت.'})

    consultation.status = ConsultationRequest.Status.CANCELLED
    consultation.save(update_fields=['status'])
    return render(request, 'home/payment_failed.html', {'message': 'پرداخت توسط کاربر لغو شد.'})


def _get_consultation_for_participant(request, pk):
    consultation = get_object_or_404(ConsultationRequest, id=pk)
    is_client = consultation.user_id == request.user.id
    is_lawyer = consultation.lawyer.user_id == request.user.id
    if not (is_client or is_lawyer):
        return None
    return consultation


@login_required
def consultation_room_view(request, pk):
    consultation = _get_consultation_for_participant(request, pk)
    if consultation is None:
        messages.error(request, 'شما به این مشاوره دسترسی ندارید.')
        return redirect('home:index')

    if consultation.status == ConsultationRequest.Status.PENDING_PAYMENT:
        messages.error(request, 'این مشاوره هنوز پرداخت نشده است.')
        return redirect('home:index')

    return render(request, 'home/consultation_room.html', {
        'consultation': consultation,
        'is_lawyer_side': consultation.lawyer.user_id == request.user.id,
        'meta_title': 'اتاق مشاوره | وکیل جو',
        'robots': 'noindex, nofollow',
    })


@login_required
def consultation_send_message(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'روش نامعتبر است.'}, status=405)

    consultation = _get_consultation_for_participant(request, pk)
    if consultation is None:
        return JsonResponse({'error': 'دسترسی ندارید.'}, status=403)

    if consultation.status != ConsultationRequest.Status.PAID:
        return JsonResponse({'error': 'این جلسه فعال نیست.'}, status=400)

    if consultation.is_session_expired:
        return JsonResponse({'error': 'زمان این جلسه‌ی مشاوره به پایان رسیده است.'}, status=400)

    try:
        body = json.loads(request.body.decode('utf-8'))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'error': 'درخواست نامعتبر است.'}, status=400)

    content = (body.get('content') or '').strip()
    if not content:
        return JsonResponse({'error': 'متن پیام نمی‌تواند خالی باشد.'}, status=400)
    if len(content) > 5000:
        content = content[:5000]

    msg = ConsultationMessage.objects.create(
        consultation=consultation, sender=request.user, content=content
    )
    return JsonResponse({
        'id': msg.id,
        'content': msg.content,
        'is_mine': True,
        'created_at': msg.created_at.isoformat(),
    })


@login_required
def consultation_poll_messages(request, pk):
    consultation = _get_consultation_for_participant(request, pk)
    if consultation is None:
        return JsonResponse({'error': 'دسترسی ندارید.'}, status=403)

    after_id = int(request.GET.get('after_id') or 0)
    qs = consultation.messages.filter(id__gt=after_id).select_related('sender')

    return JsonResponse({
        'messages': [
            {
                'id': m.id,
                'content': m.content,
                'is_mine': m.sender_id == request.user.id,
                'sender_name': m.sender.get_full_name() or m.sender.username,
                'created_at': m.created_at.isoformat(),
            } for m in qs
        ],
        'status': consultation.status,
        'is_expired': consultation.is_session_expired,
    })


@login_required
def consultation_complete_view(request, pk):
    if request.method != 'POST':
        return JsonResponse({'error': 'روش نامعتبر است.'}, status=405)

    consultation = _get_consultation_for_participant(request, pk)
    if consultation is None:
        return JsonResponse({'error': 'دسترسی ندارید.'}, status=403)

    if consultation.status == ConsultationRequest.Status.PAID:
        consultation.status = ConsultationRequest.Status.COMPLETED
        consultation.completed_at = timezone.now()
        consultation.save(update_fields=['status', 'completed_at'])

    return JsonResponse({'status': consultation.status})


@login_required
def my_consultations_view(request):
    as_client = ConsultationRequest.objects.filter(user=request.user).select_related('lawyer__user')

    as_lawyer = ConsultationRequest.objects.none()
    try:
        lawyer = LawyerProfile.objects.get(user=request.user)
        as_lawyer = ConsultationRequest.objects.filter(lawyer=lawyer).select_related('user')
    except LawyerProfile.DoesNotExist:
        pass

    return render(request, 'home/my_consultations.html', {
        'as_client': as_client,
        'as_lawyer': as_lawyer,
        'meta_title': 'مشاوره‌های من | وکیل جو',
        'robots': 'noindex, nofollow',
    })


# =========================================================
# بخش مقالات حقوقی
# =========================================================

class ArticleListView(ListView):
    model = Article
    template_name = 'home/article_list.html'
    context_object_name = 'articles'
    paginate_by = 12

    def get_queryset(self):
        qs = Article.objects.filter(is_published=True).select_related('specialty', 'author__user')

        speciality_slug = self.request.GET.get('speciality', '').strip()
        if speciality_slug:
            qs = qs.filter(specialty__slug=speciality_slug)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['specialties'] = Specialty.objects.filter(is_active=True)
        ctx['selected_speciality'] = self.request.GET.get('speciality', '')
        ctx['meta_title'] = 'مقالات و راهنمای حقوقی | وکیل جو'
        ctx['meta_description'] = 'مقالات آموزشی و راهنمای حقوقی در زمینه‌ی طلاق، مهریه، ملکی، کیفری و سایر تخصص‌ها.'
        ctx['canonical_url'] = self.request.build_absolute_uri(self.request.path)
        return ctx


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'home/article_detail.html'
    context_object_name = 'article'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Article.objects.filter(is_published=True).select_related('specialty', 'author__user')

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        Article.objects.filter(pk=self.object.pk).update(view_count=F('view_count') + 1)
        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        article = self.object

        ctx['meta_title'] = article.meta_title or f'{article.title} | وکیل جو'
        ctx['meta_description'] = article.meta_description or article.excerpt or article.title
        ctx['canonical_url'] = self.request.build_absolute_uri(article.get_absolute_url())
        ctx['og_image'] = self.request.build_absolute_uri(
            article.featured_image.url) if article.featured_image else self.request.build_absolute_uri(
            '/static/img/back.jpg')

        related = Article.objects.filter(is_published=True, specialty=article.specialty).exclude(
            id=article.id) if article.specialty else Article.objects.none()
        ctx['related_articles'] = related.select_related('specialty')[:4]

        if article.specialty:
            ctx['specialty_lawyers_url'] = reverse('home:lawyer_list', kwargs={'speciality': article.specialty.slug})

        author_name = article.author.user.get_full_name() if article.author else 'تیم تحریریه‌ی وکیل جو'

        article_schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": article.title,
            "description": ctx['meta_description'],
            "image": ctx['og_image'],
            "datePublished": article.published_at.isoformat() if article.published_at else "",
            "dateModified": article.updated_at.isoformat(),
            "author": {
                "@type": "Person" if article.author else "Organization",
                "name": author_name,
            },
            "publisher": {
                "@type": "Organization",
                "name": "وکیل جو",
                "logo": {
                    "@type": "ImageObject",
                    "url": self.request.build_absolute_uri('/static/img/back.jpg')
                }
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": ctx['canonical_url']
            }
        }
        ctx['article_schema'] = json.dumps(article_schema, ensure_ascii=False)

        breadcrumb_items = [
            {"@type": "ListItem", "position": 1, "name": "خانه", "item": self.request.build_absolute_uri('/')},
            {"@type": "ListItem", "position": 2, "name": "مقالات",
             "item": self.request.build_absolute_uri(reverse('home:article_list'))},
            {"@type": "ListItem", "position": 3, "name": article.title, "item": ctx['canonical_url']},
        ]
        ctx['breadcrumb_schema'] = json.dumps({
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": breadcrumb_items
        }, ensure_ascii=False)

        return ctx
