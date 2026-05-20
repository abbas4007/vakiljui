from django.db import models
from django.urls import reverse
from django.utils.text import slugify
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
    # فیلد خلاصه هوش مصنوعی (برای SEO)
    ai_summary = models.TextField(
        blank=True,
        null=True,
        verbose_name="خلاصه هوش مصنوعی",
        help_text="خلاصه‌ای که در نتایج جستجو نمایش داده می‌شود (۱۵۰ کاراکتر)"
    )
    profile_image = models.ImageField(upload_to='lawyers/', blank=True)
    phone_display = models.CharField(max_length=20, blank=True)
    bar_number = models.CharField(max_length=50, blank=True, verbose_name="شماره پروانه وکالت")

    # years_of_experience به عنوان فیلد اصلی + پراپرتی برای سازگاری با view
    years_of_experience = models.PositiveSmallIntegerField(default=0, verbose_name="سال‌های تجربه")

    success_rate = models.PositiveSmallIntegerField(default=0, help_text="درصد موفقیت (۰ تا ۱۰۰)")
    rating_count = models.PositiveIntegerField(default=0, verbose_name="تعداد امتیازدهندگان")
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # فیلدهای سئوی اختصاصی
    meta_title = models.CharField(max_length=70, blank=True,null=True)
    meta_description = models.CharField(max_length=160, blank=True,null = True)
    faq_data = models.JSONField(default=dict, blank=True, help_text="مثلاً {'سوال':'پاسخ'}")

    slug = models.SlugField(unique=True, allow_unicode=True, max_length=200)

    # پراپرتی برای سازگاری view قدیمی
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

    def get_structured_data(self, request=None):
        """تولید JSON-LD برای وکیل (نوع Attorney + LegalService)"""
        if request:
            url = request.build_absolute_uri(self.get_absolute_url())
        else:
            url = self.get_absolute_url()

        data = {
            "@context": "https://schema.org",
            "@type": "Attorney",
            "name": self.user.get_full_name(),
            "url": url,
            "description": self.ai_summary or self.description[:150] if self.description else "",
            "specialty": self.speciality,
            "address": {
                "@type": "PostalAddress",
                "addressLocality": self.city,
                "addressCountry": "IR"
            },
            "telephone": self.phone_display if self.phone_display else "",
            "yearsInBusiness": self.years_of_experience,
        }

        # aggregateRating فقط اگه success_rate > 0 و rating_count > 0 باشه
        if self.success_rate > 0 and self.rating_count > 0:
            data["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": str(self.success_rate),
                "bestRating": "100",
                "worstRating": "0",
                "ratingCount": str(self.rating_count),
            }

        # حذف کلیدهای خالی
        return {k: v for k, v in data.items() if v}

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
    """طرح‌های اشتراک (برنز، نقره، طلا)"""
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
    """اشتراک خریداری شده توسط وکیل"""
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
    """محتوای اختصاصی هر صفحه لندینگ"""
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
        # برای لینک به صفحه لندینگ "بهترین وکیل همه در همدان"
        # اگه می‌خوای به صفحه لیست وکلا بره، از این استفاده کن:
        # return reverse('home:lawyer_list_city', kwargs={'speciality': 'همه', 'city': self.slug})

        # اگه می‌خوای به صفحه لندینگ بره:
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
