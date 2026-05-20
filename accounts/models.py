from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.text import slugify
from django.urls import reverse


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