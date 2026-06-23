from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import LawyerSubscription


@shared_task
def check_expiring_subscriptions():

    target_date = timezone.now() + timedelta(days=3)

    subscriptions = LawyerSubscription.objects.filter(
        is_paid=True,
        end_date__date=target_date.date()
    )

    for sub in subscriptions:
        print(
            f"{sub.lawyer.user.email} expires soon"
        )