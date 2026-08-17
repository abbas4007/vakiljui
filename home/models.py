from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from datetime import timedelta
from accounts.models import User
from ckeditor.fields import RichTextField
from ckeditor_uploader.fields import RichTextUploadingField


class LawyerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'is_lawyer': True})
    speciality = models.CharField(max_length=200, verbose_name="تخصص اصلی")
    sub_speciality = models.CharField(max_length=200, blank=True, verbose_name="زیرتخصص")
    city = models.CharField(max_length=100, verbose_name="شهر")
    address = models.TextField(blank=True)
    description = RichTextUploadingField(
        verbose_name="توضیحات حرفه‌ای",
        config_name='default'
    )
    ai_summary = models.TextField(
        blank=True,
        null=True,
        verbose_name="خلاصه هوش مصنوعی",
        help_text="خلاصه‌ای که در نتایج جستجو نمایش داده می‌شود (۱۵۰ کاراکتر)"
    )
    profile_image = models.ImageField(upload_to='lawyers/', blank=True)
    phone_display = models.CharField(max_length=20, blank=True)
    bar_number = models.CharField(max_length=50, blank=True, verbose_name="شماره پروانه وکالت")

    years_of_experience = models.PositiveSmallIntegerField(default=0, verbose_name="سال‌های تجربه")

    success_rate = models.PositiveSmallIntegerField(default=0, help_text="درصد موفقیت (۰ تا ۱۰۰)")
    rating_count = models.PositiveIntegerField(default=0, verbose_name="تعداد امتیازدهندگان")
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    meta_title = models.CharField(max_length=70, blank=True,null=True)
    meta_description = models.CharField(max_length=160, blank=True,null = True)
    faq_data = models.JSONField(default=dict, blank=True, help_text="مثلاً {'سوال':'پاسخ'}")

    slug = models.SlugField(unique=True, allow_unicode=True, max_length=200)

    @property
    def years_experience(self):
        return self.years_of_experience

    def save(self, *args, **kwargs):
        if not self.slug:
            base = f"{self.user.get_full_name()}-{self.speciality}-{self.city}"
            self.slug = slugify(base, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('home:lawyer_detail', args=[self.slug])

    def __str__(self):
        return f"{self.user.get_full_name()} | {self.speciality} | {self.city}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['city', 'speciality']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]
        verbose_name = "پروفایل وکیل"
        verbose_name_plural = "پروفایل‌های وکلا"


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=50, verbose_name="نام طرح")
    price = models.PositiveIntegerField(verbose_name="قیمت (تومان)")
    duration_days = models.PositiveIntegerField(default=30, verbose_name="مدت (روز)")
    priority = models.PositiveSmallIntegerField(default=0, verbose_name="اولویت نمایش")
    features = models.JSONField(default=dict, blank=True, verbose_name="امکانات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")

    def __str__(self):
        return f"{self.name} - {self.price:,} تومان"

    class Meta:
        verbose_name = "طرح اشتراک"
        verbose_name_plural = "طرح‌های اشتراک"
        ordering = ['-priority', 'price']


class LawyerSubscription(models.Model):
    lawyer = models.ForeignKey(LawyerProfile, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    is_paid = models.BooleanField(default=False)
    payment_id = models.CharField(max_length=100, blank=True, verbose_name="شناسه پرداخت")

    def __str__(self):
        return f"{self.lawyer.user.get_full_name()} - {self.plan.name}"

    @property
    def is_active(self):
        from django.utils import timezone
        return self.is_paid and self.end_date > timezone.now()

    class Meta:
        verbose_name = "اشتراک وکیل"
        verbose_name_plural = "اشتراک‌های وکلا"
        ordering = ['-start_date']


class LandingPageContent(models.Model):
    speciality = models.CharField(max_length=100, verbose_name="تخصص")
    city = models.CharField(max_length=100, verbose_name="شهر")

    meta_title = models.CharField(max_length=70, blank=True, null = True,verbose_name="عنوان متا")
    meta_description = models.CharField(max_length=160, blank=True, null = True,verbose_name="توضیحات متا")
    h1_title = models.CharField(max_length=100, blank=True)
    intro_text = RichTextUploadingField(blank=True, verbose_name="متن معرفی")
    main_content = RichTextUploadingField(blank=True, verbose_name="محتوای اصلی", config_name='default')
    tips_content = RichTextField(blank=True, verbose_name="راهنمای انتخاب", config_name='simple')
    faq_content = models.JSONField(default=list, blank=True, verbose_name="سوالات متداول")

    avg_success_rate = models.PositiveSmallIntegerField(default=0, verbose_name="میانگین نرخ موفقیت")
    total_lawyers = models.PositiveSmallIntegerField(default=0, verbose_name="تعداد وکلا")

    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['speciality', 'city']
        verbose_name = "محتوای صفحه لندینگ"
        verbose_name_plural = "محتوای صفحات لندینگ"

    def __str__(self):
        return f"بهترین وکیل {self.speciality} در {self.city}"


class City(models.Model):
    name = models.CharField(max_length = 100, unique = True, verbose_name = "نام شهر")
    slug = models.SlugField(max_length = 100, unique = True, allow_unicode = True, blank = True)
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب نمایش")
    lawyer_count = models.PositiveSmallIntegerField(default=0, verbose_name="تعداد وکلا (آمار دستی)")

    def save(self, *args, **kwargs) :
        if not self.slug :
            from django.utils.text import slugify
            self.slug = slugify(self.name, allow_unicode = True)
        super().save(*args, **kwargs)

    def get_absolute_url(self) :
        from django.urls import reverse
        return reverse('home:seo_landing', kwargs = {'speciality' : 'همه', 'city' : self.slug})

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "شهر"
        verbose_name_plural = "شهرها"


class Specialty(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, allow_unicode=True, blank=True)
    icon = models.CharField(max_length=50, default='bi-briefcase', verbose_name="آیکون")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب نمایش")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('home:lawyer_list', kwargs={'speciality': self.slug})

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order', 'name']
        verbose_name = "تخصص"
        verbose_name_plural = "تخصص‌ها"


# =========================================================
# بخش مقالات حقوقی (برای سئوی محتوای اطلاعاتی)
# =========================================================

class Article(models.Model):
    title = models.CharField(max_length=200, verbose_name="عنوان")
    slug = models.SlugField(max_length=220, unique=True, allow_unicode=True, blank=True)

    specialty = models.ForeignKey(
        Specialty, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='articles', verbose_name="تخصص مرتبط"
    )
    # نویسنده اختیاریه؛ اگه به یه وکیل واقعی وصل بشه، اعتبار محتوا برای سئو
    # (E-E-A-T گوگل) و اعتماد کاربر بیشتر میشه
    author = models.ForeignKey(
        LawyerProfile, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='articles', verbose_name="نویسنده (وکیل)"
    )

    excerpt = models.CharField(
        max_length=300, blank=True, verbose_name="خلاصه‌ی کوتاه",
        help_text="تو لیست مقالات و به‌عنوان پیش‌فرض meta description استفاده میشه"
    )
    content = RichTextUploadingField(verbose_name="متن مقاله", config_name='default')
    featured_image = models.ImageField(upload_to='articles/', blank=True, verbose_name="تصویر شاخص")

    meta_title = models.CharField(max_length=70, blank=True, null=True)
    meta_description = models.CharField(max_length=160, blank=True, null=True)

    is_published = models.BooleanField(default=False, verbose_name="منتشر شده")
    published_at = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ انتشار")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    view_count = models.PositiveIntegerField(default=0, verbose_name="تعداد بازدید")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        if self.is_published and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('home:article_detail', args=[self.slug])

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_published']),
        ]
        verbose_name = "مقاله"
        verbose_name_plural = "مقالات"

class ConsultationSetting(models.Model):
    """تنظیمات مشاوره‌ی هر وکیل - قیمت و در دسترس بودن رو خود وکیل تعیین می‌کنه"""
    lawyer = models.OneToOneField(
        LawyerProfile, on_delete=models.CASCADE, related_name='consultation_setting'
    )
    is_available = models.BooleanField(default=False, verbose_name="آماده‌ی پذیرش مشاوره")

    chat_enabled = models.BooleanField(default=True, verbose_name="مشاوره‌ی متنی فعال")
    chat_price = models.PositiveIntegerField(default=0, verbose_name="قیمت مشاوره‌ی متنی (تومان)")

    voice_enabled = models.BooleanField(default=False, verbose_name="مشاوره‌ی تلفنی فعال")
    voice_price = models.PositiveIntegerField(default=0, verbose_name="قیمت مشاوره‌ی تلفنی (تومان)")

    session_minutes = models.PositiveSmallIntegerField(
        default=30, verbose_name="مدت هر جلسه (دقیقه)"
    )

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"تنظیمات مشاوره‌ی {self.lawyer.user.get_full_name()}"

    class Meta:
        verbose_name = "تنظیمات مشاوره‌ی وکیل"
        verbose_name_plural = "تنظیمات مشاوره‌ی وکلا"


class ConsultationRequest(models.Model):
    """یک جلسه‌ی مشاوره‌ی رزروشده/خریداری‌شده توسط کاربر"""

    class Format(models.TextChoices):
        CHAT = 'chat', 'متنی'
        VOICE = 'voice', 'تلفنی'

    class Status(models.TextChoices):
        PENDING_PAYMENT = 'pending_payment', 'در انتظار پرداخت'
        PAID = 'paid', 'پرداخت‌شده / در حال انجام'
        COMPLETED = 'completed', 'پایان‌یافته'
        CANCELLED = 'cancelled', 'لغوشده'

    user = models.ForeignKey(
        'accounts.User', on_delete=models.CASCADE, related_name='consultation_requests',
        verbose_name="کاربر متقاضی"
    )
    lawyer = models.ForeignKey(
        LawyerProfile, on_delete=models.CASCADE, related_name='consultation_requests',
        verbose_name="وکیل"
    )
    format = models.CharField(max_length=10, choices=Format.choices, default=Format.CHAT)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING_PAYMENT)

    # قیمت و مدت رو لحظه‌ی رزرو snapshot می‌کنیم؛ اگه وکیل بعداً قیمتش رو
    # عوض کرد، رو جلسات قبلی اثر نذاره
    price = models.PositiveIntegerField(verbose_name="قیمت (تومان)")
    commission_percent = models.PositiveSmallIntegerField(verbose_name="درصد کمیسیون سایت")
    session_minutes = models.PositiveSmallIntegerField()

    payment_authority = models.CharField(max_length=100, blank=True, verbose_name="شناسه‌ی پرداخت زرین‌پال")
    payment_ref_id = models.CharField(max_length=100, blank=True, verbose_name="کد رهگیری پرداخت")

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # وقتی این جلسه تسویه شد (به LawyerPayout وصل میشه)
    payout = models.ForeignKey(
        'LawyerPayout', on_delete=models.SET_NULL, null=True, blank=True, related_name='consultations'
    )

    @property
    def commission_amount(self):
        return (self.price * self.commission_percent) // 100

    @property
    def lawyer_net_amount(self):
        return self.price - self.commission_amount

    @property
    def session_ends_at(self):
        if not self.paid_at:
            return None
        return self.paid_at + timedelta(minutes=self.session_minutes)

    @property
    def is_session_expired(self):
        ends_at = self.session_ends_at
        return bool(ends_at and timezone.now() > ends_at)

    def __str__(self):
        return f"مشاوره‌ی {self.user} با {self.lawyer.user.get_full_name()} ({self.get_status_display()})"

    class Meta:
        ordering = ['-created_at']
        verbose_name = "درخواست مشاوره"
        verbose_name_plural = "درخواست‌های مشاوره"


class ConsultationMessage(models.Model):
    """پیام‌های چت داخل یک جلسه‌ی مشاوره‌ی متنی"""
    consultation = models.ForeignKey(
        ConsultationRequest, on_delete=models.CASCADE, related_name='messages'
    )
    sender = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = "پیام مشاوره"
        verbose_name_plural = "پیام‌های مشاوره"


class LawyerPayout(models.Model):
    """تسویه‌ی دوره‌ای (هفتگی/ماهانه) - همه‌ی مشاوره‌های تکمیل‌شده‌ی یک بازه با هم جمع می‌شن"""

    class Status(models.TextChoices):
        PENDING = 'pending', 'در انتظار پرداخت'
        PAID = 'paid', 'پرداخت‌شده'

    lawyer = models.ForeignKey(LawyerProfile, on_delete=models.CASCADE, related_name='payouts')
    period_start = models.DateTimeField()
    period_end = models.DateTimeField()

    gross_amount = models.PositiveIntegerField(default=0, verbose_name="جمع مبلغ مشاوره‌ها")
    commission_amount = models.PositiveIntegerField(default=0, verbose_name="کمیسیون سایت")
    net_amount = models.PositiveIntegerField(default=0, verbose_name="مبلغ قابل‌پرداخت به وکیل")

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    paid_at = models.DateTimeField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True, verbose_name="یادداشت (مثلاً کد پیگیری واریز)")

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"تسویه‌ی {self.lawyer.user.get_full_name()} — {self.net_amount:,} تومان ({self.get_status_display()})"

    class Meta:
        ordering = ['-period_end']
        verbose_name = "تسویه‌ی وکیل"
        verbose_name_plural = "تسویه‌های وکلا"