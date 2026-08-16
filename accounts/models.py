from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.urls import reverse
from django.conf import settings

class User(AbstractUser) :
    phone = models.CharField(max_length = 20, blank = True)
    is_lawyer = models.BooleanField(default = False)
    slug = models.SlugField(unique = True, blank = True, null = True, max_length = 200)

    # فیلدهای متای شخصی برای GEO
    geo_title = models.CharField(max_length = 70, blank = True, help_text = "عنوان برای هوش مصنوعی")
    geo_description = models.TextField(blank = True, help_text = "توضیحات برای خزنده‌های هوش مصنوعی")

    def save(self, *args, **kwargs) :
        if not self.slug and self.is_lawyer :
            base = slugify(self.get_full_name() or self.username)
            slug = base
            counter = 1
            while User.objects.filter(slug = slug).exists() :
                slug = f"{base}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self) :
        if self.is_lawyer and self.slug :
            return reverse('home:lawyer_detail', args = [self.slug])
        return reverse('accounts:profile', args = [self.username])

    class Meta :
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"




class LawyerVerification(models.Model):

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'

    STATUS_CHOICES = (
        (STATUS_PENDING, 'در انتظار بررسی'),
        (STATUS_APPROVED, 'تأیید شده'),
        (STATUS_REJECTED, 'رد شده'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='lawyer_verifications',
        verbose_name='کاربر'
    )

    full_name = models.CharField(
        max_length=200,
        verbose_name='نام و نام خانوادگی'
    )

    national_id = models.CharField(
        max_length=20,
        verbose_name='کد ملی'
    )

    bar_association = models.CharField(
        max_length=200,
        verbose_name='کانون وکلا'
    )

    license_number = models.CharField(
        max_length=100,
        verbose_name='شماره پروانه وکالت'
    )

    document = models.FileField(
        upload_to='lawyer_verification/',
        verbose_name='مدرک وکالت'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name='وضعیت'
    )

    admin_note = models.TextField(
        blank=True,
        verbose_name='یادداشت مدیر'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='تاریخ درخواست'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='آخرین تغییر'
    )

    class Meta:
        verbose_name = 'درخواست احراز وکالت'
        verbose_name_plural = 'درخواست‌های احراز وکالت'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.full_name} - {self.get_status_display()}'