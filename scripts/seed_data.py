#!/usr/bin/env python
# scripts/seed_data.py
import os
import sys
import django
from django.utils.text import slugify

# تنظیم مسیر پروژه
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dadvar.settings')
django.setup()

from accounts.models import User
from home.models import LawyerProfile, City, Specialty, LandingPageContent
from django.contrib.auth.hashers import make_password
import random


def create_cities() :
    """ایجاد شهرهای اصلی ایران"""
    cities_data = [
        {'name' : 'تهران', 'order' : 1},
        {'name' : 'مشهد', 'order' : 2},
        {'name' : 'اصفهان', 'order' : 3},
        {'name' : 'شیراز', 'order' : 4},
        {'name' : 'تبریز', 'order' : 5},
        {'name' : 'کرج', 'order' : 6},
        {'name' : 'قم', 'order' : 7},
        {'name' : 'اهواز', 'order' : 8},
        {'name' : 'کرمانشاه', 'order' : 9},
        {'name' : 'رشت', 'order' : 10},
    ]

    created_count = 0
    for city_data in cities_data :
        city, created = City.objects.get_or_create(
            name = city_data['name'],
            defaults = {
                'order' : city_data['order'],
                'is_active' : True
            }
        )
        if created :
            print(f'✅ شهر {city.name} ایجاد شد')
            created_count += 1
        else :
            print(f'⚠️ شهر {city.name} از قبل وجود داشت')

    print(f'\n📊 جمعاً {created_count} شهر جدید ایجاد شد.\n')
    return created_count


def create_specialties() :
    """ایجاد تخصص‌های حقوقی"""
    specialties_data = [
        {'name' : 'طلاق', 'icon' : 'bi-emoji-frown', 'order' : 1},
        {'name' : 'مهریه', 'icon' : 'bi-cash-stack', 'order' : 2},
        {'name' : 'کیفری', 'icon' : 'bi-shield-lock', 'order' : 3},
        {'name' : 'ملکی', 'icon' : 'bi-building', 'order' : 4},
        {'name' : 'خانواده', 'icon' : 'bi-people', 'order' : 5},
        {'name' : 'ارث و وصیت', 'icon' : 'bi-file-text', 'order' : 6},
        {'name' : 'تجاری', 'icon' : 'bi-shop', 'order' : 7},
        {'name' : 'کار', 'icon' : 'bi-briefcase', 'order' : 8},
        {'name' : 'چک و سفته', 'icon' : 'bi-receipt', 'order' : 9},
        {'name' : 'مهاجرت', 'icon' : 'bi-airplane', 'order' : 10},
    ]

    created_count = 0
    for spec_data in specialties_data :
        specialty, created = Specialty.objects.get_or_create(
            name = spec_data['name'],
            defaults = {
                'icon' : spec_data['icon'],
                'order' : spec_data['order'],
                'is_active' : True
            }
        )
        if created :
            print(f'✅ تخصص {specialty.name} ایجاد شد')
            created_count += 1
        else :
            print(f'⚠️ تخصص {specialty.name} از قبل وجود داشت')

    print(f'\n📊 جمعاً {created_count} تخصص جدید ایجاد شد.\n')
    return created_count


def create_sample_lawyers() :
    """ایجاد وکلا نمونه"""
    # ابتدا مطمئن شو کاربر ادمین وجود داره (بدون slug تا خودکار ساخته بشه)
    admin_user, created = User.objects.get_or_create(
        username = 'admin',
        defaults = {
            'first_name' : 'مدیر',
            'last_name' : 'سایت',
            'email' : 'admin@vakiljo.ir',
            'is_staff' : True,
            'is_superuser' : True,
            'is_active' : True,
            'is_lawyer' : False
        }
    )
    if created :
        admin_user.set_password('admin123')
        admin_user.save()
        print('✅ کاربر ادمین ایجاد شد (نام کاربری: admin، رمز: admin123)')
    else :
        print('⚠️ کاربر ادمین از قبل وجود داشت')

    # داده‌های وکلا
    lawyers_data = [
        {
            'first_name' : 'علی',
            'last_name' : 'احمدی',
            'username' : 'aliahmadi',
            'speciality' : 'طلاق',
            'city' : 'تهران',
            'description' : 'وکیل پایه یک دادگستری با ۱۵ سال سابقه در حوزه طلاق و خانواده. فارغ‌التحصیل دانشگاه شهید بهشتی تهران.',
            'ai_summary' : 'وکیل متخصص طلاق و مهریه در تهران با نرخ موفقیت ۹۸٪ و ۱۵ سال سابقه',
            'years_exp' : 15,
            'success_rate' : 98,
            'phone' : '۰۹۱۲۱۲۳۴۵۶۷',
            'bar_number' : '۱۲۳۴۵'
        },
        {
            'first_name' : 'سارا',
            'last_name' : 'کریمی',
            'username' : 'sarakarimi',
            'speciality' : 'مهریه',
            'city' : 'تهران',
            'description' : 'وکیل دعاوی خانواده و مهریه با بیش از ۱۰ سال تجربه موفق. دارای پروانه وکالت از کانون وکلای مرکز.',
            'ai_summary' : 'وکیل متخصص مهریه و دعاوی خانواده در تهران با نرخ موفقیت ۹۵٪',
            'years_exp' : 10,
            'success_rate' : 95,
            'phone' : '۰۹۱۲۲۳۳۴۴۵۵',
            'bar_number' : '۲۳۴۵۶'
        },
        {
            'first_name' : 'محمد',
            'last_name' : 'رضایی',
            'username' : 'mohamadrezaei',
            'speciality' : 'کیفری',
            'city' : 'مشهد',
            'description' : 'وکیل کیفری و حقوق جزا با ۱۲ سال سابقه. دارای مدرک دکترای حقوق جزا از دانشگاه فردوسی مشهد.',
            'ai_summary' : 'وکیل متخصص دعاوی کیفری در مشهد با نرخ موفقیت ۹۲٪',
            'years_exp' : 12,
            'success_rate' : 92,
            'phone' : '۰۹۱۵۱۲۳۴۵۶۷',
            'bar_number' : '۳۴۵۶۷'
        },
        {
            'first_name' : 'فاطمه',
            'last_name' : 'حسینی',
            'username' : 'fatemehossseini',
            'speciality' : 'ملکی',
            'city' : 'اصفهان',
            'description' : 'وکیل دعاوی ملکی و ثبت اسناد با ۸ سال سابقه. متخصص در دعاوی خلع ید و تنظیم قراردادها.',
            'ai_summary' : 'وکیل متخصص دعاوی ملکی و ثبت در اصفهان با نرخ موفقیت ۹۰٪',
            'years_exp' : 8,
            'success_rate' : 90,
            'phone' : '۰۹۱۳۱۲۳۴۵۶۷',
            'bar_number' : '۴۵۶۷۸'
        },
        {
            'first_name' : 'رضا',
            'last_name' : 'نوری',
            'username' : 'rezanoori',
            'speciality' : 'طلاق',
            'city' : 'شیراز',
            'description' : 'وکیل پایه یک با تمرکز بر طلاق توافقی و دعاوی خانواده. ۱۳ سال سابقه کاری موفق.',
            'ai_summary' : 'وکیل تخصصی طلاق و خانواده در شیراز با نرخ موفقیت ۹۳٪',
            'years_exp' : 13,
            'success_rate' : 93,
            'phone' : '۰۹۱۷۱۲۳۴۵۶۷',
            'bar_number' : '۵۶۷۸۹'
        },
        {
            'first_name' : 'زهرا',
            'last_name' : 'موسوی',
            'username' : 'zahramoosavi',
            'speciality' : 'مهریه',
            'city' : 'تبریز',
            'description' : 'وکیل دعاوی مهریه و نفقه با ۹ سال سابقه. مشاور حقوقی بانوان و خانواده.',
            'ai_summary' : 'وکیل تخصصی مهریه و نفقه در تبریز با نرخ موفقیت ۸۹٪',
            'years_exp' : 9,
            'success_rate' : 89,
            'phone' : '۰۹۱۴۱۲۳۴۵۶۷',
            'bar_number' : '۶۷۸۹۰'
        }
    ]

    created_count = 0
    for lawyer_data in lawyers_data :
        # ایجاد کاربر (بدون slug - خودکار ساخته میشه)
        user, created = User.objects.get_or_create(
            username = lawyer_data['username'],
            defaults = {
                'first_name' : lawyer_data['first_name'],
                'last_name' : lawyer_data['last_name'],
                'email' : f"{lawyer_data['username']}@example.com",
                'phone' : lawyer_data['phone'],
                'is_lawyer' : True,
                'is_active' : True,
            }
        )

        if created :
            user.set_password('lawyer123')
            user.save()
            print(f'✅ کاربر {user.get_full_name()} ایجاد شد')

            # پیدا کردن شهر و تخصص
            city = City.objects.filter(name = lawyer_data['city']).first()
            specialty = Specialty.objects.filter(name = lawyer_data['speciality']).first()

            if city and specialty :
                # ایجاد پروفایل وکیل
                lawyer = LawyerProfile.objects.create(
                    user = user,
                    speciality = specialty.name,
                    city = city.name,
                    description = lawyer_data['description'],
                    ai_summary = lawyer_data['ai_summary'],
                    years_of_experience = lawyer_data['years_exp'],
                    success_rate = lawyer_data['success_rate'],
                    phone_display = lawyer_data['phone'],
                    bar_number = lawyer_data['bar_number'],
                    is_active = True
                )
                print(f'   👨‍⚖️ وکیل {specialty.name} - {city.name} ایجاد شد')
                created_count += 1
            else :
                print(f'   ⚠️ شهر یا تخصص {lawyer_data["city"]}/{lawyer_data["speciality"]} یافت نشد')
        else :
            print(f'⚠️ کاربر {lawyer_data["username"]} از قبل وجود داشت')

    print(f'\n📊 جمعاً {created_count} وکیل جدید ایجاد شد.\n')
    return created_count


def create_landing_pages() :
    """ایجاد صفحات لندینگ پیش‌فرض"""
    cities = City.objects.filter(is_active = True)
    specialties = Specialty.objects.filter(is_active = True)

    created_count = 0
    for city in cities :
        for specialty in specialties :
            content, created = LandingPageContent.objects.get_or_create(
                speciality = specialty.name,
                city = city.name,
                defaults = {
                    'meta_title' : f'بهترین وکیل {specialty.name} در {city.name} | وکیل جو',
                    'meta_description' : f'لیست بهترین وکلای {specialty.name} در {city.name} به همراه رزومه، نرخ موفقیت و نظرات کاربران',
                    'h1_title' : f'بهترین وکیل {specialty.name} در {city.name}',
                    'is_active' : True
                }
            )
            if created :
                created_count += 1

    print(f'📊 {created_count} صفحه لندینگ ایجاد شد.\n')
    return created_count


def run() :
    print('\n' + '=' * 50)
    print('🚀 شروع فرآیند وارد کردن دیتای اولیه')
    print('=' * 50 + '\n')

    create_cities()
    create_specialties()
    create_sample_lawyers()
    create_landing_pages()

    # آمار نهایی
    print('\n' + '=' * 50)
    print('📊 آمار نهایی:')
    print('=' * 50)
    print(f'🏙️ تعداد شهرها: {City.objects.count()}')
    print(f'📚 تعداد تخصص‌ها: {Specialty.objects.count()}')
    print(f'👨‍⚖️ تعداد وکلا: {LawyerProfile.objects.filter(is_active = True).count()}')
    print(f'📄 تعداد صفحات لندینگ: {LandingPageContent.objects.count()}')
    print('\n✅ عملیات با موفقیت انجام شد!')
    print('\n🔑 اطلاعات ورود:')
    print('   ادمین: username: admin, password: admin123')
    print('   وکلا: username: (نام کاربری وکیل), password: lawyer123')
    print('=' * 50)


if __name__ == '__main__' :
    run()