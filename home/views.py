from django.contrib import messages
from django.views.generic import TemplateView, View
from django.http import HttpResponse, JsonResponse
from .ai_matcher import analyze_legal_query, AIMatcherError
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
from .models import (
    LawyerProfile, City, Specialty, LandingPageContent,
    ConsultationSetting, ConsultationRequest, ConsultationMessage, LawyerPayout,
    Article,
)
import json
from django.views.generic import DetailView
from django.db.models import Q, Max, F
from .models import LawyerProfile, LawyerProfile as Lawyer
from django.utils import timezone


from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.decorators import method_decorator


@method_decorator(ensure_csrf_cookie, name='dispatch')
class HomeView(TemplateView):
    template_name = 'home/index.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        cities = cache.get('active_cities')
        if not cities:
            cities = list(City.objects.filter(is_active=True))
            cache.set('active_cities', cities, 3600)

        specialties = cache.get('active_specialties')
        if not specialties:
            specialties = list(Specialty.objects.filter(is_active=True))
            cache.set('active_specialties', specialties, 3600)

        for city in cities:
            real_count = LawyerProfile.objects.filter(is_active=True, city=city.name).count()
            city.real_lawyer_count = real_count if real_count > 0 else city.lawyer_count

        ctx['cities'] = cities
        ctx['specialties'] = specialties

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

        ctx['meta_title'] = getattr(settings, 'DEFAULT_META_TITLE', 'وکیل جو | سامانه تخصصی وکلای ایران')
        ctx['meta_description'] = getattr(settings, 'DEFAULT_META_DESCRIPTION', 'بهترین وکلای ایران را پیدا کنید')
        ctx['canonical_url'] = self.request.build_absolute_uri('/')
        ctx['og_image'] = self.request.build_absolute_uri('/static/img/back.jfif')

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

        query = self.request.GET.get('q', '').strip()
        if query:
            valid_specialty_names = [s.name for s in specialties]
            valid_city_names = [c.name for c in cities]

            try:
                result = analyze_legal_query(query, valid_specialty_names, valid_city_names)
                ctx['initial_ai_query'] = query
                ctx['initial_ai_result'] = result
                ctx['panel_should_open'] = True

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
                ctx['canonical_url'] = self.request.build_absolute_uri('/')

            except AIMatcherError:
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

        if speciality_clean and city_clean :
            ctx['landing_page_url'] = self.request.build_absolute_uri(
                f'/بهترین-وکیل/{speciality_clean.replace(" ", "-")}/{city_clean.replace(" ", "-")}/'
            )

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

        ctx['meta_title'] = f'{full_name} | بهترین وکیل {lawyer.speciality} در {lawyer.city} | وکیل جو'
        ctx['meta_description'] = summary[:160]
        ctx['canonical_url'] = self.request.build_absolute_uri(lawyer.get_absolute_url())
        ctx['og_image'] = self.request.build_absolute_uri(
            lawyer.profile_image.url) if lawyer.profile_image else self.request.build_absolute_uri(
            '/static/img/back.jfif')

        ctx['similar_lawyers'] = LawyerProfile.objects.filter(
            is_active = True,
            speciality = lawyer.speciality,
            city = lawyer.city
        ).exclude(id = lawyer.id).select_related('user')[:4]

        return ctx


class LLMsTextView(View) :
    def get(self, request) :
        content = self._generate_llms_txt(request)
        return HttpResponse(content, content_type = 'text/plain; charset=utf-8')

    def _generate_llms_txt(self, request) :
        lines = ["# وکیل جو"]
        top_lawyers = LawyerProfile.objects.filter(is_active = True).select_related('user')[:20]
        for lawyer in top_lawyers :
            lines.append(f"- {lawyer.user.get_full_name()}")
        return "\n".join(lines)


@login_required
def subscribe_view(request, plan_id) :
    plan = get_object_or_404(SubscriptionPlan, id = plan_id, is_active = True)
    try :
        lawyer = LawyerProfile.objects.get(user = request.user)
    except LawyerProfile.DoesNotExist :
        messages.error(request, 'پروفایل وکیل یافت نشد.')
        return redirect('home:index')

    return render(request, 'home/subscribe.html', {'plan' : plan, 'lawyer' : lawyer})


def payment_verify(request) :
    return render(request, 'home/payment_failed.html', {'message' : 'تست'})


def subscription_plans(request) :
    plans = SubscriptionPlan.objects.filter(is_active = True).order_by('price')
    return render(request, 'home/subscribe.html', {'plans' : plans})


def lawyer_register(request) :
    return render(request, 'home/lawyer_register.html')


class LandingPage(View) :
    def get(self, request) :
        return render(request, 'home/landing.html')


class LawyerSearchView(ListView):
    model = LawyerProfile
    template_name = 'home/search_results.html'
    context_object_name = 'lawyers'
    paginate_by = 12

    def get_queryset(self):
        return LawyerProfile.objects.none()


class SeoLandingView(TemplateView):
    template_name = 'home/seo_landing.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['speciality'] = self.kwargs.get('speciality', '')
        ctx['city'] = self.kwargs.get('city', '')
        return ctx


class AIMatchView(View):
    def post(self, request):
        return JsonResponse({'summary': '', 'specialties': [], 'lawyers': []})


# =========================================================
# سیستم مشاوره‌ی آنلاین پولی
# =========================================================

def consultation_lawyer_list_view(request):
    """
    صفحه‌ی عمومی (بدون نیاز به لاگین) که همه‌ی وکلای فعالی که مشاوره‌ی
    آنلاین روشن کردن رو نشون می‌ده. این تنها ورودی عمومیه که کاربر عادی
    (بدون این‌که از قبل بدونه کدوم وکیل) می‌تونه به مشاوره برسه.
    """
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
    """پنل تنظیمات مشاوره برای خود وکیل (روشن/خاموش کردن، تعیین قیمت)"""
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
    """کاربر از صفحه‌ی وکیل رو دکمه‌ی درخواست مشاوره کلیک می‌کنه؛ اینجا رزرو ساخته و به درگاه پرداخت فرستاده میشه"""
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
        # جلوگیری از verify شدن دوباره‌ی یه پرداخت (مثلاً کاربر رفرش کنه)
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
    """فقط کاربر متقاضی یا خود وکیل اجازه‌ی دسترسی به یه جلسه‌ی مشاوره رو دارن"""
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
    """لیست مشاوره‌های خود کاربر (چه به‌عنوان متقاضی، چه به‌عنوان وکیل)"""
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
        # شمارنده‌ی بازدید (ساده؛ برای شمارش دقیق‌تر می‌شه بعداً session-based کرد)
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

        # مقالات مرتبط (همون تخصص)
        related = Article.objects.filter(is_published=True, specialty=article.specialty).exclude(
            id=article.id) if article.specialty else Article.objects.none()
        ctx['related_articles'] = related.select_related('specialty')[:4]

        # لینک به لیست وکلای همون تخصص (برای تبدیل بازدیدکننده به کاربر واقعی)
        if article.specialty:
            ctx['specialty_lawyers_url'] = reverse('home:lawyer_list', kwargs={'speciality': article.specialty.slug})

        author_name = article.author.user.get_full_name() if article.author else 'تیم تحریریه‌ی وکیل جو'

        # ========== Article/BlogPosting Schema ==========
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

        # ========== Breadcrumb Schema ==========
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