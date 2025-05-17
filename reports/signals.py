from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Dashboard, Widget
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Widget)
def clear_dashboard_cache(sender, instance, **kwargs):
    """
    Clear dashboard cache when widgets are updated
    """
    cache.delete(f"dashboard_{instance.dashboard.id}_data")
    logger.debug(f"Cleared cache for dashboard {instance.dashboard.id}")

@receiver(post_save, sender=Dashboard)
def initialize_default_widgets(sender, instance, created, **kwargs):
    """
    Add default widgets when a new dashboard is created
    """
    if created and instance.widgets.count() == 0:
        from .default_widgets import create_default_widgets
        create_default_widgets(instance)
        logger.info(f"Created default widgets for new dashboard {instance.id}")