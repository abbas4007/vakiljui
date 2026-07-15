from django.contrib import messages
from django.views.generic import TemplateView, View
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
import requests
from django.conf import settings
from .models import SubscriptionPlan, LawyerSubscription
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
import json
from django.views.generic import ListView
from .models import LawyerProfile, City, Specialty
import json
from django.views.generic import DetailView
from django.db.models import Q
from .models import LawyerProfile, LawyerProfile as Lawyer
from django.utils import timezone


class HomeView(TemplateView) :
    template_name = 'home/index.html'

    def get_context_data(self, **kwargs) :
        ctx = super().get_context_data(**kwargs)

        # کش کردن شهرها و تخصص‌ها
        cities = cache.get('active_cities')
        if not cities :
            cities = list(City.objects.filter(is_active = True))
            cache.set('active_cities', cities, 3600)

        specialties = cache.get('active_specialties')
        if not specialties :
            specialties = list(Specialty.objects.filter(is_active = True))
            cache.set('active_specialties', specialties, 3600)

        for city in cities :
            real_count = LawyerProfile.objects.filter(is_active = True, city = city.name).count()
            city.real_lawyer_count = real_count if real_count > 0 else city.lawyer_count

        ctx['cities'] = cities
        ctx['specialties'] = specialties

        # ============ وکلای طلایی ============
        top_lawyers = cache.get('top_lawyers')
        if not top_lawyers :
            # پیدا کردن طرح طلایی
            try :
                gold_plan = SubscriptionPlan.objects.get(
                    name__icontains = 'طلا',  # یا name='gold' یا هر چیزی که در دیتابیس دارید
                    is_active = True
                )
            except SubscriptionPlan.DoesNotExist :
                # اگر طرح طلایی وجود نداشت، می‌توانید از priority استفاده کنید
                gold_plan = SubscriptionPlan.objects.filter(
                    is_active = True
                ).order_by('-priority').first()

            if gold_plan :
                # وکلایی که اشتراک طلایی فعال دارند
                top_lawyers = LawyerProfile.objects.filter(
                    is_active = True,
                    subscriptions__plan = gold_plan,
                    subscriptions__is_paid = True,
                    subscriptions__end_date__gt = timezone.now()  # اشتراک فعال
                ).select_related('user').distinct().order_by('-subscriptions__start_date')[:8]

                # اگر وکیل طلایی پیدا نشد، وکلای با بالاترین اولویت را بیار
                if not top_lawyers :
                    top_lawyers = LawyerProfile.objects.filter(
                        is_active = True,
                        subscriptions__is_paid = True,
                        subscriptions__end_date__gt = timezone.now()
                    ).select_related('user').distinct().order_by(
                        '-subscriptions__plan__priority',
                        '-subscriptions__start_date'
                    )[:8]
            else :
                # اگر هیچ طرح اشتراکی وجود نداشت، وکلای با موفقیت بالا
                top_lawyers = LawyerProfile.objects.filter(
                    is_active = True
                ).select_related('user').order_by('-success_rate')[:8]

            cache.set('top_lawyers', top_lawyers, 3600)

        ctx['top_lawyers'] = top_lawyers

        # متا تگ‌ها و Schema
        ctx['meta_title'] = getattr(settings, 'DEFAULT_META_TITLE', 'وکیل جو | سامانه تخصصی وکلای ایران')
        ctx['meta_description'] = getattr(settings, 'DEFAULT_META_DESCRIPTION', 'بهترین وکلای ایران را پیدا کنید')
        ctx['canonical_url'] = self.request.build_absolute_uri('/')
        ctx['og_image'] = self.request.build_absolute_uri('/static/img/back.jfif')

        ctx['site_schema'] = json.dumps({
            "@context" : "https://schema.org",
            "@type" : "WebSite",
            "name" : "وکیل جو",
            "url" : self.request.build_absolute_uri('/'),
            "description" : ctx['meta_description'],
            "potentialAction" : {
                "@type" : "SearchAction",
                "target" : {
                    "@type" : "EntryPoint",
                    "urlTemplate" : self.request.build_absolute_uri('/') + "جستجو?q={search_term_string}"
                },
                "query-input" : "required name=search_term_string"
            }
        }, ensure_ascii = False)

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

            # لینک‌های راهنما
            ctx['related_guides'] = [
                {'title' : f'هزینه وکیل {speciality} در {city}', 'url' : f'/هزینه-وکیل-{speciality}-در-{city}/'},
                {'title' : f'مدارک لازم برای {speciality}', 'url' : f'/مدارک-لازم-{speciality}/'},
                {'title' : f'مراحل {speciality} در {city}', 'url' : f'/مراحل-{speciality}-در-{city}/'},
                {'title' : f'بهترین وکیل {speciality} در {city}', 'url' : f'/بهترین-وکیل-{speciality}-{city}/'},
                {'title' : f'سوالات متداول {speciality}', 'url' : f'/سوالات-متداول-{speciality}/'},
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

            # متا تگ‌ها
            ctx['meta_title'] = f'بهترین وکیل {speciality} در {city} | وکیل جو'
            ctx[
                'meta_description'] = f'لیست بهترین وکلای {speciality} در {city} به همراه رزومه، نرخ موفقیت و نظرات کاربران'

        else :
            # مقادیر پیش‌فرض
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

        # canonical_url
        ctx['canonical_url'] = self.request.build_absolute_uri(self.request.path)
        ctx['article_schema'] = {
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
            "articleBody" : ctx.get('main_content', '')[:500]  # خلاصه 500 کاراکتری
        }

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


def lawyer_register(request) :
    if request.method == 'POST' :
        from accounts.models import User

        username = request.POST.get('username') or request.POST.get('phone')
        password = request.POST.get('password')

        if not username or not password :
            messages.error(request, 'نام کاربری و رمز عبور الزامی است')
            return render(request, 'home/lawyer_register.html')

        if User.objects.filter(username = username).exists() :
            messages.error(request, 'این نام کاربری قبلاً ثبت شده است')
            return render(request, 'home/lawyer_register.html')

        full_name = request.POST.get('full_name', '')
        name_parts = full_name.split()
        first_name = name_parts[0] if name_parts else ''
        last_name = ' '.join(name_parts[1 :]) if len(name_parts) > 1 else ''

        user = User.objects.create_user(
            username = username,
            password = password,
            first_name = first_name,
            last_name = last_name,
            email = request.POST.get('email', ''),
            phone = request.POST.get('phone', ''),
            is_lawyer = True
        )

        lawyer_profile = LawyerProfile.objects.create(
            user = user,
            speciality = request.POST.get('speciality', ''),
            city = request.POST.get('city', ''),
            description = request.POST.get('description', ''),
            ai_summary = request.POST.get('ai_summary', ''),
            years_of_experience = int(request.POST.get('years_of_experience', 0) or 0),
            phone_display = request.POST.get('phone_display', ''),
            is_active = True
        )

        if request.FILES.get('profile_image') :
            lawyer_profile.profile_image = request.FILES['profile_image']
            lawyer_profile.save()

        from django.contrib.auth import login
        login(request, user)

        messages.success(request, 'ثبت‌نام با موفقیت انجام شد. پروفایل شما ساخته شد.')
        return redirect('home:index')

    return render(request, 'home/lawyer_register.html', {
        'meta_title' : 'ثبت‌نام وکیل | وکیل جو',
        'meta_description' : 'در سامانه وکیل جو ثبت‌نام کنید و در گوگل دیده شوید',
        'canonical_url' : request.build_absolute_uri(request.path),
    })


class LandingPage(View) :

    def get(self, request) :
        return render(request, 'home/landing.html')
