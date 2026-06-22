from celery import shared_task


@shared_task
def hello():
    print("Celery is working!")
    return "ok"