import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrportal.settings')

app = Celery('hrportal')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()