from celery import shared_task


@shared_task()
def create_fec_file(x, y):
    return x + y
