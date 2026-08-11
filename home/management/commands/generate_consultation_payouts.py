"""
تولید تسویه‌ی دوره‌ای (LawyerPayout) برای هر وکیل، از روی مشاوره‌های
تکمیل‌شده‌ای که هنوز به هیچ تسویه‌ای وصل نشدن.

استفاده:
    python manage.py generate_consultation_payouts

پیشنهاد: این دستور رو هفتگی (یا ماهانه) با cron یا celery beat اجرا کن.
خودش هیچ پولی جابه‌جا نمی‌کنه - فقط رکورد "چقدر باید به کی پرداخت بشه" رو
می‌سازه؛ خود واریز (کارت‌به‌کارت/شبا) دستیه و بعدش باید تو ادمین وضعیت
LawyerPayout رو به «پرداخت‌شده» تغییر بدی.
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum, Count
from django.utils import timezone
from home.models import LawyerProfile, ConsultationRequest, LawyerPayout


class Command(BaseCommand):
    help = "تولید تسویه‌ی دوره‌ای برای وکلا از روی مشاوره‌های تکمیل‌شده‌ی تسویه‌نشده"

    def handle(self, *args, **options):
        now = timezone.now()

        lawyer_ids = ConsultationRequest.objects.filter(
            status=ConsultationRequest.Status.COMPLETED,
            payout__isnull=True,
        ).values_list('lawyer_id', flat=True).distinct()

        if not lawyer_ids:
            self.stdout.write("هیچ مشاوره‌ی تسویه‌نشده‌ای پیدا نشد.")
            return

        total_created = 0
        for lawyer_id in lawyer_ids:
            pending_list = list(ConsultationRequest.objects.filter(
                lawyer_id=lawyer_id,
                status=ConsultationRequest.Status.COMPLETED,
                payout__isnull=True,
            ).order_by('created_at'))

            if not pending_list:
                continue

            gross = sum(c.price for c in pending_list)
            commission = sum(c.commission_amount for c in pending_list)
            net = gross - commission
            first_created = pending_list[0].created_at

            payout = LawyerPayout.objects.create(
                lawyer_id=lawyer_id,
                period_start=first_created,
                period_end=now,
                gross_amount=gross,
                commission_amount=commission,
                net_amount=net,
            )
            ConsultationRequest.objects.filter(
                id__in=[c.id for c in pending_list]
            ).update(payout=payout)

            lawyer = LawyerProfile.objects.get(id=lawyer_id)
            self.stdout.write(
                f"تسویه ساخته شد: {lawyer.user.get_full_name()} — "
                f"{net:,} تومان (از {len(pending_list)} مشاوره)"
            )
            total_created += 1

        self.stdout.write(self.style.SUCCESS(f"مجموعاً {total_created} تسویه ساخته شد."))