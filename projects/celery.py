from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrportal.settings')
app = Celery('hrportal')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()