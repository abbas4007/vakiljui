from django.contrib import admin
from .models import LawyerProfile, LandingPageContent, SubscriptionPlan, LawyerSubscription,City, Specialty

@admin.register(LandingPageContent)
class LandingPageContentAdmin(admin.ModelAdmin):
    list_display = ['speciality', 'city', 'is_active', 'updated_at']
    list_filter = ['speciality', 'city', 'is_active']
    search_fields = ['speciality', 'city']
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('speciality', 'city', 'is_active')
        }),
        ('سئو و متا تگ‌ها', {
            'fields': ('meta_title', 'meta_description', 'h1_title')
        }),
        ('محتوای صفحه', {
            'fields': ('intro_text', 'main_content', 'tips_content')
        }),
        ('سوالات متداول (JSON)', {
            'fields': ('faq_content',),
            'classes': ('wide',),
            'description': 'فرمت JSON: [{"question": "...", "answer": "..."}, ...]'
        }),
        ('آمار', {
            'fields': ('avg_success_rate', 'total_lawyers')
        }),
    )

@admin.register(LawyerProfile)
class LawyerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'speciality', 'city', 'success_rate', 'is_active']
    list_filter = ['speciality', 'city', 'is_active']
    search_fields = ['user__first_name', 'user__last_name', 'speciality']

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'duration_days', 'priority', 'is_active']
    list_editable = ['price', 'priority', 'is_active']

@admin.register(LawyerSubscription)
class LawyerSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['lawyer', 'plan', 'start_date', 'end_date', 'is_paid']
    list_filter = ['plan', 'is_paid']


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active', 'order', 'lawyer_count']
    list_editable = ['is_active', 'order', 'lawyer_count']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'is_active', 'order']
    list_editable = ['is_active', 'order', 'icon']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}