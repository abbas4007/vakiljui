from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, LawyerVerification


@admin.register(User)
class CustomUserAdmin(UserAdmin):

    fieldsets = UserAdmin.fieldsets + (

        (
            'اطلاعات وکالت',
            {
                'fields': (
                    'is_lawyer',
                    'phone',
                    'slug',
                )
            }
        ),

        (
            'اطلاعات GEO',
            {
                'fields': (
                    'geo_title',
                    'geo_description',
                )
            }
        ),

    )

    list_display = (
        'username',
        'email',
        'phone',
        'is_lawyer',
        'is_active',
        'is_staff',
    )

    list_filter = (
        'is_lawyer',
        'is_active',
        'is_staff',
    )

    search_fields = (
        'username',
        'email',
        'phone',
    )


@admin.register(LawyerVerification)
class LawyerVerificationAdmin(admin.ModelAdmin):

    list_display = (
        'full_name',
        'user',
        'bar_association',
        'license_number',
        'status',
        'created_at',
    )

    list_filter = (
        'status',
        'bar_association',
    )

    search_fields = (
        'full_name',
        'user__username',
        'user__email',
        'national_id',
        'license_number',
    )

    readonly_fields = (
        'created_at',
        'updated_at',
    )

    def save_model(self, request, obj, form, change):

        super().save_model(request, obj, form, change)

        user = obj.user

        if obj.status == LawyerVerification.STATUS_APPROVED:

            user.is_lawyer = True

        elif obj.status == LawyerVerification.STATUS_REJECTED:

            user.is_lawyer = False

        user.save(update_fields=['is_lawyer'])